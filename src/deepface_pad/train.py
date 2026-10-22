from __future__ import annotations

import csv
import json
import platform
import random
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import yaml
from torch import nn
from torch.utils.data import DataLoader

from .data import PadDataset, manifest_checksum
from .losses import FocalLoss, depth_loss, official_cdcn_depth_loss
from .metrics import aggregate_video_scores, evaluate_scores
from .models import (
    MobileNetBaseline,
    OFFICIAL_CDCN_PROVENANCE,
    OfficialCDCN,
    OfficialCDCNWithDepthHead,
)
from .preflight import inspect_training_inputs


def seed_everything(seed: int) -> None:
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    if torch.cuda.is_available(): torch.cuda.manual_seed_all(seed)


def build_model(config: dict) -> nn.Module:
    name = config["model"]["name"]
    if name == "mobilenet_v3_small": return MobileNetBaseline(config["model"].get("pretrained", True))
    if name == "cdcn_official": return OfficialCDCN(config["model"].get("theta", 0.7))
    if name == "cdcn_official_head": return OfficialCDCNWithDepthHead(config["model"].get("theta", 0.7))
    if name in {"cdcn", "cdcn_lite", "cdcn_mt_lite"}:
        raise ValueError("Legacy CDCN Lite/Pilot was removed; use cdcn_official or cdcn_official_head with an official checkpoint")
    raise ValueError(f"unknown model: {name}")


def load_initial_weights(model: nn.Module, checkpoint_path: str | Path, device: torch.device) -> None:
    # Official E1 keys are explicitly mapped into the E2 backbone namespace.
    state = torch.load(checkpoint_path, map_location=device, weights_only=False)
    weights = state["model"]
    target_keys = set(model.state_dict())
    if hasattr(model, "backbone") and weights and not any(key.startswith("backbone.") for key in weights):
        if all(f"backbone.{key}" in target_keys for key in weights):
            weights = {f"backbone.{key}": value for key, value in weights.items()}
    missing, unexpected = model.load_state_dict(weights, strict=False)
    allowed_missing = {
        "head.layers.0.weight",
        "head.layers.0.bias",
        "head.layers.2.weight",
        "head.layers.2.bias",
        "head.classifier.weight",
        "head.classifier.bias",
    }
    if unexpected or not set(missing).issubset(allowed_missing):
        raise RuntimeError(f"incompatible init checkpoint; missing={missing}, unexpected={unexpected}")


def _loss(config: dict, output: dict[str, torch.Tensor], batch: dict[str, object], stage: str = "joint") -> torch.Tensor:
    label = batch["label"].to(output[next(iter(output))].device)
    total = torch.zeros((), device=label.device)
    if "depth" in output and stage != "head":
        loss_function = (
            official_cdcn_depth_loss
            if config["loss"].get("implementation") == "official_cdcn"
            else depth_loss
        )
        total = total + loss_function(output["depth"], batch["depth"].to(label.device), config["loss"].get("lambda_abs", 1.0), config["loss"].get("lambda_contrast", 0.5))
    if "logit" in output and stage != "depth":
        if config["loss"].get("classification", "bce") == "focal":
            cls = FocalLoss(config["loss"].get("alpha", 0.25), config["loss"].get("gamma", 2.0))(output["logit"], label)
        else:
            cls = nn.functional.binary_cross_entropy_with_logits(output["logit"], label)
        total = total + config["loss"].get("lambda_cls", 1.0) * cls
    return total


def _set_stage(model: nn.Module, stage: str) -> None:
    if stage not in {"depth", "head", "joint"}:
        raise ValueError(f"unknown training stage: {stage}")
    for parameter in model.parameters(): parameter.requires_grad = True
    if stage == "head" and hasattr(model, "backbone"):
        for parameter in model.backbone.parameters(): parameter.requires_grad = False
    elif stage == "depth" and hasattr(model, "head"):
        for parameter in model.head.parameters(): parameter.requires_grad = False


