from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd
from PIL import Image

from .data import manifest_checksum
from .depth_qa import _load_depth


LEDGER_COLUMNS = [
    "sample_id",
    "split",
    "label",
    "image_path",
    "output_path",
    "status",
    "last_error",
]
VALID_STATUSES = {
    "pending_3ddfa",
    "complete_bona_fide",
    "complete_attack_zero",
    "failed_bona_fide",
    "failed_attack_target",
}
COMPLETE_STATUS_BY_LABEL = {
    0: "complete_attack_zero",
    1: "complete_bona_fide",
}
PROVENANCE_SCHEMA_VERSION = 1


def _valid_depth(path: Path, *, require_nonzero: bool, zero_tolerance: float) -> tuple[bool, str]:
    try:
        depth = _load_depth(path)
    except Exception as exc:
        return False, f"unreadable output: {exc}"
    if depth.ndim != 2 or depth.size == 0:
        return False, f"invalid output shape: {tuple(depth.shape)}"
    if not np.isfinite(depth).all():
        return False, "output contains NaN or infinity"
    maximum = float(np.max(np.abs(depth)))
    if require_nonzero and maximum <= zero_tolerance:
        return False, "bona fide output is all zero"
    if not require_nonzero and maximum > zero_tolerance:
        return False, "attack output is not zero"
    return True, ""


def _read_previous_ledger(path: Path) -> dict[str, dict[str, Any]]:
    if not path.is_file():
        return {}
    frame = pd.read_csv(path, keep_default_na=False, dtype={"sample_id": str})
    missing = sorted(set(LEDGER_COLUMNS).difference(frame.columns))
    if missing:
        raise ValueError(f"status ledger is missing columns: {missing}")
    if frame["sample_id"].duplicated().any():
        raise ValueError("status ledger contains duplicate sample_id")
    unknown = sorted(set(frame["status"]).difference(VALID_STATUSES))
    if unknown:
        raise ValueError(f"status ledger contains unknown statuses: {unknown}")
    return {str(row.sample_id): row._asdict() for row in frame.itertuples(index=False)}


def _read_failures(path: str | Path | None) -> dict[str, str]:
    if path is None:
        return {}
    frame = pd.read_csv(path, keep_default_na=False, dtype={"sample_id": str})
    missing = sorted({"sample_id", "error"}.difference(frame.columns))
    if missing:
        raise ValueError(f"failure report is missing columns: {missing}")
    if frame["sample_id"].duplicated().any():
        raise ValueError("failure report contains duplicate sample_id")
    return {str(row.sample_id): str(row.error) for row in frame.itertuples(index=False)}


