"""Continue the frozen CDCN baseline and evaluate a fixed schedule on Dev."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import time

import torch
import cv2
import numpy as np

from cdcn_prnet_locked_test import verify_run
from cdcn_prnet_smoke import sha
from cdcn_prnet_train_pilot import read_recovery, train


def write_json(path, value):
    partial = path.with_suffix(path.suffix + ".part")
    partial.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    partial.replace(path)


def training_environment(device):
    gpu = device.type == "cuda"
    return {"gpu": torch.cuda.get_device_name(device) if gpu else None,
            "gpu_total_bytes": torch.cuda.get_device_properties(device).total_memory if gpu else None,
            "torch": str(torch.__version__), "cuda": torch.version.cuda,
            "cudnn": torch.backends.cudnn.version(), "opencv": cv2.__version__, "numpy": np.__version__,
            "deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
            "cudnn_deterministic": torch.backends.cudnn.deterministic,
            "cudnn_benchmark": torch.backends.cudnn.benchmark,
            "tf32_matmul": torch.backends.cuda.matmul.allow_tf32,
            "tf32_cudnn": torch.backends.cudnn.allow_tf32,
            "float32_matmul_precision": torch.get_float32_matmul_precision(),
            "cublas_workspace_config": os.environ.get("CUBLAS_WORKSPACE_CONFIG")}


def candidate(directory, config, epoch):
    path = directory / "pilot_result.json"
    report = json.loads(path.read_text(encoding="utf-8"))
    expected = {key: config[key] for key in ("seed", "batch", "assets_manifest_sha256", "architecture_source_commit")}
    if (any(report.get(key) != value for key, value in expected.items())
            or report.get("mode") != "full" or report.get("loader_workers") != config["workers"]
            or report.get("device") != config["device"] or report.get("train_videos") != 1200
            or report.get("dev_videos") != 900 or report.get("dev_frames_per_video") != 8
            or [row["epoch"] for row in report["history"]] != list(range(1, epoch + 1))
            or sha(directory / "checkpoint.pt") != report["checkpoint_sha256"]):
        raise ValueError(f"Unexpected scheduled training result in {directory}")
    return {"epoch": epoch, "run": str(directory), "checkpoint_sha256": report["checkpoint_sha256"],
            "report_sha256": sha(path), "dev": report["dev"]}


def save_selection(output, candidates, plan, complete):
    eligible = [item for item in candidates if "acer_pooled" in item["dev"]]
    best = min(eligible, key=lambda item: (item["dev"]["acer_pooled"], item["epoch"]))
    selection = {"plan": plan, "complete": complete, "candidates": candidates,
                 "selection_rule": "minimum Dev pooled ACER, earliest epoch breaks ties", "best": best}
    write_json(output / "dev_selection.json", selection)
    print(f"DEV_SELECTION epoch={best['epoch']} acer={best['dev']['acer_pooled']:.6f} {best['run']}", flush=True)


def continue_training(initial, assets, protocol, output, device, *, epochs=1300, dev_every=50,
                      checkpoint_every=5, workers=4):
    locked = verify_run(initial, protocol)
    source_report = json.loads((initial / "pilot_result.json").read_text(encoding="utf-8"))
    environment = training_environment(device)
    start = locked["epoch"]
    if epochs <= start or min(dev_every, checkpoint_every, workers) < 1:
        raise ValueError("Choose a later final epoch and positive evaluation, save and worker intervals")
    config = {"profile": "full", "seed": locked["seed"], "batch": locked["batch"], "workers": workers,
              "device": device.type, "assets_manifest_sha256": sha(assets / "smoke_summary.json"),
              "architecture_source_commit": source_report["architecture_source_commit"]}
    if config["assets_manifest_sha256"] != locked["assets_manifest_sha256"]:
        raise ValueError("Restore the original Train/Dev manifest before continuing")
    recovery = initial / "resume.pt"
    saved = read_recovery(recovery, config)
    weights = torch.load(initial / "checkpoint.pt", map_location="cpu", weights_only=True)
    if (len(saved["history"]) != start or saved["model"].keys() != weights.keys()
            or any(not torch.equal(value, weights[key]) for key, value in saved["model"].items())):
        raise ValueError("Initial resume.pt must contain the frozen epoch and identical baseline weights")
    del saved, weights
    milestones = list(range(start + dev_every, epochs, dev_every)) + [epochs]
    plan = {"source_run": str(initial), "source_report_sha256": locked["dev_report_sha256"],
            "source_resume_sha256": sha(recovery), "config": config, "milestones": milestones,
            "checkpoint_every": checkpoint_every, "protocol_sha256": locked["protocol_sha256"]}
    output.mkdir(parents=True, exist_ok=True)
    plan_path = output / "schedule.json"
    previous = json.loads(plan_path.read_text(encoding="utf-8")) if plan_path.exists() else {}
    if previous and any(previous.get(key) != value for key, value in plan.items()):
        raise ValueError("Use a separate output directory for a changed Dev schedule")
    observations = list(previous.get("environment_history", []))
    if not observations and previous.get("environment"):
        observations.append({"observed_at_utc": None, "runtime": previous["environment"]})
    observations.append({"observed_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                         "runtime": environment})
    plan.update(environment=environment, environment_history=observations,
                source_environment={key: source_report.get(key) for key in ("gpu", "torch", "opencv")})
    write_json(plan_path, plan)
    candidates = [candidate(initial, config, start)]
    save_selection(output, candidates, plan, complete=False)

    for target in milestones:
        segment = output / f"epoch-{target:04d}"
        completed = sorted(segment.glob("attempt-*/pilot_result.json"))
        if completed:
            finished = completed[0].parent
            item = candidate(finished, config, target)
            recovery = finished / "resume.pt"
            print(f"REUSE_DEV_EPOCH {target} {finished}", flush=True)
        else:
            recovered_epoch = len(read_recovery(recovery, config)["history"])
            for path in sorted(segment.glob("attempt-*/resume.pt")):
                epoch = len(read_recovery(path, config)["history"])
                if epoch > target:
                    raise ValueError(f"Recovery epoch exceeds this segment in {path}")
                if epoch > recovered_epoch:
                    recovered_epoch, recovery = epoch, path
            print(f"CONTINUE_EPOCH {recovered_epoch} -> {target} | recovery {recovery}", flush=True)
            finished = segment / f"attempt-{time.time_ns()}"
            train(assets, finished, device, target, locked["batch"], locked["seed"], "full", protocol,
                  workers, checkpoint_every=checkpoint_every, resume=recovery)
            item = candidate(finished, config, target)
            recovery = finished / "resume.pt"
        candidates.append(item)
        save_selection(output, candidates, plan, complete=target == epochs)
    print(f"CDCN_DEV_SCHEDULE_READY {output / 'dev_selection.json'}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("initial", "assets", "protocol", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=1300)
    parser.add_argument("--dev-every", type=int, default=50)
    parser.add_argument("--checkpoint-every", type=int, default=5)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if not torch.cuda.is_available():
        parser.error("Select an A100 runtime for the scheduled training run")
    continue_training(**vars(args), device=torch.device("cuda"))
