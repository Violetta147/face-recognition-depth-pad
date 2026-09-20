import json
from pathlib import Path

import numpy as np
import pandas as pd

from deepface_pad.data import MANIFEST_COLUMNS, manifest_checksum
import pytest

from deepface_pad.data import validate_manifest
from deepface_pad.depth_jobs import (
    depth_provenance_path,
    materialize_depth_manifest,
    prepare_depth_jobs,
    process_pending_depth_jobs,
    verify_depth_manifest_provenance,
)


def _write_manifest(path: Path) -> None:
    rows = [
        ["live", "train", "1", "v1", 0, "live.jpg", "", 1, "live"],
        ["print", "train", "2", "v2", 0, "print.jpg", "", 0, "print"],
    ]
    pd.DataFrame(rows, columns=MANIFEST_COLUMNS).to_csv(path, index=False)


def test_depth_jobs_create_zero_target_pending_list_and_ledger(tmp_path: Path):
    manifest = tmp_path / "manifest.csv"
    output = tmp_path / "depth"
    _write_manifest(manifest)

    counts = prepare_depth_jobs(manifest, tmp_path, output)

    assert counts["pending_3ddfa"] == 1
    assert counts["complete_attack_zero"] == 1
    assert np.array_equal(np.load(output / "print.npy"), np.zeros((32, 32), dtype=np.float32))
    pending = pd.read_csv(output / "3ddfa_pending.csv")
    assert pending["sample_id"].tolist() == ["live"]
    ledger = pd.read_csv(output / "depth_status.csv", keep_default_na=False)
    assert dict(zip(ledger.sample_id, ledger.status)) == {
        "live": "pending_3ddfa",
        "print": "complete_attack_zero",
    }


def test_depth_jobs_resume_from_valid_bona_fide_output(tmp_path: Path):
    manifest = tmp_path / "manifest.csv"
    output = tmp_path / "depth"
    _write_manifest(manifest)
    prepare_depth_jobs(manifest, tmp_path, output)
    np.save(output / "live.npy", np.array([[0.0, 0.5], [0.75, 1.0]], dtype=np.float32))

    counts = prepare_depth_jobs(manifest, tmp_path, output)

    assert counts["complete_bona_fide"] == 1
    assert pd.read_csv(output / "3ddfa_pending.csv").empty


def test_failed_bona_fide_is_retained_until_explicit_retry(tmp_path: Path):
    manifest = tmp_path / "manifest.csv"
    output = tmp_path / "depth"
    failures = tmp_path / "failures.csv"
    _write_manifest(manifest)
    pd.DataFrame([{"sample_id": "live", "error": "face fitting failed"}]).to_csv(failures, index=False)

    prepare_depth_jobs(manifest, tmp_path, output, failure_report=failures)
    counts = prepare_depth_jobs(manifest, tmp_path, output)

    assert counts["failed_bona_fide"] == 1
    assert not (output / "live.npy").exists()
    failed = pd.read_csv(output / "depth_status.csv", keep_default_na=False).set_index("sample_id").loc["live"]
    assert failed.status == "failed_bona_fide"
    assert failed.last_error == "face fitting failed"
    assert pd.read_csv(output / "3ddfa_pending.csv").empty

    retried = prepare_depth_jobs(manifest, tmp_path, output, retry_failed=True)
    assert retried["pending_3ddfa"] == 1
    assert pd.read_csv(output / "3ddfa_pending.csv").sample_id.tolist() == ["live"]


def test_invalid_existing_bona_fide_output_requires_explicit_retry(tmp_path: Path):
    manifest = tmp_path / "manifest.csv"
    output = tmp_path / "depth"
    _write_manifest(manifest)
    output.mkdir()
    np.save(output / "live.npy", np.zeros((2, 2), dtype=np.float32))

    failed = prepare_depth_jobs(manifest, tmp_path, output)
    retried = prepare_depth_jobs(manifest, tmp_path, output, retry_failed=True)

    assert failed["failed_bona_fide"] == 1
    assert retried["pending_3ddfa"] == 1
    assert (output / "live.npy").is_file()


