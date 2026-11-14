"""Train and score a bounded OULU P1 CDCN pilot with reconstructed PRNet assets."""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import time

import cv2
import numpy as np
import pandas as pd
import torch
from torch.nn import functional as F

from audit_cdc_n_p1_scores import NonFiniteDevThreshold, score
from cdcn_prnet_expanded import SUBJECT_COUNTS
from cdcn_prnet_smoke import PILOT_SLOTS, crop_bounds, sha
from deepface_pad.losses import OfficialContrastiveDepthLoss
from deepface_pad.models.cdcn_official import OfficialCDCN, OFFICIAL_CDCN_PROVENANCE
from deepface_pad.progress import Progress


def load_videos(root, profile="pilot"):
    manifest = json.loads((root / "smoke_summary.json").read_text(encoding="utf-8"))
    if manifest["failures"] or manifest.get("slots") != list(PILOT_SLOTS):
        raise ValueError("Use a complete eight-frame training pilot snapshot")
    if manifest.get("profile", "pilot") != profile:
        raise ValueError(f"Expected {profile} assets")
    splits = {"Train": defaultdict(list), "Dev": defaultdict(list)}
    for row in manifest["frames"]:
        video = row["video_id"]
        fields = video.split("_")
        if (len(fields) != 4 or not all(field.isascii() and field.isdigit() for field in fields)
                or row["frame_id"] < 1 or int(fields[-1]) != row["access"]
                or row["train_target_zero"] != (row["access"] != 1)):
            raise ValueError(f"Inconsistent video ID or label: {video}")
        splits[row["split"]][video].append(row)

    subjects = {}
    for split, videos in splits.items():
        expected = SUBJECT_COUNTS[split] * 5 if profile == "expanded" else (6 if manifest["wide_sample"] else 3)
        accesses = {1, 2, 3, 4, 5} if profile == "expanded" else {1, 2, 4}
        if len(videos) != expected or {rows[0]["access"] for rows in videos.values()} != accesses:
            raise ValueError(f"Incomplete {split} pilot membership")
        subjects[split] = {int(video.split("_")[2]) for video in videos}
        for video, rows in videos.items():
            rows.sort(key=lambda row: row["slot"])
            if ([row["slot"] for row in rows] != list(PILOT_SLOTS)
                    or len({row["frame_id"] for row in rows}) != len(PILOT_SLOTS)):
                raise ValueError(f"Incomplete or duplicate frames for {video}")
    if subjects["Train"] & subjects["Dev"]:
        raise ValueError("Train and Dev share subjects")
    return splits


def load_frame(root, row, scale):
    video, split = row["video_id"], row["split"]
    prefix = f"{video}_{row['frame_id']:03d}"
    scene = root / split / "images" / video / f"{prefix}_scene.jpg"
    depth = root / split / "maps" / video / f"{prefix}_depth1D.jpg"
    image = cv2.imread(str(scene))
    target = cv2.imread(str(depth), cv2.IMREAD_GRAYSCALE)
    if image is None or target is None or image.shape[:2] != target.shape:
        raise ValueError(f"Missing or misaligned RGB/depth: {prefix}")
    box = tuple(map(float, scene.with_suffix(".dat").read_text().splitlines()))
    roi = crop_bounds(box, image.shape, scale)
    image = cv2.resize(image[roi], (256, 256))
    target = cv2.resize(target[roi], (32, 32))
    if scale == 1.3 and int(target.sum()) != row["prnet_sum_32"]:
        raise ValueError(f"PRNet map sum changed: {prefix}")
    return image, target


def sample_training_frame(root, rows, rng):
    row = rows[int(rng.integers(len(rows)))]
    scale = rng.integers(12, 15) / 10
    image, depth = load_frame(root, row, scale)
    # Same color ranges as the public loader, implemented with NumPy for this pilot.
    image = np.clip(image.astype(np.float32) + rng.integers(-40, 41, size=3), 0, 255)
    image = np.floor(255 * (image / 255) ** rng.uniform(0.5, 1.5)).astype(np.float32)
    if rng.random() < 0.5:
        for _ in range(rng.integers(1, 3)):
            area, ratio = rng.uniform(0.01, 0.05) * 256**2, rng.uniform(0.5, 2)
            height, width = round((area * ratio)**0.5), round((area / ratio)**0.5)
            top, left = rng.integers(257 - height), rng.integers(257 - width)
            image[top:top+height, left:left+width] = (0.4914, 0.4822, 0.4465)
    if rng.random() < 0.5:
        image, depth = image[:, ::-1], depth[:, ::-1]
    y, x = rng.integers(256, size=2)
    half = rng.integers(1, 50) // 2
    image[max(0, y-half):y+half, max(0, x-half):x+half] = 0
    target = np.zeros((1, 32, 32), np.float32)
    if row["access"] == 1:
        target[0] = depth / 255.0
    return normalized_rgb(image), torch.from_numpy(target)


def normalized_rgb(image):
    rgb = (image[:, :, ::-1].astype(np.float32) - 127.5) / 128
    return torch.from_numpy(np.ascontiguousarray(rgb.transpose(2, 0, 1)))


def frame_ratios(depth, denominators):
    if not torch.isfinite(depth).all() or not torch.isfinite(denominators).all() or (denominators <= 0).any():
        raise ValueError("Dev scoring requires finite predictions and positive PRNet sums")
    return depth.flatten(1).sum(dim=1) / denominators


