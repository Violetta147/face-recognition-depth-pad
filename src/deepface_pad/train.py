from __future__ import annotations

import csv
import json
import platform
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import yaml
from torch import nn
from torch.utils.data import DataLoader

from .data import PadDataset, manifest_checksum
from .losses import FocalLoss, depth_loss
from .metrics import aggregate_video_scores, evaluate_scores
from .models import CDCN, CDCNMultiTaskLite, MobileNetBaseline
from .preflight import inspect_training_inputs


def seed_everything(seed: int) -> None:
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    if torch.cuda.is_available(): torch.cuda.manual_seed_all(seed)


def build_model(config: dict) -> nn.Module:
    name = config["model"]["name"]
    if name == "mobilenet_v3_small": return MobileNetBaseline(config["model"].get("pretrained", True))
    if name == "cdcn": return CDCN(config["model"].get("theta", 0.7), config["model"].get("base_channels", 32))
    if name == "cdcn_mt_lite": return CDCNMultiTaskLite(config["model"].get("theta", 0.7), config["model"].get("base_channels", 32))
    raise ValueError(f"unknown model: {name}")


def _loss(config: dict, output: dict[str, torch.Tensor], batch: dict[str, object], stage: str = "joint") -> torch.Tensor:
    label = batch["label"].to(output[next(iter(output))].device)
    total = torch.zeros((), device=label.device)
    if "depth" in output and stage != "head":
        total = total + depth_loss(output["depth"], batch["depth"].to(label.device), config["loss"].get("lambda_abs", 1.0), config["loss"].get("lambda_contrast", 0.5))
    if "logit" in output and stage != "depth":
        if config["loss"].get("classification", "bce") == "focal":
            cls = FocalLoss(config["loss"].get("alpha", 0.25), config["loss"].get("gamma", 2.0))(output["logit"], label)
        else:
            cls = nn.functional.binary_cross_entropy_with_logits(output["logit"], label)
        total = total + config["loss"].get("lambda_cls", 1.0) * cls
    return total


def _set_stage(model: nn.Module, stage: str) -> None:
    for parameter in model.parameters(): parameter.requires_grad = True
    if stage == "head" and hasattr(model, "backbone"):
        for parameter in model.backbone.parameters(): parameter.requires_grad = False
    elif stage == "depth" and hasattr(model, "head"):
        for parameter in model.head.parameters(): parameter.requires_grad = False


@torch.no_grad()
def score_loader(model: nn.Module, loader: DataLoader, device: torch.device) -> pd.DataFrame:
    model.eval(); rows = []
    for batch in loader:
        output = model(batch["image"].to(device))
        score = torch.sigmoid(output["logit"]) if "logit" in output else output["score"]
        rows.extend({"sample_id": s, "video_id": v, "label": int(y), "score": float(z)} for s, v, y, z in zip(batch["sample_id"], batch["video_id"], batch["label"], score.cpu()))
    return pd.DataFrame(rows)


def run(config_path: str | Path) -> Path:
    config_path = Path(config_path); config = yaml.safe_load(config_path.read_text(encoding="utf-8")); seed_everything(config["seed"])
    require_depth, depth_snapshot = inspect_training_inputs(config)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    run_id = f'{config["experiment_id"]}_seed{config["seed"]}_{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")}'
    run_dir = Path(config.get("runs_dir", "runs")) / run_id; run_dir.mkdir(parents=True)
    (run_dir / "config.yaml").write_text(config_path.read_text(encoding="utf-8"), encoding="utf-8")
    (run_dir / "environment.txt").write_text(f"python={sys.version}\nplatform={platform.platform()}\ntorch={torch.__version__}\ndevice={device}\n", encoding="utf-8")
    checksum = manifest_checksum(config["data"]["manifest"])
    (run_dir / "manifest_checksum.json").write_text(json.dumps({"sha256": checksum}, indent=2), encoding="utf-8")
    if depth_snapshot is not None:
        (run_dir / "depth_input_snapshot.json").write_text(
            json.dumps(depth_snapshot, indent=2) + "\n", encoding="utf-8"
        )
    datasets = {
        split: PadDataset(
            config["data"]["manifest"],
            config["data"]["root"],
            split,
            config["data"].get("image_size", 256),
            split == "train",
            require_depth=require_depth,
        )
        for split in ("train", "val")
    }
    loaders = {split: DataLoader(ds, batch_size=config["training"].get("batch_size", 16), shuffle=split == "train", num_workers=config["training"].get("workers", 0)) for split, ds in datasets.items()}
    model = build_model(config).to(device); best = float("inf"); history = []
    stages = config["training"].get("stages", [{"name": "joint", "epochs": config["training"]["epochs"], "lr": config["training"]["lr"]}])
    initial = config["training"].get("init_checkpoint")
    if initial:
        state = torch.load(initial, map_location=device, weights_only=False)
        missing, unexpected = model.load_state_dict(state["model"], strict=False)
        allowed_missing = {"head.layers.0.weight", "head.layers.0.bias", "head.layers.2.weight", "head.layers.2.bias", "head.classifier.weight", "head.classifier.bias"}
        if unexpected or not set(missing).issubset(allowed_missing):
            raise RuntimeError(f"incompatible init checkpoint; missing={missing}, unexpected={unexpected}")
    elif any(stage["name"] == "head" for stage in stages):
        raise ValueError("head-only training requires training.init_checkpoint from E1")
    for stage in stages:
        _set_stage(model, stage["name"]); optimizer = torch.optim.AdamW((p for p in model.parameters() if p.requires_grad), lr=stage["lr"], weight_decay=config["training"].get("weight_decay", 1e-4))
        for epoch in range(stage["epochs"]):
            model.train(); losses = []
            for batch in loaders["train"]:
                optimizer.zero_grad(); output = model(batch["image"].to(device)); loss = _loss(config, output, batch, stage["name"]); loss.backward(); optimizer.step(); losses.append(loss.item())
            model.eval(); val_losses = []
            with torch.no_grad():
                for batch in loaders["val"]: val_losses.append(_loss(config, model(batch["image"].to(device)), batch, stage["name"]).item())
            row = {"stage": stage["name"], "epoch": epoch + 1, "train_loss": float(np.mean(losses)), "val_loss": float(np.mean(val_losses))}; history.append(row)
            if row["val_loss"] < best: best = row["val_loss"]; torch.save({"model": model.state_dict(), "config": config, "val_loss": best}, run_dir / "best.ckpt")
    pd.DataFrame(history).to_csv(run_dir / "train_log.csv", index=False)
    checkpoint = torch.load(run_dir / "best.ckpt", map_location=device, weights_only=False); model.load_state_dict(checkpoint["model"])
    frame_scores = score_loader(model, loaders["val"], device); frame_scores.to_csv(run_dir / "val_frame_scores.csv", index=False)
    video_scores = aggregate_video_scores(frame_scores, config["evaluation"].get("aggregation", "mean")); video_scores.to_csv(run_dir / "val_scores.csv", index=False)
    metrics = evaluate_scores(video_scores.label.to_numpy(), video_scores.score.to_numpy()); payload = metrics.to_dict()
    (run_dir / "threshold.json").write_text(json.dumps({"threshold": metrics.threshold, "source": "validation"}, indent=2), encoding="utf-8")
    (run_dir / "metrics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return run_dir