def test_pending_worker_normalises_updates_and_resumes(tmp_path: Path):
    manifest = tmp_path / "manifest.csv"
    output = tmp_path / "depth"
    _write_manifest(manifest)
    prepare_depth_jobs(manifest, tmp_path, output)

    calls = []

    def reconstruct(path: Path) -> np.ndarray:
        calls.append(path)
        return np.arange(16, dtype=np.float32).reshape(4, 4)

    summary = process_pending_depth_jobs(
        output / "3ddfa_pending.csv",
        output / "depth_status.csv",
        reconstruct,
    )

    assert summary == {"attempted": 1, "succeeded": 1, "failed": 0, "remaining": 0}
    assert calls == [tmp_path / "live.jpg"]
    saved = np.load(output / "live.npy")
    assert saved.shape == (32, 32)
    assert saved.min() == pytest.approx(0)
    assert saved.max() == pytest.approx(1)
    assert pd.read_csv(output / "3ddfa_pending.csv").empty
    assert process_pending_depth_jobs(
        output / "3ddfa_pending.csv", output / "depth_status.csv", reconstruct
    )["attempted"] == 0


def test_pending_worker_records_failure_without_zero_fallback(tmp_path: Path):
    manifest = tmp_path / "manifest.csv"
    output = tmp_path / "depth"
    failures = tmp_path / "failures.csv"
    _write_manifest(manifest)
    prepare_depth_jobs(manifest, tmp_path, output)

    def reconstruct(_path: Path) -> np.ndarray:
        raise RuntimeError("face fitting failed")

    summary = process_pending_depth_jobs(
        output / "3ddfa_pending.csv",
        output / "depth_status.csv",
        reconstruct,
        failure_report=failures,
    )

    assert summary["failed"] == 1
    assert not (output / "live.npy").exists()
    failed = pd.read_csv(failures, keep_default_na=False).iloc[0]
    assert failed.sample_id == "live"
    assert "face fitting failed" in failed.error


def test_materialize_verified_depth_manifest_without_mutating_source(tmp_path: Path):
    manifest = tmp_path / "manifest.csv"
    output = tmp_path / "depth"
    derived = tmp_path / "manifest-with-depth.csv"
    _write_manifest(manifest)
    (tmp_path / "live.jpg").touch()
    (tmp_path / "print.jpg").touch()
    prepare_depth_jobs(manifest, tmp_path, output)
    np.save(output / "live.npy", np.array([[0.0, 0.5], [0.75, 1.0]], dtype=np.float32))
    prepare_depth_jobs(manifest, tmp_path, output)

    counts = materialize_depth_manifest(manifest, output / "depth_status.csv", tmp_path, derived)

    source_frame = pd.read_csv(manifest, keep_default_na=False)
    derived_frame = pd.read_csv(derived, keep_default_na=False)
    assert source_frame["depth_path"].tolist() == ["", ""]
    assert derived_frame["depth_path"].tolist() == ["depth/live.npy", "depth/print.npy"]
    assert counts == {"rows": 2, "bona_fide": 1, "attack": 1}
    assert validate_manifest(derived, tmp_path, require_depth=True) == []
    sidecar = depth_provenance_path(derived)
    provenance = json.loads(sidecar.read_text(encoding="utf-8"))
    assert provenance["source_manifest"]["sha256"] == manifest_checksum(manifest)
    assert provenance["ledger"]["sha256"] == manifest_checksum(output / "depth_status.csv")
    assert provenance["derived_manifest"]["sha256"] == manifest_checksum(derived)
    assert verify_depth_manifest_provenance(manifest, output / "depth_status.csv", derived) == provenance


