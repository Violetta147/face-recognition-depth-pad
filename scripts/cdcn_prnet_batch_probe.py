"""Measure CDCN FP32 training throughput after RGB/depth preparation."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
import time

import cv2
import numpy as np
import torch
from torch.nn import functional as F

from cdcn_prnet_train_pilot import load_videos, sample_training_frame, sha
from deepface_pad.losses import OfficialContrastiveDepthLoss
from deepface_pad.models.cdcn_official import OfficialCDCN
from deepface_pad.progress import Progress


def prepare_pool(root, seed):
    # Cycle through all eight frames per Train video before repeating samples.
    videos = load_videos(root)["Train"]
    rng = np.random.default_rng(seed)
    order = [(rows[slot],) for slot in range(8) for _, rows in sorted(videos.items())]
    rng.shuffle(order)
    with Progress("Decode and augment probe inputs", len(order), "frames") as progress:
        samples = []
        for done, row in enumerate(order, 1):
            samples.append(sample_training_frame(root, row, rng))
            progress.update(done)
    images, targets = zip(*samples)
    return torch.stack(images), torch.stack(targets)


def measure_batch(pool, batch, warmup, steps, seed, device):
    torch.manual_seed(seed)
    model = OfficialCDCN(theta=0.7).to(device).train()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-4, weight_decay=5e-5)
    contrast = OfficialContrastiveDepthLoss().to(device)
    gpu = device.type == "cuda"
    if gpu:
        torch.cuda.reset_peak_memory_stats(device)
    durations = []
    with Progress(f"FP32 batch {batch}", warmup + steps, "updates") as progress:
        for step in range(warmup + steps):
            indices = torch.arange(step * batch, (step + 1) * batch) % len(pool[0])
            images, targets = (values[indices] for values in pool)
            started = time.perf_counter()
            image, target = images.to(device), targets.to(device)
            optimizer.zero_grad(set_to_none=True)
            prediction = model(image)["depth"]
            loss = F.mse_loss(prediction, target) + contrast(prediction, target)
            loss.backward()
            optimizer.step()
            if not torch.isfinite(loss).item():
                raise ValueError(f"Non-finite loss for batch {batch}")
            if gpu:
                torch.cuda.synchronize(device)
            if step >= warmup:
                durations.append(time.perf_counter() - started)
            progress.update(step + 1)
    median = statistics.median(durations)
    return {"batch": batch, "status": "ok", "median_update_seconds": median,
            "frames_per_second": batch / median, "update_seconds": durations,
            "peak_allocated_bytes": torch.cuda.max_memory_allocated(device) if gpu else None,
            "peak_reserved_bytes": torch.cuda.max_memory_reserved(device) if gpu else None}


def probe(root, out, batches, warmup, steps, seed, device):
    cv2.setNumThreads(1)
    gpu = device.type == "cuda"
    started = time.perf_counter()
    pool = prepare_pool(root, seed)
    seconds = time.perf_counter() - started
    report = {"mode": "fp32_compute_probe", "torch": torch.__version__, "opencv": cv2.__version__,
              "device": str(device), "gpu": torch.cuda.get_device_name(device) if gpu else None,
              "gpu_total_bytes": torch.cuda.get_device_properties(device).total_memory if gpu else None,
              "tf32_matmul": torch.backends.cuda.matmul.allow_tf32 if gpu else None,
              "tf32_cudnn": torch.backends.cudnn.allow_tf32 if gpu else None,
              "seed": seed, "warmup_updates": warmup, "timed_updates": steps,
              "preparation_seconds": seconds, "cached_train_frames": len(pool[0]),
              "manifest_sha256": sha(root / "smoke_summary.json"), "batches": []}
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        raise FileExistsError(out)
    for batch in batches:
        if gpu:
            torch.cuda.empty_cache()
        try:
            row = measure_batch(pool, batch, warmup, steps, seed, device)
        except torch.cuda.OutOfMemoryError:
            row = {"batch": batch, "status": "out_of_memory"}
        report["batches"].append(row)
        print(json.dumps(row), flush=True)
        partial = out.with_suffix(".json.part")
        partial.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        partial.replace(out)
    print("CDCN_BATCH_PROBE_READY", out, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--batches", type=int, nargs="+", default=(8, 16, 32, 56))
    parser.add_argument("--warmup", type=int, default=2)
    parser.add_argument("--steps", type=int, default=6)
    parser.add_argument("--seed", type=int, default=43)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    args = parser.parse_args()
    if min(args.batches) < 1 or args.warmup < 1 or args.steps < 1:
        parser.error("batch sizes, warm-up updates, and timed updates must be positive")
    if args.device == "cuda" and not torch.cuda.is_available():
        parser.error("Select a GPU runtime or pass --device cpu")
    probe(args.assets, args.output, args.batches, args.warmup, args.steps, args.seed, torch.device(args.device))