@torch.inference_mode()
def score_dev(model, root, videos, batch, device):
    model.eval()
    scores = []
    with Progress("Score Dev", len(videos), "videos") as progress:
        for done, (video, rows) in enumerate(sorted(videos.items()), 1):
            frames = [load_frame(root, row, 1.3) for row in rows]
            images = torch.stack([normalized_rgb(im) for im, _ in frames])
            totals = torch.tensor([int(depth.sum()) for _, depth in frames], dtype=torch.float32)
            ratios = []
            for rgb, sums in zip(images.split(batch), totals.split(batch)):
                depth = model(rgb.to(device))["depth"].cpu()
                ratios.append(frame_ratios(depth, sums))
            scores.append({"video_id": video, "label": int(rows[0]["access"] == 1),
                           "score": torch.cat(ratios).mean().item()})
            progress.update(done)
    return pd.DataFrame(scores)


def train(root, out, device, epochs, batch, seed, profile="pilot"):
    if epochs < 1 or batch < 1:
        raise ValueError("epochs and batch must be positive")
    cv2.setNumThreads(1)
    with Progress("Verify pilot manifest and Dev assets"):
        splits = load_videos(root, profile)
        for videos in splits.values():
            for rows in videos.values():
                for row in rows:
                    load_frame(root, row, 1.3)
    train_videos = sorted(splits["Train"])
    rng = np.random.default_rng(seed)
    torch.manual_seed(seed)
    model = OfficialCDCN(theta=0.7).to(device)
    contrast = OfficialContrastiveDepthLoss().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-4, weight_decay=5e-5)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=500, gamma=0.5)
    out.mkdir(parents=True, exist_ok=False)
    gpu = device.type == "cuda"
    if gpu:
        torch.cuda.reset_peak_memory_stats(device)
    history = []
    started = time.monotonic()
    for epoch in range(1, epochs + 1):
        model.train()
        begin = time.monotonic()
        shuffled = rng.permutation(train_videos)
        losses = []
        with Progress(f"Train epoch {epoch}/{epochs}", len(train_videos), "videos") as progress:
            for start in range(0, len(shuffled), batch):
                videos = shuffled[start:start+batch]
                images, targets = zip(*(sample_training_frame(root, splits["Train"][video], rng) for video in videos))
                target = torch.stack(targets).to(device)
                optimizer.zero_grad(set_to_none=True)
                prediction = model(torch.stack(images).to(device))["depth"]
                absolute, local = F.mse_loss(prediction, target), contrast(prediction, target)
                loss = absolute + local
                if not torch.isfinite(loss):
                    raise ValueError(f"Non-finite loss in epoch {epoch}")
                loss.backward()
                optimizer.step()
                losses.extend([(absolute.item(), local.item())] * len(videos))
                progress.update(start + len(videos))
        means = np.mean(losses, axis=0)
        history.append({"epoch": epoch, "depth_mse": float(means[0]), "contrast_mse": float(means[1]),
                        "seconds": time.monotonic() - begin, "updates": (len(shuffled) + batch - 1) // batch})
        print(json.dumps(history[-1]), flush=True)
        scheduler.step()
    compute_seconds = time.monotonic() - started
    peak_train = torch.cuda.max_memory_allocated(device) if gpu else None
    checkpoint = out / "checkpoint.pt"
    torch.save(model.state_dict(), checkpoint)
    with Progress("Reload checkpoint"):
        model.load_state_dict(torch.load(checkpoint, map_location="cpu", weights_only=True))
    dev_started = time.monotonic()
    dev = score_dev(model, root, splits["Dev"], batch, device)
    dev_seconds = time.monotonic() - dev_started
    dev.to_csv(out / "dev_scores.csv", index=False)
    # A collapsed score has no useful ROC threshold and is reported explicitly.
    if dev.score.nunique() == 1:
        metrics = {"status": "constant_scores", "score": float(dev.score.iloc[0])}
    else:
        try:
            evaluated = score(dev, dev)
        except NonFiniteDevThreshold:
            metrics = {"status": "non_finite_threshold"}
        else:
            metrics = evaluated["dev"] | {"threshold_from_dev": evaluated["threshold_from_dev"]}
    result = {"mode": profile, "seed": seed, "batch": batch, "device": str(device),
              "gpu": torch.cuda.get_device_name(device) if gpu else None, "torch": torch.__version__,
              "opencv": cv2.__version__, "architecture_source_commit": OFFICIAL_CDCN_PROVENANCE["git_commit"],
              "train_videos": len(train_videos), "dev_videos": len(dev), "dev_frames_per_video": len(PILOT_SLOTS),
              "history": history, "dev": metrics, "train_seconds": compute_seconds, "dev_seconds": dev_seconds,
              "peak_train_gpu_allocated_bytes": peak_train, "checkpoint_sha256": sha(checkpoint),
              "assets_manifest_sha256": sha(root / "smoke_summary.json")}
    (out / "pilot_result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"CDCN_TRAIN_PILOT_READY {out}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch", type=int, default=3)
    parser.add_argument("--seed", type=int, default=43)
    parser.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    parser.add_argument("--profile", choices=("pilot", "expanded"), default="pilot")
    args = parser.parse_args()
    if args.device == "cuda" and not torch.cuda.is_available():
        parser.error("Select a Colab GPU runtime or pass --device cpu")
    train(args.assets, args.output, torch.device(args.device), args.epochs, args.batch, args.seed, args.profile)
