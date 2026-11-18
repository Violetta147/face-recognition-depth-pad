"""Train and score a bounded OULU P1 CDCN pilot with reconstructed PRNet assets."""
from __future__ import annotations

import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from contextlib import suppress
import json
from pathlib import Path
import shutil
import tempfile
import time
from uuid import uuid4

import cv2
import numpy as np
import pandas as pd
import torch
from torch.nn import functional as F

from audit_cdc_n_p1_scores import NonFiniteDevThreshold, score
from cdcn_prnet_expanded import FULL_COUNTS, FULL_TRAIN_SLOTS, SUBJECT_COUNTS, full_membership
from cdcn_prnet_smoke import PILOT_SLOTS, crop_bounds, sha
from deepface_pad.losses import OfficialContrastiveDepthLoss
from deepface_pad.models.cdcn_official import OfficialCDCN, OFFICIAL_CDCN_PROVENANCE
from deepface_pad.progress import Progress


RECOVERY_FORMAT = "cdcn-prnet-resume-v1"


def load_videos(root, profile="pilot", protocol=None):
    manifest = json.loads((root / "smoke_summary.json").read_text(encoding="utf-8"))
    if manifest["failures"] or manifest.get("slots") != list(PILOT_SLOTS):
        raise ValueError("Use a complete eight-frame training pilot snapshot")
    if manifest.get("profile", "pilot") != profile:
        raise ValueError(f"Expected {profile} assets")
    membership = None
    if profile == "full":
        if protocol is None or manifest["protocol_sha256"] != sha(protocol):
            raise ValueError("Full training requires the matching official protocol TAR")
        if manifest.get("train_slots") != list(FULL_TRAIN_SLOTS):
            raise ValueError("Full training requires the configured Train frame pool")
        membership = full_membership(protocol)
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
        if profile == "full":
            expected = FULL_COUNTS[split]
        elif profile == "expanded":
            expected = SUBJECT_COUNTS[split] * 5
        else:
            expected = 6 if manifest["wide_sample"] else 3
        accesses = {1, 2, 4} if profile == "pilot" else {1, 2, 3, 4, 5}
        slots = FULL_TRAIN_SLOTS if profile == "full" and split == "Train" else PILOT_SLOTS
        if len(videos) != expected or {rows[0]["access"] for rows in videos.values()} != accesses:
            raise ValueError(f"Incomplete {split} membership")
        if membership is not None and videos.keys() != membership[split].keys():
            raise ValueError(f"{split} video IDs differ from Protocol 1")
        subjects[split] = {int(video.split("_")[2]) for video in videos}
        for video, rows in videos.items():
            rows.sort(key=lambda row: row["slot"])
            if ([row["slot"] for row in rows] != list(slots)
                    or len({row["frame_id"] for row in rows}) != len(slots)):
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
def score_videos(model, root, videos, batch, device, *, split):
    model.eval()
    scores = []
    with Progress(f"Score {split}", len(videos), "videos") as progress:
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


def score_dev(model, root, videos, batch, device):
    return score_videos(model, root, videos, batch, device, split="Dev")


def publish_recovery(state, local, destination):
    local.parent.mkdir(parents=True, exist_ok=True)
    partial = local.with_suffix(".pt.part")
    try:
        torch.save(state, partial)
        partial.replace(local)
    finally:
        partial.unlink(missing_ok=True)
    mirror = destination.with_suffix(".pt.part")
    try:
        shutil.copyfile(local, mirror)
        if sha(local) != sha(mirror):
            raise OSError("Recovery checkpoint copy differs from the local file")
        mirror.replace(destination)
    except OSError as exc:
        raise OSError(f"Could not publish recovery checkpoint. Local checkpoint: {local}") from exc
    finally:
        with suppress(OSError):
            mirror.unlink(missing_ok=True)


def read_recovery(path, config):
    with tempfile.TemporaryDirectory() as directory:
        local = Path(directory) / "resume.pt"
        shutil.copyfile(path, local)
        state = torch.load(local, map_location="cpu", weights_only=True)
    if (not isinstance(state, dict) or state.get("format") != RECOVERY_FORMAT
            or state.get("config") != config):
        raise ValueError("Use a resume.pt matching this manifest, training configuration and device type")
    history = state["history"]
    if not history or [row["epoch"] for row in history] != list(range(1, len(history) + 1)):
        raise ValueError("Recovery checkpoint has invalid epoch history")
    return state


