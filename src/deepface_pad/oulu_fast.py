"""Deadline run for the MobileNetV3 OULU-NPU baseline."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

import pandas as pd
import torch
import yaml
from torch.utils.data import DataLoader, Subset

from .data import PadDataset, manifest_checksum, validate_manifest
from .metrics import aggregate_video_scores
from .oulu_metrics import attach_attack_types, oulu_metrics
from .oulu_npu import atomic_text, write_json
from .progress import Progress
from .train import build_model, run, score_loader, seed_everything


def checked_manifest(path, root, split):
    info = json.loads(path.with_suffix(".json").read_text())
    if info["manifest_sha256"] != manifest_checksum(path) or info["split"] != split:
        raise ValueError(f"unexpected manifest identity: {path}")
    errors = validate_manifest(path, root, require_subject_disjoint=True, check_files=False)
    if errors:
        raise ValueError(errors)
    frame = pd.read_csv(path, keep_default_na=False)
    if set(frame.split) != {split}:
        raise ValueError(f"unexpected split: {path}")
    with Progress(f"{split}: verify crop hashes", len(frame), "frames") as progress:
        for number, row in enumerate(frame.itertuples(index=False), 1):
            if manifest_checksum(root / row.image_path) != row.image_sha256:
                raise ValueError(f"changed crop: {row.image_path}")
            progress.update(number)
    identity = {key: info[key] for key in ("protocol", "fold", "pilot", "protocol_sha256",
                                         "crop_version", "detector_sha256", "opencv", "frames_per_video")}
    return frame, identity


def config_for(root, manifest, runs, batch, workers, epochs, precision, seed):
    return {
        "experiment_id": "OULU_FAST_MOBILENET", "seed": seed, "runs_dir": str(runs),
        "model": {"name": "mobilenet_v3_small", "pretrained": True},
        "data": {"manifest": str(manifest), "root": str(root), "image_size": 224},
        "loss": {"classification": "bce"},
        "training": {"epochs": epochs, "lr": 3e-4, "batch_size": batch, "workers": workers,
                     "optimizer": "adamw", "weight_decay": 1e-4, "precision": precision,
                     "selection_metric": "oulu_video_acer"},
        "evaluation": {"protocol": "oulu_npu", "aggregation": "mean"},
    }


def benchmark(root, manifest, batch, workers, precision):
    seed_everything(43)
    device = torch.device("cuda")
    model = build_model({"model": {"name": "mobilenet_v3_small", "pretrained": False}}).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4)
    data = PadDataset(manifest, root, "train", 224, augment=True)
    sample = torch.randperm(len(data), generator=torch.Generator().manual_seed(43)).tolist()[:768]
    loader = DataLoader(Subset(data, sample), batch_size=batch, num_workers=workers, pin_memory=True)
    torch.cuda.reset_peak_memory_stats()
    measured = 0
    started = None
    for index, row in enumerate(loader):
        if index == 2:
            torch.cuda.synchronize()
            started = time.perf_counter()
        x = row["image"].to(device, non_blocking=True)
        y = row["label"].to(device, non_blocking=True)
        optimizer.zero_grad(set_to_none=True)
        with torch.autocast("cuda", dtype=torch.bfloat16, enabled=precision == "bf16"):
            logits = model(x)["logit"]
        torch.nn.functional.binary_cross_entropy_with_logits(logits.float(), y).backward()
        optimizer.step()
        if started is not None:
            measured += len(y)
    torch.cuda.synchronize()
    if started is None:
        raise ValueError("throughput probe requires at least three batches")
    return {"batch": batch, "samples_per_second": measured / (time.perf_counter() - started),
            "peak_gpu_allocated_bytes": torch.cuda.max_memory_allocated()}


def train_fast(root, directory, runs, workers, epochs, seed, batch, precision):
    train, identity = checked_manifest(directory / "train.csv", root, "train")
    dev, dev_identity = checked_manifest(directory / "val.csv", root, "val")
    if identity != dev_identity or set(train.subject_id) & set(dev.subject_id):
        raise ValueError("mismatched train/dev preparation or overlapping subjects")
    runs.mkdir(parents=True, exist_ok=True)
    attempt = runs / f"setup-{time.time_ns()}"
    attempt.mkdir()
    manifest = attempt / "train_dev.csv"
    atomic_text(manifest, pd.concat([train, dev], ignore_index=True).to_csv(index=False))
    if batch == 0:
        results = []
        for candidate in (64, 128):
            try:
                with Progress(f"Benchmark batch {candidate}"):
                    result = benchmark(root, manifest, candidate, workers, precision)
            except torch.cuda.OutOfMemoryError:
                result = {"batch": candidate, "status": "out_of_memory"}
            torch.cuda.empty_cache()
            results.append(result)
            print(result, flush=True)
        write_json(attempt / "throughput.json", {"candidates": results})
        valid = [row for row in results if "samples_per_second" in row]
        if not valid:
            raise ValueError("both batch sizes ran out of GPU memory")
        batch = max(valid, key=lambda row: row["samples_per_second"])["batch"]
    config = config_for(root, manifest, runs, batch, workers, epochs, precision, seed)
    config_path = attempt / "config.yaml"
    atomic_text(config_path, yaml.safe_dump(config, sort_keys=False))
    output = run(config_path)
    write_json(output / "freeze.json", {
        "preparation": identity, "train_manifest_sha256": manifest_checksum(manifest),
        "sha256": {name: manifest_checksum(output / name) for name in ("best.ckpt", "config.yaml", "threshold.json")},
    })
    print(f"RUN_DIR={output}", flush=True)


def score_test(root, manifest, output):
    freeze = json.loads((output / "freeze.json").read_text())
    test, identity = checked_manifest(manifest, root, "test")
    if identity != freeze["preparation"] or identity["pilot"]:
        raise ValueError("test requires matching full-run preparation")
    for name, expected in freeze["sha256"].items():
        if manifest_checksum(output / name) != expected:
            raise ValueError(f"changed frozen file: {name}")
    if (output / "test_metrics.json").exists():
        raise FileExistsError(output / "test_metrics.json")
    config = yaml.safe_load((output / "config.yaml").read_text())
    config["model"]["pretrained"] = False
    threshold = json.loads((output / "threshold.json").read_text())
    if threshold["source"] != "validation":
        raise ValueError("expected a dev threshold")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = build_model(config).to(device)
    model.load_state_dict(torch.load(output / "best.ckpt", map_location=device, weights_only=True)["model"])
    data = PadDataset(manifest, root, "test", config["data"]["image_size"])
    loader = DataLoader(data, batch_size=config["training"]["batch_size"], num_workers=config["training"]["workers"])
    scores = score_loader(model, loader, device)
    videos = attach_attack_types(aggregate_video_scores(scores), test)
    metrics = oulu_metrics(videos, threshold["threshold"])
    atomic_text(output / "test_frame_scores.csv", scores.to_csv(index=False))
    atomic_text(output / "test_scores.csv", videos.to_csv(index=False))
    write_json(output / "test_metrics.json", metrics | {"test_manifest_sha256": manifest_checksum(manifest)})
    print(json.dumps(metrics, indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    train = commands.add_parser("train")
    score = commands.add_parser("score")
    for command in (train, score):
        command.add_argument("--root", type=Path, required=True)
    train.add_argument("--directory", type=Path, required=True)
    train.add_argument("--runs", type=Path, required=True)
    train.add_argument("--batch", type=int, default=0)
    train.add_argument("--workers", type=int, default=2)
    train.add_argument("--epochs", type=int, default=3)
    train.add_argument("--seed", type=int, default=43)
    train.add_argument("--precision", choices=("fp32", "bf16"), default="bf16")
    score.add_argument("--manifest", type=Path, required=True)
    score.add_argument("--output", type=Path, required=True)
    args = vars(parser.parse_args())
    action = train_fast if args.pop("command") == "train" else score_test
    action(**args)


if __name__ == "__main__":
    main()
