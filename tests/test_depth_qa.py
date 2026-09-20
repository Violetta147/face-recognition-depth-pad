from pathlib import Path

import numpy as np
import pandas as pd

from deepface_pad.data import MANIFEST_COLUMNS
from deepface_pad.depth_qa import audit_depth_targets


def _write_manifest(path: Path, rows: list[list[object]]) -> None:
    pd.DataFrame(rows, columns=MANIFEST_COLUMNS).to_csv(path, index=False)


def test_depth_audit_accepts_live_maps_and_zero_attack_targets(tmp_path: Path):
    np.save(tmp_path / "live.npy", np.array([[0.0, 0.25], [0.5, 1.0]], dtype=np.float32))
    np.save(tmp_path / "attack.npy", np.zeros((2, 2), dtype=np.float32))
    manifest = tmp_path / "manifest.csv"
    _write_manifest(
        manifest,
        [
            ["live", "train", "1", "v1", 0, "live.jpg", "live.npy", 1, "live"],
            ["print", "train", "2", "v2", 0, "print.jpg", "attack.npy", 0, "print"],
            ["replay", "val", "3", "v3", 0, "replay.jpg", "", 0, "replay"],
        ],
    )

    report = audit_depth_targets(manifest, tmp_path)

    assert report["valid"]
    assert report["issues"] == []
    assert report["implicit_attack_zero_maps"] == 1
    assert report["by_split"]["train"]["bona_fide_failure_rate"] == 0.0
    assert report["depth_statistics"]["bona_fide"]["max"] == 1.0
    assert report["depth_statistics"]["attack"]["mean"] == 0.0


def test_depth_audit_reports_invalid_targets_and_split_failure_rate(tmp_path: Path):
    np.save(tmp_path / "empty.npy", np.zeros((2, 2), dtype=np.float32))
    np.save(tmp_path / "nan.npy", np.array([[0.0, np.nan]], dtype=np.float32))
    np.save(tmp_path / "spoof.npy", np.array([[0.0, 0.1]], dtype=np.float32))
    manifest = tmp_path / "manifest.csv"
    _write_manifest(
        manifest,
        [
            ["missing", "train", "1", "v1", 0, "a.jpg", "", 1, "live"],
            ["empty", "train", "2", "v2", 0, "b.jpg", "empty.npy", 1, "live"],
            ["nan", "val", "3", "v3", 0, "c.jpg", "nan.npy", 1, "live"],
            ["spoof", "val", "4", "v4", 0, "d.jpg", "spoof.npy", 0, "print"],
        ],
    )

    report = audit_depth_targets(manifest, tmp_path)

    assert not report["valid"]
    assert {issue["issue"] for issue in report["issues"]} == {
        "missing_bona_fide_depth",
        "empty_bona_fide_depth",
        "non_finite_depth",
        "nonzero_attack_depth",
    }
    assert report["by_split"]["train"]["bona_fide_failure_rate"] == 1.0
    assert report["by_split"]["val"]["bona_fide_failure_rate"] == 1.0