def train(root, out, device, epochs, batch, seed, profile="pilot", protocol=None, workers=1,
          *, checkpoint_every=0, resume=None):
    if min(epochs, batch, workers) < 1 or checkpoint_every < 0:
        raise ValueError("epochs, batch and workers must be positive and checkpoint_every nonnegative")
    cv2.setNumThreads(1)
    with Progress("Verify training manifest and assets"):
        splits = load_videos(root, profile, protocol)
        if profile != "full":
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
    gpu = device.type == "cuda"
    config = {
        "profile": profile, "seed": seed, "batch": batch, "workers": workers, "device": device.type,
        "assets_manifest_sha256": sha(root / "smoke_summary.json"),
        "architecture_source_commit": OFFICIAL_CDCN_PROVENANCE["git_commit"],
    }
    history = []
    if resume is not None:
        saved = read_recovery(resume, config)
        history = saved["history"]
        if epochs < len(history):
            raise ValueError(f"Set epochs to at least the saved epoch, {len(history)}")
        model.load_state_dict(saved["model"])
        optimizer.load_state_dict(saved["optimizer"])
        scheduler.load_state_dict(saved["scheduler"])
        rng.bit_generator.state = saved["numpy_rng"]
        torch.set_rng_state(saved["torch_rng"])
        if gpu:
            torch.cuda.set_rng_state(saved["cuda_rng"], device)
        print(f"RESUMED_EPOCH {len(history)} {resume}", flush=True)
    resumed_from_epoch = len(history)
    out.mkdir(parents=True, exist_ok=False)
    local_recovery = root.parent / "training-recovery" / f"{out.name}-{uuid4().hex}" / "resume.pt"

    def save_recovery(history):
        epoch = history[-1]["epoch"]
        if epoch % checkpoint_every and epoch != epochs:
            return
        state = {
            "format": RECOVERY_FORMAT, "config": config, "history": history,
            "model": model.state_dict(), "optimizer": optimizer.state_dict(),
            "scheduler": scheduler.state_dict(), "numpy_rng": rng.bit_generator.state,
            "torch_rng": torch.get_rng_state(), "cuda_rng": torch.cuda.get_rng_state(device) if gpu else None,
        }
        destination = out / "resume.pt"
        publish_recovery(state, local_recovery, destination)
        print(f"RECOVERY_CHECKPOINT epoch={epoch} {destination}", flush=True)

    if gpu:
        torch.cuda.reset_peak_memory_stats(device)
    started = time.monotonic()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        history = train_epochs(model, contrast, optimizer, scheduler, train_videos, splits["Train"],
                               root, device, epochs, batch, rng, pool, workers, history=history,
                               on_epoch_end=save_recovery if checkpoint_every else None)
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
    metrics = dev_metrics(dev)
    result = {"mode": profile, "seed": seed, "batch": batch, "device": str(device),
              "gpu": torch.cuda.get_device_name(device) if gpu else None, "torch": torch.__version__,
              "opencv": cv2.__version__, "architecture_source_commit": OFFICIAL_CDCN_PROVENANCE["git_commit"],
              "train_videos": len(train_videos), "dev_videos": len(dev), "dev_frames_per_video": len(PILOT_SLOTS),
              "history": history, "dev": metrics, "train_seconds": compute_seconds, "dev_seconds": dev_seconds,
              "peak_train_gpu_allocated_bytes": peak_train, "checkpoint_sha256": sha(checkpoint),
              "assets_manifest_sha256": config["assets_manifest_sha256"]}
    if resume is not None:
        result["resumed_from_epoch"] = resumed_from_epoch
    if profile == "full":
        result.update(train_frames_per_video=len(FULL_TRAIN_SLOTS), loader_workers=workers)
    (out / "pilot_result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"CDCN_TRAIN_PILOT_READY {out}", flush=True)


def train_epochs(model, contrast, optimizer, scheduler, train_videos, videos_by_id,
                 root, device, epochs, batch, rng, pool, workers, *, history=None, on_epoch_end=None):
    history = [] if history is None else history
    for epoch in range(len(history) + 1, epochs + 1):
        model.train()
        begin = time.monotonic()
        shuffled = rng.permutation(train_videos)
        losses = []
        load_seconds = 0.0
        with Progress(f"Train epoch {epoch}/{epochs}", len(train_videos), "videos") as progress:
            for start in range(0, len(shuffled), batch):
                videos = shuffled[start:start+batch]
                load_started = time.monotonic()
                if workers == 1:
                    samples = [sample_training_frame(root, videos_by_id[video], rng) for video in videos]
                else:
                    seeds = rng.integers(0, 2**63, size=len(videos))
                    jobs = [pool.submit(sample_training_frame, root, videos_by_id[video], np.random.default_rng(seed))
                            for video, seed in zip(videos, seeds)]
                    samples = [job.result() for job in jobs]
                load_seconds += time.monotonic() - load_started
                images, targets = zip(*samples)
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
                        "seconds": time.monotonic() - begin, "load_seconds": load_seconds,
                        "updates": (len(shuffled) + batch - 1) // batch})
        print(json.dumps(history[-1]), flush=True)
        scheduler.step()
        if on_epoch_end is not None:
            on_epoch_end(history)
    return history


def dev_metrics(dev):
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
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch", type=int, default=3)
    parser.add_argument("--seed", type=int, default=43)
    parser.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    parser.add_argument("--profile", choices=("pilot", "expanded", "full"), default="pilot")
    parser.add_argument("--protocol", type=Path)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--checkpoint-every", type=int, default=0)
    parser.add_argument("--resume", type=Path)
    args = parser.parse_args()
    if args.device == "cuda" and not torch.cuda.is_available():
        parser.error("Select a Colab GPU runtime or pass --device cpu")
    train(args.assets, args.output, torch.device(args.device), args.epochs, args.batch, args.seed,
          args.profile, args.protocol, args.workers, checkpoint_every=args.checkpoint_every, resume=args.resume)