@pytest.mark.parametrize("changed", ["source_manifest", "ledger", "derived_manifest"])
def test_depth_provenance_detects_exact_byte_changes(tmp_path: Path, changed: str):
    manifest = tmp_path / "manifest.csv"
    output = tmp_path / "depth"
    derived = tmp_path / "manifest-with-depth.csv"
    _write_manifest(manifest)
    prepare_depth_jobs(manifest, tmp_path, output)
    np.save(output / "live.npy", np.ones((2, 2), dtype=np.float32))
    prepare_depth_jobs(manifest, tmp_path, output)
    materialize_depth_manifest(manifest, output / "depth_status.csv", tmp_path, derived)
    changed_path = {
        "source_manifest": manifest,
        "ledger": output / "depth_status.csv",
        "derived_manifest": derived,
    }[changed]
    changed_path.write_bytes(changed_path.read_bytes() + b"\n")

    with pytest.raises(ValueError, match=rf"{changed}: checksum mismatch"):
        verify_depth_manifest_provenance(manifest, output / "depth_status.csv", derived)


def test_depth_provenance_includes_and_verifies_worker_metadata(tmp_path: Path):
    manifest = tmp_path / "manifest.csv"
    output = tmp_path / "depth"
    derived = tmp_path / "manifest-with-depth.csv"
    _write_manifest(manifest)
    prepare_depth_jobs(manifest, tmp_path, output)
    np.save(output / "live.npy", np.ones((2, 2), dtype=np.float32))
    prepare_depth_jobs(manifest, tmp_path, output)
    worker_metadata = output / "depth_status.csv.worker.json"
    worker_metadata.write_text('{"git_commit": "abc123"}\n', encoding="utf-8")

    materialize_depth_manifest(manifest, output / "depth_status.csv", tmp_path, derived)
    provenance = verify_depth_manifest_provenance(
        manifest, output / "depth_status.csv", derived
    )

    assert provenance["worker_metadata"]["sha256"] == manifest_checksum(worker_metadata)
    worker_metadata.write_text('{"git_commit": "changed"}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="worker_metadata: checksum mismatch"):
        verify_depth_manifest_provenance(manifest, output / "depth_status.csv", derived)


def test_materialize_rejects_incomplete_ledger_without_writing_output(tmp_path: Path):
    manifest = tmp_path / "manifest.csv"
    output = tmp_path / "depth"
    derived = tmp_path / "manifest-with-depth.csv"
    _write_manifest(manifest)
    prepare_depth_jobs(manifest, tmp_path, output)

    with pytest.raises(ValueError, match="pending_3ddfa"):
        materialize_depth_manifest(manifest, output / "depth_status.csv", tmp_path, derived)

    assert not derived.exists()


def test_materialize_rejects_depth_outputs_outside_data_root(tmp_path: Path):
    data_root = tmp_path / "data"
    data_root.mkdir()
    manifest = tmp_path / "manifest.csv"
    output = tmp_path / "external-depth"
    derived = tmp_path / "manifest-with-depth.csv"
    _write_manifest(manifest)
    prepare_depth_jobs(manifest, data_root, output)
    np.save(output / "live.npy", np.ones((2, 2), dtype=np.float32))
    prepare_depth_jobs(manifest, data_root, output)

    with pytest.raises(ValueError, match="outside data root"):
        materialize_depth_manifest(manifest, output / "depth_status.csv", data_root, derived)

    assert not derived.exists()


def test_materialize_rejects_stale_ledger_metadata(tmp_path: Path):
    manifest = tmp_path / "manifest.csv"
    output = tmp_path / "depth"
    derived = tmp_path / "manifest-with-depth.csv"
    _write_manifest(manifest)
    prepare_depth_jobs(manifest, tmp_path, output)
    np.save(output / "live.npy", np.ones((2, 2), dtype=np.float32))
    prepare_depth_jobs(manifest, tmp_path, output)
    changed = pd.read_csv(manifest, keep_default_na=False)
    changed.loc[changed["sample_id"] == "live", "image_path"] = "changed.jpg"
    changed.to_csv(manifest, index=False)

    with pytest.raises(ValueError, match="stale ledger metadata"):
        materialize_depth_manifest(manifest, output / "depth_status.csv", tmp_path, derived)

    assert not derived.exists()
