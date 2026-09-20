from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from deepface_pad.data import MANIFEST_COLUMNS
from deepface_pad.depth_jobs import materialize_depth_manifest, prepare_depth_jobs
from deepface_pad.preflight import inspect_training_inputs, validate_training_inputs


def _write_source_manifest(path: Path) -> None:
    rows = [
        ["live", "train", "1", "v1", 0, "live.jpg", "", 1, "live"],
        ["attack", "val", "2", "v2", 0, "attack.jpg", "", 0, "print"],
    ]
    pd.DataFrame(rows, columns=MANIFEST_COLUMNS).to_csv(path, index=False)


def _depth_config(source: Path, ledger: Path, derived: Path, root: Path) -> dict:
    return {
        "model": {"name": "cdcn"},
        "data": {
            "manifest": str(derived),
            "source_manifest": str(source),
            "depth_ledger": str(ledger),
            "root": str(root),
        },
    }


def _materialized_inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    source = tmp_path / "all.csv"
    depth_root = tmp_path / "depth"
    derived = tmp_path / "all-with-depth.csv"
    _write_source_manifest(source)
    (tmp_path / "live.jpg").touch()
    (tmp_path / "attack.jpg").touch()
    prepare_depth_jobs(source, tmp_path, depth_root)
    np.save(depth_root / "live.npy", np.ones((2, 2), dtype=np.float32))
    prepare_depth_jobs(source, tmp_path, depth_root)
    ledger = depth_root / "depth_status.csv"
    materialize_depth_manifest(source, ledger, tmp_path, derived)
    return source, ledger, derived


def test_depth_training_preflight_requires_and_verifies_provenance(tmp_path: Path):
    source, ledger, derived = _materialized_inputs(tmp_path)

    assert validate_training_inputs(_depth_config(source, ledger, derived, tmp_path))


def test_depth_training_preflight_captures_reproducible_input_snapshot(tmp_path: Path):
    source, ledger, derived = _materialized_inputs(tmp_path)

    require_depth, snapshot = inspect_training_inputs(
        _depth_config(source, ledger, derived, tmp_path)
    )

    assert require_depth
    assert snapshot is not None
    assert snapshot["schema_version"] == 1
    assert snapshot["files"]["source_manifest"]["sha256"]
    checksums = snapshot["depth_audit"]["artifact_checksums"]
    assert [entry["sample_id"] for entry in checksums] == ["live", "attack"]
    assert all(len(entry["sha256"]) == 64 for entry in checksums)
    assert snapshot["depth_audit"]["valid"]


def test_depth_training_preflight_rejects_missing_provenance_config(tmp_path: Path):
    source, ledger, derived = _materialized_inputs(tmp_path)
    config = _depth_config(source, ledger, derived, tmp_path)
    del config["data"]["source_manifest"]

    with pytest.raises(ValueError, match="missing data config keys: source_manifest"):
        validate_training_inputs(config)


def test_depth_training_preflight_rejects_changed_source_bytes(tmp_path: Path):
    source, ledger, derived = _materialized_inputs(tmp_path)
    source.write_bytes(source.read_bytes() + b"\n")

    with pytest.raises(ValueError, match="source_manifest: checksum mismatch"):
        validate_training_inputs(_depth_config(source, ledger, derived, tmp_path))


def test_depth_training_preflight_rejects_depth_changed_after_materialization(tmp_path: Path):
    source, ledger, derived = _materialized_inputs(tmp_path)
    np.save(tmp_path / "depth" / "live.npy", np.zeros((2, 2), dtype=np.float32))

    with pytest.raises(
        ValueError,
        match=r"depth content preflight failed:\n- live \(train\): "
        r"empty_bona_fide_depth",
    ):
        validate_training_inputs(_depth_config(source, ledger, derived, tmp_path))


def test_depth_training_preflight_rejects_nonzero_attack_map(tmp_path: Path):
    source, ledger, derived = _materialized_inputs(tmp_path)
    np.save(tmp_path / "depth" / "attack.npy", np.ones((2, 2), dtype=np.float32))

    with pytest.raises(ValueError, match="nonzero_attack_depth"):
        validate_training_inputs(_depth_config(source, ledger, derived, tmp_path))


def test_non_depth_training_does_not_require_provenance(tmp_path: Path):
    source = tmp_path / "all.csv"
    _write_source_manifest(source)
    (tmp_path / "live.jpg").touch()
    (tmp_path / "attack.jpg").touch()
    config = {
        "model": {"name": "mobilenet_v3_small"},
        "data": {"manifest": str(source), "root": str(tmp_path)},
    }

    assert not validate_training_inputs(config)
    assert inspect_training_inputs(config) == (False, None)
