from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .data import depth_supervision_required, manifest_checksum, validate_manifest
from .depth_jobs import depth_provenance_path, verify_depth_manifest_provenance
from .depth_qa import audit_depth_targets


def _format_depth_issues(issues: list[dict[str, str]]) -> str:
    return "\n- ".join(
        f"{issue['sample_id']} ({issue['split']}): "
        f"{issue['issue']} - {issue['detail']}"
        for issue in issues
    )


def inspect_training_inputs(config: dict) -> tuple[bool, dict[str, Any] | None]:
    """Validate inputs and capture the exact depth state before a run starts.

    The returned snapshot is dependency-light JSON data that can be persisted in
    the run directory after all checks pass. Non-depth configurations return no
    snapshot.
    """
    data = config["data"]
    require_depth = depth_supervision_required(config)
    manifest_errors = validate_manifest(
        data["manifest"],
        data["root"],
        check_files=True,
        require_depth=require_depth,
    )
    if manifest_errors:
        raise ValueError("manifest preflight failed:\n- " + "\n- ".join(manifest_errors))

    if not require_depth:
        return False, None

    required_provenance_keys = ("source_manifest", "depth_ledger")
    missing = [key for key in required_provenance_keys if not data.get(key)]
    if missing:
        raise ValueError(
            "depth provenance preflight failed: missing data config keys: "
            + ", ".join(missing)
        )

    provenance_path = Path(
        data.get("depth_provenance") or depth_provenance_path(data["manifest"])
    )
    provenance = verify_depth_manifest_provenance(
        data["source_manifest"],
        data["depth_ledger"],
        data["manifest"],
        provenance_path=provenance_path,
    )

    depth_report = audit_depth_targets(
        data["manifest"], data["root"], include_checksums=True
    )
    if not depth_report["valid"]:
        raise ValueError(
            "depth content preflight failed:\n- "
            + _format_depth_issues(depth_report["issues"])
        )
    files = {
        "source_manifest": Path(data["source_manifest"]),
        "depth_ledger": Path(data["depth_ledger"]),
        "derived_manifest": Path(data["manifest"]),
        "provenance_sidecar": provenance_path,
    }
    worker_record = provenance.get("worker_metadata")
    if isinstance(worker_record, dict) and worker_record.get("file"):
        files["worker_metadata"] = Path(data["depth_ledger"]).with_name(
            str(worker_record["file"])
        )
    snapshot = {
        "schema_version": 1,
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "hash_algorithm": "sha256",
        "files": {
            key: {"path": str(path), "sha256": manifest_checksum(path)}
            for key, path in files.items()
        },
        "materialization_provenance": provenance,
        "depth_audit": depth_report,
    }
    return True, snapshot


def validate_training_inputs(config: dict) -> bool:
    """Validate training inputs and return whether depth supervision is consumed."""
    require_depth, _ = inspect_training_inputs(config)
    return require_depth