def _selection_loss(metric: str, output: dict[str, torch.Tensor],
                    batch: dict[str, object], stage: str,
                    objective: torch.Tensor) -> torch.Tensor:
    # Depth-only warm-up has no trained classifier. In head/joint stages a
    # common BCE criterion permits the same selection rule for BCE and Focal.
    if metric == "val_loss" or stage == "depth":
        return objective
    if metric != "classification_bce":
        raise ValueError(f"unknown checkpoint selection metric: {metric}")
    if "logit" not in output:
        raise ValueError("classification_bce selection requires classifier logits")
    return nn.functional.binary_cross_entropy_with_logits(
        output["logit"], batch["label"].to(output["logit"].device))


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
    round6_binding = None
    if config.get("round6_registration"):
        from .round6 import Batch, environment, read
        batch = Batch(Path(__file__).resolve().parents[2], Path(config["round6_registration"]).parent)
        registration = batch.current()
        key = ("E3" if config["model"]["name"] == "cdcn_official_head" else "E1") + f"_{config['seed']}"
        folders = {}
        if key.startswith("E3_"):
            peer = "E1_" + str(config["seed"])
            folders[peer] = Path(read(batch.output / f"{peer}-run.json")["run"])
        if config != batch.config_for(key, folders, registration) or batch.freeze_path.exists():
            raise ValueError("Round 6 configuration differs from registration or is already frozen")
        round6_binding = {"registration_sha256": manifest_checksum(batch.registration_path),
                          "environment": environment()}
    require_depth, depth_snapshot = inspect_training_inputs(config)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    run_id = f'{config["experiment_id"]}_seed{config["seed"]}_{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")}'
    run_dir = Path(config.get("runs_dir", "runs")) / run_id; run_dir.mkdir(parents=True)
    if round6_binding is not None:
        (run_dir / "round6_binding.json").write_text(json.dumps(round6_binding, indent=2), encoding="utf-8")
    (run_dir / "config.yaml").write_text(config_path.read_text(encoding="utf-8"), encoding="utf-8")
    (run_dir / "environment.txt").write_text(f"python={sys.version}\nplatform={platform.platform()}\ntorch={torch.__version__}\ndevice={device}\n", encoding="utf-8")
    checksum = manifest_checksum(config["data"]["manifest"])
    (run_dir / "manifest_checksum.json").write_text(json.dumps({"sha256": checksum}, indent=2), encoding="utf-8")
    if config["model"]["name"] in {"cdcn_official", "cdcn_official_head"}:
        provenance = dict(OFFICIAL_CDCN_PROVENANCE)
        if config["model"]["name"] == "cdcn_official_head":
            provenance["modification"] = "DepthHead: Conv 1->8->16, global average pool, Linear 16->1"
        (run_dir / "model_provenance.json").write_text(
            json.dumps(provenance, indent=2) + "\n", encoding="utf-8"
        )
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
            normalization=config["data"].get("normalization", "imagenet"),
        )
        for split in ("train", "val")
    }
    loaders = {split: DataLoader(ds, batch_size=config["training"].get("batch_size", 16), shuffle=split == "train", num_workers=config["training"].get("workers", 0)) for split, ds in datasets.items()}
    model = build_model(config).to(device); history = []
    stages = config["training"].get("stages")
    if stages is None:
        stages = [{"name": "joint", "epochs": config["training"]["epochs"], "lr": config["training"]["lr"]}]
    if not stages or any(stage.get("name") not in {"depth", "head", "joint"}
                         or int(stage.get("epochs", 0)) <= 0
                         or float(stage.get("lr", 0)) <= 0 for stage in stages):
        raise ValueError("training stages require a known name, positive epochs and positive lr")
    initial = config["training"].get("init_checkpoint")
    if initial:
        load_initial_weights(model, initial, device)
        (run_dir / "initial_checkpoint.json").write_text(
            json.dumps({"path": str(initial), "sha256": manifest_checksum(initial)}, indent=2) + "\n",
            encoding="utf-8",
        )
    elif any(stage["name"] == "head" for stage in stages):
        raise ValueError("head-only training requires training.init_checkpoint from E1")
    selection_metric = config["training"].get("selection_metric", "val_loss")
    if selection_metric not in {"val_loss", "classification_bce"}:
        raise ValueError(f"unknown checkpoint selection metric: {selection_metric}")
    selections = []
    for stage_index, stage in enumerate(stages, 1):
        # The objectives of depth, head and joint stages are different. Reset
        # selection at every boundary and report only the final stage's best.
        best = float("inf")
        stage_checkpoint = run_dir / f"best_stage_{stage_index:02d}_{stage['name']}.ckpt"
        _set_stage(model, stage["name"])
        optimizer_class = (
            torch.optim.Adam
            if config["training"].get("optimizer", "adamw") == "adam"
            else torch.optim.AdamW
        )
        optimizer = optimizer_class(
            (p for p in model.parameters() if p.requires_grad),
            lr=stage["lr"],
            weight_decay=config["training"].get("weight_decay", 1e-4),
        )
        scheduler = None
        if config["training"].get("step_size"):
            scheduler = torch.optim.lr_scheduler.StepLR(
                optimizer,
                step_size=config["training"]["step_size"],
                gamma=config["training"].get("gamma", 0.5),
            )
        for epoch in range(stage["epochs"]):
            epoch_started = time.perf_counter()
            model.train(); losses = []
            for batch in loaders["train"]:
                optimizer.zero_grad(); output = model(batch["image"].to(device)); loss = _loss(config, output, batch, stage["name"]); loss.backward(); optimizer.step(); losses.append(loss.item())
            model.eval(); val_losses = []; selection_losses = []
            with torch.no_grad():
                for batch in loaders["val"]:
                    output = model(batch["image"].to(device))
                    objective = _loss(config, output, batch, stage["name"])
                    val_losses.append(objective.item())
                    selection_losses.append(_selection_loss(
                        selection_metric, output, batch, stage["name"], objective).item())
            row = {"stage": stage["name"], "epoch": epoch + 1,
                   "train_loss": float(np.mean(losses)), "val_loss": float(np.mean(val_losses)),
                   "val_selection_loss": float(np.mean(selection_losses))}; history.append(row)
            if not np.isfinite([row["train_loss"], row["val_loss"], row["val_selection_loss"]]).all():
                raise ValueError(f"non-finite loss in {stage['name']} epoch {epoch + 1}")
            if row["val_selection_loss"] < best:
                best = row["val_selection_loss"]
                torch.save({"model": model.state_dict(), "config": config,
                            "val_loss": row["val_loss"], "selection_value": best,
                            "selection_metric": "val_loss" if stage["name"] == "depth" else selection_metric,
                            "stage": stage["name"],
                            "stage_index": stage_index, "epoch": epoch + 1,
                            "global_epoch": len(history)}, stage_checkpoint)
            if scheduler is not None:
                scheduler.step()
            # Persist and report every epoch. This gives Colab-visible progress and
            # retains a valid partial log if a long GPU run is interrupted.
            log_path = run_dir / "train_log.csv"
            temporary_log = log_path.with_suffix(".csv.tmp")
            pd.DataFrame(history).to_csv(temporary_log, index=False)
            temporary_log.replace(log_path)
            elapsed = time.perf_counter() - epoch_started
            remaining = stage["epochs"] - epoch - 1
            print(
                f"[{stage['name']}] epoch {epoch + 1}/{stage['epochs']} "
                f"train_loss={row['train_loss']:.6f} "
                f"val_loss={row['val_loss']:.6f} "
                f"best={best:.6f} elapsed={elapsed:.1f}s "
                f"stage_eta={remaining * elapsed / 60:.1f}m",
                flush=True,
            )
        selected = torch.load(stage_checkpoint, map_location=device, weights_only=False)
        model.load_state_dict(selected["model"])
        shutil.copyfile(stage_checkpoint, run_dir / "best.ckpt")
        selections.append({key: selected[key] for key in
                           ("stage", "stage_index", "epoch", "global_epoch", "val_loss")})
        selections[-1].update({key: selected[key] for key in ("selection_metric", "selection_value")})
        (run_dir / "checkpoint_selection.json").write_text(
            json.dumps({"criterion": "minimum declared validation criterion within each stage",
                        "configured_selection_metric": selection_metric,
                        "reported_stage": stage["name"], "stages": selections}, indent=2) + "\n",
            encoding="utf-8",
        )
    pd.DataFrame(history).to_csv(run_dir / "train_log.csv", index=False)
    checkpoint = torch.load(run_dir / "best.ckpt", map_location=device, weights_only=False); model.load_state_dict(checkpoint["model"])
    frame_scores = score_loader(model, loaders["val"], device); frame_scores.to_csv(run_dir / "val_frame_scores.csv", index=False)
    video_scores = aggregate_video_scores(frame_scores, config["evaluation"].get("aggregation", "mean")); video_scores.to_csv(run_dir / "val_scores.csv", index=False)
    metrics = evaluate_scores(video_scores.label.to_numpy(), video_scores.score.to_numpy()); payload = metrics.to_dict()
    (run_dir / "threshold.json").write_text(json.dumps({"threshold": metrics.threshold, "source": "validation"}, indent=2), encoding="utf-8")
    (run_dir / "metrics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return run_dir
