"""Configuration and bounded CUDA throughput probe for OULU P1 E1."""
from __future__ import annotations

import time

import torch
from torch.utils.data import DataLoader, Subset

from .data import PadDataset
from .progress import Progress
from .train import _loss, build_model, seed_everything


def e1_config(root, runs, batch_size):
    if batch_size not in (8, 16):
        raise ValueError("E1 batch must be one of the registered candidates: 8 or 16")
    return {
        "experiment_id": "OULU_P1_E1_CDCN",
        "seed": 43,
        "runs_dir": str(runs),
        "model": {"name": "cdcn_official", "theta": 0.7},
        "data": {
            "root": str(root), "manifest": str(root / "train_dev_with_depth.csv"),
            "source_manifest": str(root / "train_dev.csv"),
            "depth_ledger": str(root / "depth/depth_status.csv"), "image_size": 256,
            "normalization": "cdcn_official",
        },
        "loss": {"implementation": "official_cdcn", "lambda_abs": 1.0, "lambda_contrast": 1.0},
        "training": {"epochs": 5, "batch_size": batch_size, "workers": 2, "precision": "bf16",
                     "optimizer": "adam", "lr": 1e-4, "weight_decay": 5e-5,
                     "selection_metric": "oulu_video_acer"},
        "evaluation": {"protocol": "oulu_npu", "aggregation": "mean"},
    }


def probe(config):
    """Compare the same 64 timed samples after warming up on the same 32 samples."""
    seed_everything(config["seed"])
    device = torch.device("cuda")
    data = config["data"]
    settings = config["training"]
    batch_size = settings["batch_size"]
    dataset = PadDataset(data["manifest"], data["root"], "train", data["image_size"], True,
                         require_depth=True, normalization=data["normalization"])
    selection = torch.randperm(len(dataset), generator=torch.Generator().manual_seed(config["seed"]))[:96].tolist()
    if len(selection) != 96:
        raise ValueError("the E1 probe expects at least 96 Train frames")
    loader = DataLoader(Subset(dataset, selection), batch_size=batch_size, pin_memory=True,
                        num_workers=settings["workers"])
    torch.cuda.reset_peak_memory_stats()
    model = build_model(config).to(device).train()
    optimizer = torch.optim.Adam(model.parameters(), lr=settings["lr"], weight_decay=settings["weight_decay"])
    with Progress(f"E1 probe batch {batch_size}", len(loader), "batches") as progress:
        for index, batch in enumerate(loader):
            if index == 32 // batch_size:
                torch.cuda.synchronize()
                started = time.perf_counter()
            optimizer.zero_grad()
            with torch.autocast("cuda", dtype=torch.bfloat16):
                output = model(batch["image"].to(device, non_blocking=True))
            loss = _loss(config, {key: value.float() for key, value in output.items()}, batch)
            loss.backward()
            optimizer.step()
            progress.update(index + 1)
        torch.cuda.synchronize()
    if not torch.isfinite(loss).item():
        raise ValueError(f"non-finite probe loss for batch {batch_size}")
    return {"batch_size": batch_size, "frames_per_second": 64 / (time.perf_counter() - started),
            "peak_gpu_allocated_bytes": torch.cuda.max_memory_allocated()}
