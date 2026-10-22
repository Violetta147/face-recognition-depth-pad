"""Verified inputs and deterministic case selection for the frozen E0–E4 figures."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tarfile
import zipfile

import numpy as np
import pandas as pd
import yaml

from .metrics import aggregate_video_scores, evaluate_scores

MANIFEST_SHA = "4c302c9039e48a8ea6baedf426b26e1b0a6663bc295c661bb71fefccdb9b37fd"
DEPTH_TAR_SHA = "26cfa7f26d61e3a71372404008f5dc9dd696af931172850986a8642e440b3d80"
MODELS = ("E0", "E1", "E2", "E3", "E3b", "E4")
DEPTH_MODELS = MODELS[1:]


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_csv(path):
    return pd.read_csv(path, keep_default_na=False, float_precision="round_trip")


def verify_scores(frame, video, expected, threshold, metrics):
    columns = ["sample_id", "video_id", "label"]
    pd.testing.assert_frame_equal(frame[columns].sort_values("sample_id").reset_index(drop=True),
                                  expected[columns].sort_values("sample_id").reset_index(drop=True))
    if not np.isfinite(frame.score).all():
        raise ValueError("non-finite saved frame score")
    pd.testing.assert_frame_equal(aggregate_video_scores(frame),
                                  video.sort_values("video_id").reset_index(drop=True), atol=1e-12, rtol=0)
    computed = evaluate_scores(video.label.to_numpy(), video.score.to_numpy(), threshold=threshold).to_dict()
    if any(abs(computed[key] - metrics[key]) > 1e-12 for key in computed):
        raise ValueError("saved metrics do not match frozen scores/threshold")
    return computed


def load_evidence(project_root, runs_dir, manifest_path, freeze_path):
    """Fail on changed artifacts; never alter a run or retune its threshold."""
    root, runs_dir = Path(project_root), Path(runs_dir)
    if sha256(manifest_path) != MANIFEST_SHA:
        raise ValueError("manifest differs from the frozen CASIA manifest")
    manifest = read_csv(manifest_path)
    audit = read_json(root / "reports/ROUND_5_TEST_RESULTS_2026-10-16.json")
    validation = read_json(root / "reports/ROUND_5_FULL_VALIDATION_2026-10-16.json")
    baseline = read_json(root / "reports/RESEARCH_AUDIT_ROUNDS_1_4_2026-10-16.json")
    freeze = read_json(freeze_path)
    if freeze["selected_variant"] != "E3" or freeze["selection_source"] != "validation":
        raise ValueError("unexpected pre-test selection")
    source_files, runs = {}, {}
    for name in MODELS:
        record = audit["runs"][name]
        folder = runs_dir / record["run_id"]
        cfg = yaml.safe_load((folder / "config.yaml").read_text(encoding="utf-8"))
        if cfg["seed"] != 42:
            raise ValueError("figures expect the audited seed-42 runs")
        for filename, digest in record["test_artifact_hashes"].items():
            if sha256(folder / filename) != digest:
                raise ValueError(f"changed test artifact: {name}/{filename}")
        if name in freeze["runs"]:
            if freeze["runs"][name]["hashes"] != validation["runs"][name]["hashes"]:
                raise ValueError("freeze differs from pre-test audit")
            expected_checkpoint = freeze["runs"][name]["hashes"]["best.ckpt"]
            for filename, digest in freeze["runs"][name]["hashes"].items():
                if sha256(folder / filename) != digest:
                    raise ValueError(f"changed frozen artifact: {name}/{filename}")
        else:
            old = next(row for row in baseline["runs"] if row["run_id"] == record["run_id"])
            expected_checkpoint = old["checkpoint"]["sha256"]
        if sha256(folder / "best.ckpt") != expected_checkpoint:
            raise ValueError(f"changed checkpoint: {name}")
        threshold = read_json(folder / "threshold.json")
        if threshold["source"] != "validation":
            raise ValueError("threshold must come from validation")
        item = {"folder":folder, "config":cfg, "threshold":threshold["threshold"],
                "log":read_csv(folder / "train_log.csv"), "checkpoint_sha256":expected_checkpoint}
        for split, filename in (("val", "metrics.json"), ("test", "test_metrics.json")):
            frame = read_csv(folder / f"{split}_frame_scores.csv")
            video = read_csv(folder / f"{split}_scores.csv")
            metrics = read_json(folder / filename)
            item[f"{split}_metrics"] = verify_scores(frame, video, manifest[manifest.split == split],
                                                      threshold["threshold"], metrics)
            item[f"{split}_frame"] = frame
            item[f"{split}_video"] = video.assign(prediction=(video.score >= threshold["threshold"]).astype(int))
        item["log"] = item["log"].assign(global_epoch=np.arange(1, len(item["log"])+1))
        runs[name] = item
        for filename in ("config.yaml", "best.ckpt", "threshold.json", "train_log.csv",
                         "metrics.json", "test_metrics.json", "val_scores.csv", "test_scores.csv",
                         "val_frame_scores.csv", "test_frame_scores.csv"):
            source_files[str(folder / filename)] = sha256(folder / filename)
    return {"manifest":manifest, "runs":runs, "audit":audit, "freeze":freeze,
            "source_files":source_files, "manifest_sha256":MANIFEST_SHA}


def choose_cases(evidence):
    """One middle temporal frame/video, chosen by explicit outcome categories."""
    manifest, runs = evidence["manifest"], evidence["runs"]
    merged = runs["E1"]["test_video"][["video_id", "label", "prediction"]].rename(columns={"prediction":"p1"})
    for name, suffix in (("E3","p3"),("E3b","p3b"),("E4","p4")):
        merged = merged.merge(runs[name]["test_video"][["video_id","prediction"]].rename(columns={"prediction":suffix}), on="video_id", validate="one_to_one")
    categories = [
        ("live_common_correct", (merged.label == 1) & (merged.p1 == 1) & (merged.p3 == 1) & (merged.p4 == 1)),
        ("live_common_error", (merged.label == 1) & (merged.p1 == 0) & (merged.p3 == 0) & (merged.p4 == 0)),
        ("E3_fixes_E1", (merged.p1 != merged.label) & (merged.p3 == merged.label)),
        ("E3_new_error", (merged.p1 == merged.label) & (merged.p3 != merged.label)),
        ("Focal_fixes_staged_BCE", (merged.p3b != merged.label) & (merged.p4 == merged.label)),
    ]
    selected = {}
    for role, mask in categories:
        candidates = sorted(merged.loc[mask,"video_id"])
        if candidates:
            selected.setdefault(candidates[0], []).append(role)
    attacks = manifest[(manifest.split == "test") & (manifest.label == 0)]
    for attack_type, group in attacks.groupby("attack_type", sort=True):
        video_id = sorted(group.video_id.unique())[0]
        selected.setdefault(video_id, []).append(f"attack_{attack_type}")
    result = []
    for video_id, roles in selected.items():
        frames = manifest[(manifest.split == "test") & (manifest.video_id == video_id)].sort_values("frame_index")
        row = frames.iloc[len(frames)//2].to_dict()
        row["role"] = "; ".join(roles)
        result.append(row)
    return pd.DataFrame(result)


def safe_destination(root, relative):
    root = Path(root).resolve()
    destination = (root / str(relative)).resolve()
    if not destination.is_relative_to(root):
        raise ValueError("input path escapes data root")
    return destination


def restore_selected_inputs(rows, data_root, dataset_zip, depth_tar, depth_checksums):
    """Restore only requested RGB/targets; never regenerate 3DDFA or overwrite data."""
    root = Path(data_root)
    required = rows.drop_duplicates("sample_id")
    missing_rgb = [row for row in required.itertuples() if not safe_destination(root,row.image_path).is_file()]
    if missing_rgb:
        with zipfile.ZipFile(dataset_zip) as archive:
            names = set(archive.namelist())
            for row in missing_rgb:
                member = f"casia-fasd/{row.image_path}"
                if member not in names:
                    raise ValueError(f"RGB missing from frozen ZIP: {member}")
                target = safe_destination(root,row.image_path)
                target.parent.mkdir(parents=True,exist_ok=True)
                with target.open("xb") as stream:
                    stream.write(archive.read(member))
    missing_live = [row for row in required.itertuples() if int(row.label) == 1 and not safe_destination(root,row.depth_path).is_file()]
    if missing_live:
        if sha256(depth_tar) != DEPTH_TAR_SHA:
            raise ValueError("depth archive changed")
        with tarfile.open(depth_tar) as archive:
            for row in missing_live:
                target = safe_destination(root,row.depth_path)
                target.parent.mkdir(parents=True,exist_ok=True)
                member = archive.extractfile(str(row.depth_path).replace("\\", "/"))
                if member is None:
                    raise ValueError(f"depth missing from TAR: {row.depth_path}")
                with target.open("xb") as stream:
                    stream.write(member.read())
    for row in required.itertuples():
        target = safe_destination(root,row.depth_path)
        if not target.is_file():
            if int(row.label) != 0:
                raise ValueError("missing live pseudo-depth")
            target.parent.mkdir(parents=True,exist_ok=True)
            with target.open("xb") as stream:
                np.save(stream,np.zeros((32,32),dtype=np.float32))
        if sha256(target) != depth_checksums[str(row.sample_id)]:
            raise ValueError(f"depth differs from E1 snapshot: {row.sample_id}")
    return {str(row.sample_id):{"rgb_sha256":sha256(safe_destination(root,row.image_path)),
                                "depth_sha256":depth_checksums[str(row.sample_id)]}
            for row in required.itertuples()}
