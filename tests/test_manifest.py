from pathlib import Path

import pandas as pd

from deepface_pad.data import MANIFEST_COLUMNS, depth_supervision_required, validate_manifest


def test_video_leakage_is_rejected(tmp_path: Path):
    rows = [
        ["a", "train", "1", "video", 0, "a.jpg", "", 1, "live"],
        ["b", "test", "1", "video", 1, "b.jpg", "", 1, "live"],
    ]
    path = tmp_path / "manifest.csv"
    pd.DataFrame(rows, columns=MANIFEST_COLUMNS).to_csv(path, index=False)
    errors = validate_manifest(path, tmp_path, check_files=False)
    assert any("video leakage" in error for error in errors)


def test_depth_supervision_rejects_missing_bona_fide_target(tmp_path: Path):
    rows = [
        ["live", "train", "1", "live-video", 0, "live.jpg", "", 1, "live"],
        ["spoof", "train", "2", "spoof-video", 0, "spoof.jpg", "", 0, "print"],
    ]
    path = tmp_path / "manifest.csv"
    pd.DataFrame(rows, columns=MANIFEST_COLUMNS).to_csv(path, index=False)

    errors = validate_manifest(path, tmp_path, check_files=False, require_depth=True)

    assert errors == ["missing bona fide depth_path: ['live']"]


def test_only_depth_consuming_configs_require_targets():
    assert depth_supervision_required({"model": {"name": "cdcn"}})
    assert depth_supervision_required(
        {
            "model": {"name": "cdcn_mt_lite"},
            "training": {"stages": [{"name": "joint"}]},
            "loss": {"lambda_abs": 1.0, "lambda_contrast": 0.5},
        }
    )
    assert not depth_supervision_required({"model": {"name": "mobilenet_v3_small"}})
    assert not depth_supervision_required(
        {
            "model": {"name": "cdcn_mt_lite"},
            "training": {"stages": [{"name": "head"}]},
            "loss": {"lambda_abs": 0.0, "lambda_contrast": 0.0},
        }
    )
