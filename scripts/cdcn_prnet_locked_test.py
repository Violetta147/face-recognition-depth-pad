"""Score OULU-NPU P1 Test with the frozen 100-epoch CDCN and Dev threshold."""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import time

import cv2
import torch

from audit_cdc_n_p1_scores import rates
from cdcn_prnet_expanded import full_membership, video_assets
from cdcn_prnet_smoke import DEPTH_COMMIT, INDEX_SHA, PILOT_SLOTS, PRNET_COMMIT, WEIGHT_SHA, sha
from cdcn_prnet_train_pilot import score_videos
from deepface_pad.colab_cache import copy_progress
from deepface_pad.models.cdcn_official import OFFICIAL_CDCN_PROVENANCE, OfficialCDCN


RUN_NAME = "train-1794973542248985819"
LOCK = {
    "protocol": 1,
    "protocol_sha256": "efb3ada89450c8c1d447fa947c68d164e4e73001e24d06afbb16034f0da73d6d",
    "checkpoint_sha256": "ec0a3ecc6828cedc7bfb34c87affabe7b8469fbc8b33a40cf1a7cadedbbe0497",
    "assets_manifest_sha256": "5fb7ca14a195e4fd6347475574519e4f1c59f79fda5890b9ee833a1586a4357d",
    "threshold_from_dev": 0.0007160214008763433,
    "epoch": 100,
    "seed": 43,
    "batch": 56,
}


def verify_run(run, protocol):
    report_path = run / "pilot_result.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    expected = {key: LOCK[key] for key in ("checkpoint_sha256", "assets_manifest_sha256", "seed", "batch")}
    expected.update(mode="full", train_videos=1200, dev_videos=900, dev_frames_per_video=8,
                    architecture_source_commit=OFFICIAL_CDCN_PROVENANCE["git_commit"])
    if (run.name != RUN_NAME or any(report.get(key) != value for key, value in expected.items())
            or [row["epoch"] for row in report["history"]] != list(range(1, LOCK["epoch"] + 1))
            or report["dev"]["threshold_from_dev"] != LOCK["threshold_from_dev"]):
        raise ValueError(f"Result does not match the locked 100-epoch run: {report_path}")
    if sha(protocol) != LOCK["protocol_sha256"]:
        raise ValueError(f"Unexpected OULU-NPU protocol TAR: {protocol}")
    if sha(run / "checkpoint.pt") != LOCK["checkpoint_sha256"]:
        raise ValueError(f"Unexpected checkpoint SHA-256: {run / 'checkpoint.pt'}")
    return {**LOCK, "training_run": run.name, "dev_report_sha256": sha(report_path),
            "threshold_rule": "video score > threshold is bona fide"}


def load_test_videos(assets, protocol):
    manifest = json.loads((assets / "smoke_summary.json").read_text(encoding="utf-8"))
    if (manifest["failures"] or manifest["profile"] != "full"
            or manifest["protocol_sha256"] != LOCK["protocol_sha256"]
            or manifest["slots"] != list(PILOT_SLOTS)
            or manifest["source"] != {"prnet": PRNET_COMMIT, "renderer": DEPTH_COMMIT}
            or manifest["weight_sha256"] != WEIGHT_SHA or manifest["weight_index_sha256"] != INDEX_SHA):
        raise ValueError("Use the complete Test assets prepared by the locked MTCNN–PRNet pipeline")
    expected = full_membership(protocol, splits=("Test",))["Test"]
    videos = defaultdict(list)
    for row in manifest["frames"]:
        videos[row["video_id"]].append(row)
    if len(expected) != 600 or videos.keys() != expected.keys():
        raise ValueError("Test manifest must contain all 600 official Protocol 1 videos")
    for video, rows in videos.items():
        rows.sort(key=lambda row: row["slot"])
        video_assets(rows, "Test", video, expected[video])
    return videos


def evaluate(run, assets, protocol, work, output, device):
    if (output / "test_metrics.json").is_file():
        raise FileExistsError(f"Test metrics already saved in {output}")
    binding = verify_run(run, protocol)
    expected_lock = json.loads((output / "test_lock.json").read_text(encoding="utf-8"))
    if binding != expected_lock:
        raise ValueError("The locked run changed between preparation and scoring")
    videos = load_test_videos(assets, protocol)
    checkpoint = copy_progress(run / "checkpoint.pt", work / "checkpoint.pt", "Stage checkpoint")
    if sha(checkpoint) != binding["checkpoint_sha256"]:
        raise ValueError("Runtime checkpoint copy failed verification")

    cv2.setNumThreads(1)
    model = OfficialCDCN(theta=0.7).to(device)
    model.load_state_dict(torch.load(checkpoint, map_location="cpu", weights_only=True))
    started = time.monotonic()
    scores = score_videos(model, assets, videos, binding["batch"], device, split="Test")
    metrics = {
        **binding, "split": "Test", "videos": len(videos), "frames_per_video": len(PILOT_SLOTS),
        "test_assets_manifest_sha256": sha(assets / "smoke_summary.json"),
        "test": rates(scores, binding["threshold_from_dev"]),
        "score_seconds": round(time.monotonic() - started, 3),
        "device": str(device), "gpu": torch.cuda.get_device_name(device) if device.type == "cuda" else None,
        "torch": torch.__version__, "opencv": cv2.__version__,
    }
    scores_path = work / "test_scores.csv"
    scores.to_csv(scores_path, index=False)
    metrics["test_scores_sha256"] = sha(scores_path)
    metrics_path = work / "test_metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    copy_progress(scores_path, output / scores_path.name, "Save Test video scores")
    if sha(output / scores_path.name) != metrics["test_scores_sha256"]:
        raise OSError("Saved Test scores failed verification")
    copy_progress(metrics_path, output / metrics_path.name, "Save Test metrics")
    print(metrics_path.read_text(encoding="utf-8"), flush=True)
    print("CDCN_LOCKED_TEST_READY", output, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("run", "assets", "protocol", "work", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    args = parser.parse_args()
    evaluate(**(vars(args) | {"device": torch.device(args.device)}))