def _write_csv_atomic(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    frame.to_csv(temporary, index=False)
    temporary.replace(path)


def _write_json_atomic(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def depth_provenance_path(derived_manifest: str | Path) -> Path:
    path = Path(derived_manifest)
    return path.with_suffix(path.suffix + ".provenance.json")


def verify_depth_manifest_provenance(
    manifest: str | Path,
    ledger_path: str | Path,
    derived_manifest: str | Path,
    *,
    provenance_path: str | Path | None = None,
) -> dict[str, Any]:
    """Verify that current files exactly match a materialization provenance record."""
    paths = {
        "source_manifest": Path(manifest),
        "ledger": Path(ledger_path),
        "derived_manifest": Path(derived_manifest),
    }
    sidecar = Path(provenance_path) if provenance_path is not None else depth_provenance_path(derived_manifest)
    try:
        payload = json.loads(sidecar.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read provenance sidecar {sidecar}: {exc}") from exc
    if payload.get("schema_version") != PROVENANCE_SCHEMA_VERSION:
        raise ValueError(f"unsupported provenance schema_version: {payload.get('schema_version')}")
    if payload.get("hash_algorithm") != "sha256":
        raise ValueError(f"unsupported provenance hash_algorithm: {payload.get('hash_algorithm')}")

    worker_record = payload.get("worker_metadata")
    if worker_record is not None:
        worker_file = worker_record.get("file") if isinstance(worker_record, dict) else None
        if not isinstance(worker_file, str) or not worker_file:
            raise ValueError("worker_metadata is missing its file name")
        paths["worker_metadata"] = Path(ledger_path).with_name(worker_file)

    mismatches: list[str] = []
    for key, path in paths.items():
        expected = payload.get(key, {}).get("sha256")
        if not isinstance(expected, str):
            mismatches.append(f"{key}: missing recorded sha256")
            continue
        if not path.is_file():
            mismatches.append(f"{key}: file is missing: {path}")
            continue
        actual = manifest_checksum(path)
        if actual != expected:
            mismatches.append(f"{key}: checksum mismatch (expected {expected}, got {actual})")
    if mismatches:
        raise ValueError("depth manifest provenance verification failed:\n- " + "\n- ".join(mismatches))
    return payload


def prepare_depth_jobs(
    manifest: str | Path,
    data_root: str | Path,
    output_root: str | Path,
    *,
    ledger_path: str | Path | None = None,
    failure_report: str | Path | None = None,
    retry_failed: bool = False,
    zero_tolerance: float = 1e-6,
) -> dict[str, int]:
    """Prepare a resumable pseudo-depth work list and status ledger.

    Existing valid outputs are reused. A reported or detected bona fide failure is
    retained in the ledger and is never replaced with a zero map. ``retry_failed``
    explicitly moves failed bona fide rows back to the pending work list.
    """
    manifest_frame = pd.read_csv(manifest, keep_default_na=False, dtype={"sample_id": str})
    required = {"sample_id", "split", "image_path", "label"}
    missing = sorted(required.difference(manifest_frame.columns))
    if missing:
        raise ValueError(f"manifest is missing columns: {missing}")
    if manifest_frame["sample_id"].duplicated().any():
        raise ValueError("manifest contains duplicate sample_id")
    if not manifest_frame["label"].isin([0, 1]).all():
        raise ValueError("manifest labels must be 0 or 1")

    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    ledger_path = Path(ledger_path) if ledger_path is not None else output_root / "depth_status.csv"
    pending_path = output_root / "3ddfa_pending.csv"
    previous = _read_previous_ledger(ledger_path)
    failures = _read_failures(failure_report)
    manifest_ids = set(manifest_frame["sample_id"].astype(str))
    unknown_failures = sorted(set(failures).difference(manifest_ids))
    if unknown_failures:
        raise ValueError(f"failure report contains sample_id not in manifest: {unknown_failures[:10]}")
    labels = dict(zip(manifest_frame["sample_id"].astype(str), manifest_frame["label"].astype(int)))
    attack_failures = sorted(sample_id for sample_id in failures if labels[sample_id] == 0)
    if attack_failures:
        raise ValueError(f"failure report contains attack sample_id: {attack_failures[:10]}")

    ledger_rows: list[dict[str, Any]] = []
    pending_rows: list[dict[str, str]] = []
    for row in manifest_frame.itertuples(index=False):
        sample_id = str(row.sample_id)
        label = int(row.label)
        destination = output_root / f"{sample_id}.npy"
        try:
            destination.resolve().relative_to(output_root.resolve())
        except ValueError as exc:
            raise ValueError(f"sample_id escapes output root: {sample_id}") from exc
        destination.parent.mkdir(parents=True, exist_ok=True)
        prior = previous.get(sample_id, {})
        status: str
        error = ""

        if label == 0:
            if not destination.exists():
                np.save(destination, np.zeros((32, 32), dtype=np.float32))
            valid, error = _valid_depth(destination, require_nonzero=False, zero_tolerance=zero_tolerance)
            status = "complete_attack_zero" if valid else "failed_attack_target"
        else:
            if destination.is_file():
                valid, error = _valid_depth(destination, require_nonzero=True, zero_tolerance=zero_tolerance)
                status = "complete_bona_fide" if valid else "failed_bona_fide"
                if not valid and retry_failed:
                    status = "pending_3ddfa"
                    pending_rows.append(
                        {
                            "sample_id": sample_id,
                            "image_path": str(Path(data_root) / str(row.image_path)),
                            "output_path": str(destination),
                        }
                    )
            elif sample_id in failures:
                status = "failed_bona_fide"
                error = failures[sample_id] or "3DDFA reconstruction failed without an error message"
            elif prior.get("status") == "failed_bona_fide" and not retry_failed:
                status = "failed_bona_fide"
                error = str(prior.get("last_error", ""))
            else:
                status = "pending_3ddfa"
                pending_rows.append(
                    {
                        "sample_id": sample_id,
                        "image_path": str(Path(data_root) / str(row.image_path)),
                        "output_path": str(destination),
                    }
                )

        ledger_rows.append(
            {
                "sample_id": sample_id,
                "split": str(row.split),
                "label": label,
                "image_path": str(Path(data_root) / str(row.image_path)),
                "output_path": str(destination),
                "status": status,
                "last_error": error,
            }
        )

    ledger = pd.DataFrame(ledger_rows, columns=LEDGER_COLUMNS)
    pending = pd.DataFrame(pending_rows, columns=["sample_id", "image_path", "output_path"])
    _write_csv_atomic(ledger, ledger_path)
    _write_csv_atomic(pending, pending_path)
    return {status: int((ledger["status"] == status).sum()) for status in sorted(VALID_STATUSES)}


def _normalise_bona_fide_depth(depth: np.ndarray, output_size: int) -> np.ndarray:
    depth = np.asarray(depth, dtype=np.float32)
    if depth.ndim != 2 or depth.size == 0:
        raise ValueError(f"3DDFA returned invalid depth shape: {tuple(depth.shape)}")
    if not np.isfinite(depth).all():
        raise ValueError("3DDFA returned NaN or infinity")
    minimum = float(depth.min())
    maximum = float(depth.max())
    if maximum - minimum <= 1e-8:
        raise ValueError("3DDFA returned a constant depth map")
    depth = (depth - minimum) / (maximum - minimum)
    if depth.shape != (output_size, output_size):
        depth = np.asarray(
            Image.fromarray(depth, mode="F").resize(
                (output_size, output_size),
                resample=Image.Resampling.BILINEAR,
            ),
            dtype=np.float32,
        )
    return depth


def process_pending_depth_jobs(
    pending_path: str | Path,
    ledger_path: str | Path,
    reconstruct: Callable[[Path], np.ndarray],
    *,
    failure_report: str | Path | None = None,
    output_size: int = 32,
    limit: int | None = None,
) -> dict[str, int]:
    """Run a reconstruction callback and atomically update the depth ledger.

    The callback isolates the queue/provenance logic from the external 3DDFA V2
    checkout.  State is saved after every sample so a Colab disconnect can be
    resumed without repeating completed reconstructions.
    """
    pending_path = Path(pending_path)
    ledger_path = Path(ledger_path)
    pending = pd.read_csv(pending_path, keep_default_na=False, dtype={"sample_id": str})
    required_pending = {"sample_id", "image_path", "output_path"}
    missing = sorted(required_pending.difference(pending.columns))
    if missing:
        raise ValueError(f"pending work list is missing columns: {missing}")
    ledger = pd.read_csv(ledger_path, keep_default_na=False, dtype={"sample_id": str})
    missing = sorted(set(LEDGER_COLUMNS).difference(ledger.columns))
    if missing:
        raise ValueError(f"status ledger is missing columns: {missing}")
    if pending["sample_id"].duplicated().any() or ledger["sample_id"].duplicated().any():
        raise ValueError("pending work list and ledger require unique sample_id values")
    ledger = ledger.set_index("sample_id", drop=False)
    unknown = sorted(set(pending["sample_id"]).difference(ledger.index))
    if unknown:
        raise ValueError(f"pending work list contains sample_id not in ledger: {unknown[:10]}")

    attempted = succeeded = failed = 0
    failures: list[dict[str, str]] = []
    rows = pending.to_dict("records")
    for row in rows:
        if limit is not None and attempted >= limit:
            break
        sample_id = str(row["sample_id"])
        if str(ledger.at[sample_id, "status"]) != "pending_3ddfa":
            continue
        attempted += 1
        destination = Path(str(row["output_path"]))
        try:
            depth = _normalise_bona_fide_depth(reconstruct(Path(str(row["image_path"]))), output_size)
            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary = destination.with_suffix(destination.suffix + ".tmp")
            with temporary.open("wb") as handle:
                np.save(handle, depth.astype(np.float32, copy=False))
            temporary.replace(destination)
            valid, error = _valid_depth(destination, require_nonzero=True, zero_tolerance=1e-6)
            if not valid:
                raise ValueError(error)
            ledger.at[sample_id, "status"] = "complete_bona_fide"
            ledger.at[sample_id, "last_error"] = ""
            succeeded += 1
        except Exception as exc:
            message = f"{type(exc).__name__}: {exc}"
            ledger.at[sample_id, "status"] = "failed_bona_fide"
            ledger.at[sample_id, "last_error"] = message
            failures.append({"sample_id": sample_id, "error": message})
            failed += 1

        ledger_frame = ledger.reset_index(drop=True)[LEDGER_COLUMNS]
        remaining = pending[
            pending["sample_id"].map(
                lambda value: str(ledger.at[str(value), "status"]) == "pending_3ddfa"
            )
        ]
        _write_csv_atomic(ledger_frame, ledger_path)
        _write_csv_atomic(remaining, pending_path)
        if failure_report is not None:
            current_failures = ledger_frame.loc[
                ledger_frame["status"] == "failed_bona_fide", ["sample_id", "last_error"]
            ].rename(columns={"last_error": "error"})
            _write_csv_atomic(current_failures, Path(failure_report))

    return {
        "attempted": attempted,
        "succeeded": succeeded,
        "failed": failed,
        "remaining": int((ledger["status"] == "pending_3ddfa").sum()),
    }


def materialize_depth_manifest(
    manifest: str | Path,
    ledger_path: str | Path,
    data_root: str | Path,
    destination: str | Path,
    *,
    provenance_path: str | Path | None = None,
    zero_tolerance: float = 1e-6,
) -> dict[str, int]:
    """Write a derived manifest containing only verified generated depth paths.

    The source manifest is never changed. Every row must have a matching completed
    ledger entry and a valid depth artifact contained by ``data_root`` before the
    derived manifest is written.
    """
    source = Path(manifest)
    ledger_path = Path(ledger_path)
    destination = Path(destination)
    provenance_path = Path(provenance_path) if provenance_path is not None else depth_provenance_path(destination)
    if source.resolve() == destination.resolve():
        raise ValueError("destination must differ from the source manifest")
    reserved_inputs = {source.resolve(), ledger_path.resolve(), destination.resolve()}
    if provenance_path.resolve() in reserved_inputs:
        raise ValueError("provenance sidecar must differ from source, ledger, and destination")

    frame = pd.read_csv(source, keep_default_na=False, dtype={"sample_id": str})
    required = {"sample_id", "split", "image_path", "depth_path", "label"}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"manifest is missing columns: {missing}")
    if frame["sample_id"].duplicated().any():
        raise ValueError("manifest contains duplicate sample_id")
    if not frame["label"].isin([0, 1]).all():
        raise ValueError("manifest labels must be 0 or 1")

    ledger = _read_previous_ledger(ledger_path)
    manifest_ids = set(frame["sample_id"].astype(str))
    ledger_ids = set(ledger)
    missing_ledger = sorted(manifest_ids.difference(ledger_ids))
    extra_ledger = sorted(ledger_ids.difference(manifest_ids))
    if missing_ledger or extra_ledger:
        problems = []
        if missing_ledger:
            problems.append(f"missing ledger sample_id: {missing_ledger[:10]}")
        if extra_ledger:
            problems.append(f"ledger sample_id not in manifest: {extra_ledger[:10]}")
        raise ValueError("; ".join(problems))

    root = Path(data_root).resolve()
    depth_paths: list[str] = []
    counts = {"bona_fide": 0, "attack": 0}
    errors: list[str] = []
    for row in frame.itertuples(index=False):
        sample_id = str(row.sample_id)
        label = int(row.label)
        entry = ledger[sample_id]
        expected_status = COMPLETE_STATUS_BY_LABEL[label]
        expected_image = (root / str(row.image_path)).resolve()
        ledger_image = Path(str(entry["image_path"])).resolve()
        metadata_errors = []
        if str(entry["split"]) != str(row.split):
            metadata_errors.append(f"split {entry['split']} != {row.split}")
        if int(entry["label"]) != label:
            metadata_errors.append(f"label {entry['label']} != {label}")
        if ledger_image != expected_image:
            metadata_errors.append(f"image_path {ledger_image} != {expected_image}")
        if metadata_errors:
            errors.append(f"{sample_id}: stale ledger metadata ({'; '.join(metadata_errors)})")
            continue
        if entry["status"] != expected_status:
            errors.append(f"{sample_id}: status is {entry['status']}, expected {expected_status}")
            continue

        output_path = Path(str(entry["output_path"])).resolve()
        try:
            relative_path = output_path.relative_to(root)
        except ValueError:
            errors.append(f"{sample_id}: output path is outside data root: {output_path}")
            continue
        valid, error = _valid_depth(
            output_path,
            require_nonzero=label == 1,
            zero_tolerance=zero_tolerance,
        )
        if not valid:
            errors.append(f"{sample_id}: {error}")
            continue
        depth_paths.append(relative_path.as_posix())
        counts["bona_fide" if label == 1 else "attack"] += 1

    if errors:
        raise ValueError("cannot materialize depth manifest:\n- " + "\n- ".join(errors[:20]))

    derived = frame.copy()
    derived["depth_path"] = depth_paths
    _write_csv_atomic(derived, destination)
    provenance = {
        "schema_version": PROVENANCE_SCHEMA_VERSION,
        "hash_algorithm": "sha256",
        "source_manifest": {"file": source.name, "sha256": manifest_checksum(source)},
        "ledger": {"file": ledger_path.name, "sha256": manifest_checksum(ledger_path)},
        "derived_manifest": {"file": destination.name, "sha256": manifest_checksum(destination)},
        "rows": len(derived),
        **counts,
    }
    worker_metadata = ledger_path.with_suffix(ledger_path.suffix + ".worker.json")
    if worker_metadata.is_file():
        provenance["worker_metadata"] = {
            "file": worker_metadata.name,
            "sha256": manifest_checksum(worker_metadata),
        }
    _write_json_atomic(provenance, provenance_path)
    return {"rows": len(derived), **counts}
