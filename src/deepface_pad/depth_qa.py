from __future__ import annotations

from collections import defaultdict
from hashlib import sha256
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from PIL import Image


def _load_depth(path: Path) -> np.ndarray:
    if path.suffix.lower() == ".npy":
        return np.asarray(np.load(path, allow_pickle=False))
    return np.asarray(Image.open(path).convert("F"))


def audit_depth_targets(
    manifest: str | Path,
    data_root: str | Path,
    zero_tolerance: float = 1e-6,
    *,
    include_checksums: bool = False,
) -> dict[str, Any]:
    """Audit pseudo-depth targets without loading RGB or training dependencies.

    Bona fide samples must have a readable, finite, non-zero 2-D depth map. Attack
    samples may omit ``depth_path`` (their implicit target is zero); an explicit
    attack target must contain only zeros within ``zero_tolerance``.
    """
    frame = pd.read_csv(manifest, keep_default_na=False)
    required = {"sample_id", "split", "depth_path", "label"}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"manifest is missing columns: {missing}")

    root = Path(data_root)
    issues: list[dict[str, str]] = []
    split_counts: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "samples": 0,
            "bona_fide_samples": 0,
            "attack_samples": 0,
            "bona_fide_failures": 0,
            "bona_fide_failure_rate": 0.0,
        }
    )
    class_values: dict[str, list[np.ndarray]] = {"bona_fide": [], "attack": []}
    failed_bona_fide: dict[str, set[str]] = defaultdict(set)
    explicit_maps = 0
    implicit_attack_zero_maps = 0
    artifact_checksums: list[dict[str, Any]] = []

    def add_issue(row: Any, issue: str, detail: str) -> None:
        issues.append(
            {
                "sample_id": str(row.sample_id),
                "split": str(row.split),
                "issue": issue,
                "detail": detail,
            }
        )
        if int(row.label) == 1:
            failed_bona_fide[str(row.split)].add(str(row.sample_id))

    for row in frame.itertuples(index=False):
        split = str(row.split)
        label = int(row.label)
        split_counts[split]["samples"] += 1
        class_key = "bona_fide" if label == 1 else "attack"
        split_counts[split][f"{class_key}_samples"] += 1

        depth_path = str(row.depth_path)
        if not depth_path:
            if label == 1:
                add_issue(row, "missing_bona_fide_depth", "depth_path is empty")
            else:
                implicit_attack_zero_maps += 1
            continue

        target = root / depth_path
        if not target.is_file():
            add_issue(row, "missing_depth_file", depth_path)
            continue

        try:
            depth = _load_depth(target)
        except Exception as exc:  # Corrupt or unsupported files belong in the QA report.
            add_issue(row, "unreadable_depth", f"{depth_path}: {exc}")
            continue

        explicit_maps += 1
        if depth.ndim != 2 or depth.size == 0:
            add_issue(row, "invalid_depth_shape", str(tuple(depth.shape)))
            continue
        if not np.isfinite(depth).all():
            add_issue(row, "non_finite_depth", depth_path)
            continue

        values = depth.astype(np.float64, copy=False).reshape(-1)
        if include_checksums:
            artifact_checksums.append(
                {
                    "sample_id": str(row.sample_id),
                    "split": split,
                    "label": label,
                    "depth_path": depth_path,
                    "size_bytes": target.stat().st_size,
                    "sha256": sha256(target.read_bytes()).hexdigest(),
                }
            )
        class_values[class_key].append(values)
        if label == 1 and float(np.max(np.abs(values))) <= zero_tolerance:
            add_issue(row, "empty_bona_fide_depth", depth_path)
        if label == 0 and np.any(np.abs(values) > zero_tolerance):
            add_issue(row, "nonzero_attack_depth", depth_path)

    for split, counts in split_counts.items():
        failures = len(failed_bona_fide[split])
        counts["bona_fide_failures"] = failures
        total = counts["bona_fide_samples"]
        counts["bona_fide_failure_rate"] = failures / total if total else 0.0

    def summarize(arrays: list[np.ndarray]) -> dict[str, float | int | None]:
        if not arrays:
            return {"map_count": 0, "pixel_count": 0, "min": None, "max": None, "mean": None}
        values = np.concatenate(arrays)
        return {
            "map_count": len(arrays),
            "pixel_count": int(values.size),
            "min": float(values.min()),
            "max": float(values.max()),
            "mean": float(values.mean()),
        }

    report = {
        "valid": not issues,
        "manifest": str(Path(manifest)),
        "samples": int(len(frame)),
        "explicit_maps_checked": explicit_maps,
        "implicit_attack_zero_maps": implicit_attack_zero_maps,
        "by_split": dict(sorted(split_counts.items())),
        "depth_statistics": {key: summarize(values) for key, values in class_values.items()},
        "issues": issues,
    }
    if include_checksums:
        report["artifact_checksums"] = artifact_checksums
    return report
