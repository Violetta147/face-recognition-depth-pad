"""Verify saved CDCN P1 results and describe errors at the frozen Dev threshold."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd
from sklearn.metrics import roc_auc_score

from audit_cdc_n_p1_scores import load_scores, score
from deepface_pad.oulu_npu import expected_ids


def file_sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked_scores(path, split):
    frame = load_scores(path)
    parts = frame.video_id.str.extract(r"^([1-6])_([1-3])_(\d{2})_([1-5])$")
    if parts.isna().any().any():
        raise ValueError(f"Invalid OULU video ID in {path}")
    parts = parts.astype(int)
    actual = set(parts.itertuples(index=False, name=None))
    if actual != expected_ids(1, None, split):
        raise ValueError(f"Unexpected Protocol 1 {split} membership")
    if not frame.label.eq(parts[3].eq(1).astype(int)).all():
        raise ValueError(f"Labels conflict with OULU access types in {path}")
    frame[["phone", "session", "subject", "access"]] = parts.to_numpy()
    return frame


def describe_groups(frame, threshold, column):
    groups = []
    for value, group in frame.groupby(column, sort=True):
        live = group.label.eq(1)
        accepted = group.score.gt(threshold)
        live_total, attack_total = int(live.sum()), int((~live).sum())
        rejected_live = int((live & ~accepted).sum())
        accepted_attack = int((~live & accepted).sum())
        bpcer = rejected_live / live_total if live_total else None
        apcer = accepted_attack / attack_total if attack_total else None
        groups.append({column: int(value), "videos": len(group), "live_total": live_total,
                       "attack_total": attack_total, "live_rejected": rejected_live,
                       "attack_accepted": accepted_attack, "bpcer": bpcer, "apcer_pooled": apcer,
                       "acer_pooled": (bpcer + apcer) / 2 if live_total and attack_total else None})
    return groups


def audit(source, output):
    report = json.loads((source / "pilot_result.json").read_text(encoding="utf-8"))
    metrics = json.loads((source / "test_metrics.json").read_text(encoding="utf-8"))
    lock = json.loads((source / "test_lock.json").read_text(encoding="utf-8"))
    if any(metrics.get(key) != value for key, value in lock.items()):
        raise ValueError("Test metrics differ from the frozen lock")
    if (file_sha(source / "pilot_result.json") != lock["dev_report_sha256"]
            or file_sha(source / "test_scores.csv") != metrics["test_scores_sha256"]):
        raise ValueError("Saved source hash differs from the frozen result")
    if (metrics["split"] != "Test" or metrics["protocol"] != 1 or metrics["videos"] != 600
            or metrics["frames_per_video"] != 8 or report["mode"] != "full"
            or report["train_videos"] != 1200 or report["dev_videos"] != 900
            or report["dev_frames_per_video"] != 8
            or [row["epoch"] for row in report["history"]] != list(range(1, lock["epoch"] + 1))):
        raise ValueError("Unexpected full Protocol 1 run configuration")
    for key in ("checkpoint_sha256", "assets_manifest_sha256", "seed", "batch"):
        if report[key] != lock[key]:
            raise ValueError(f"Train/Dev and Test differ in {key}")

    dev = checked_scores(source / "dev_scores.csv", "val")
    test = checked_scores(source / "test_scores.csv", "test")
    threshold = lock["threshold_from_dev"]
    evaluated = score(dev, test)
    if (evaluated["threshold_from_dev"] != threshold or report["dev"]["threshold_from_dev"] != threshold
            or evaluated["test"] != metrics["test"]
            or any(report["dev"].get(key) != value for key, value in evaluated["dev"].items())):
        raise ValueError("Recalculated scores disagree with the saved threshold or metrics")

    accepted = test.score.gt(threshold)
    errors = test.loc[accepted.ne(test.label.eq(1))].copy()
    errors["error"] = errors.label.map({1: "bona_fide_rejected", 0: "attack_accepted"})
    errors["threshold_from_dev"] = threshold
    analysis = {
        "status": "verified", "training_run": lock["training_run"], "epoch": lock["epoch"],
        "seed": lock["seed"], "threshold_from_dev": threshold,
        "dev": evaluated["dev"], "test": evaluated["test"],
        "dev_auc": float(roc_auc_score(dev.label, dev.score)),
        "test_auc": float(roc_auc_score(test.label, test.score)),
        "by_phone": describe_groups(test, threshold, "phone"),
        "by_access": describe_groups(test, threshold, "access"),
        "by_subject": describe_groups(test, threshold, "subject"),
        "source_sha256": {path.name: file_sha(path) for path in sorted(source.iterdir()) if path.is_file()},
    }
    output.mkdir(parents=True, exist_ok=True)
    errors.to_csv(output / "test_errors.csv", index=False)
    for key in ("by_phone", "by_access", "by_subject"):
        pd.DataFrame(analysis[key]).to_csv(output / f"{key}.csv", index=False)
    (output / "audit.json").write_text(json.dumps(analysis, indent=2) + "\n", encoding="utf-8")
    return analysis


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.source, args.output)
    print(json.dumps({key: result[key] for key in ("status", "threshold_from_dev", "dev", "test", "test_auc")}, indent=2))
