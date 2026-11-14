"""Restore locked OULU P1 RGB and validate the complete Train/Dev depth set."""
from __future__ import annotations

import json
from pathlib import Path
import zipfile

import numpy as np
import pandas as pd

from .colab_cache import INDEX, copy_progress, file_hash, restore_cache
from .depth_jobs import materialize_depth_manifest
from .depth_qa import audit_depth_targets
from .oulu_depth_smoke import RGB_CACHES
from .progress import Progress


def restore_rgb(cache_dir: Path, work: Path, root: Path) -> Path:
    splits = []
    for split, (name, expected_hash, count) in RGB_CACHES.items():
        manifest = root / f"p1/{split}.csv"
        summary = manifest.with_suffix(".json")
        if not manifest.is_file() or not summary.is_file() or file_hash(manifest) != expected_hash:
            archive = copy_progress(cache_dir / name, work / name, f"Fetch {split} RGB snapshot")
            with zipfile.ZipFile(archive) as bundle:
                index = json.loads(bundle.read(INDEX))
                if index["sha256"].get(f"p1/{split}.csv") != expected_hash:
                    raise ValueError(f"wrong locked manifest in {name}")
                identity = index["identity"]
                if (identity["protocol"], identity["split"], identity["frames_per_video"], identity["pilot"]) != (1, split, 8, False):
                    raise ValueError(f"wrong RGB cache identity: {name}")
            restore_cache(root, archive, identity)
            archive.unlink()
        if file_hash(manifest) != expected_hash or json.loads(summary.read_text())["manifest_sha256"] != expected_hash:
            raise ValueError(f"wrong RGB provenance: {manifest}")
        frame = pd.read_csv(manifest, keep_default_na=False, dtype={"video_id": str})
        if set(frame.split) != {split} or len(frame) != count:
            raise ValueError(f"wrong split membership: {manifest}")
        splits.append(frame)
    train, dev = splits
    if set(train.subject_id) & set(dev.subject_id) or set(train.video_id) & set(dev.video_id):
        raise ValueError("overlapping Train and Dev")
    rows = pd.concat(splits, ignore_index=True)
    if rows.sample_id.duplicated().any() or rows.label.value_counts().to_dict() != {0: 13440, 1: 3360}:
        raise ValueError("unexpected sample membership or class counts")
    destination = root / "train_dev.csv"
    payload = rows.to_csv(index=False, lineterminator="\n").encode("utf-8")
    if destination.is_file() and destination.read_bytes() != payload:
        raise ValueError("existing combined Train/Dev manifest differs")
    destination.write_bytes(payload)
    return destination


def check_full_depth(manifest: Path, ledger: Path, root: Path) -> dict:
    derived = root / "train_dev_with_depth.csv"
    with Progress("Materialize depth manifest"):
        counts = materialize_depth_manifest(manifest, ledger, root, derived)
    if counts != {"rows": 16800, "bona_fide": 3360, "attack": 13440}:
        raise ValueError(f"unexpected depth coverage: {counts}")
    with Progress("Audit depth targets"):
        audit = audit_depth_targets(derived, root, include_checksums=True)
    if not audit["valid"]:
        raise ValueError(audit["issues"][:20])
    rows = pd.read_csv(derived)
    with Progress("Check 32×32 depth shape and dtype", len(rows), "maps") as progress:
        for done, row in enumerate(rows.itertuples(index=False), 1):
            target = np.load(root / row.depth_path, allow_pickle=False)
            if target.shape != (32, 32) or target.dtype != np.float32 or (
                row.label == 1 and (np.ptp(target) <= 0 or target.min() < 0 or target.max() > 1)
            ):
                raise ValueError(f"invalid depth target: {row.sample_id}")
            progress.update(done)
    return {"counts": counts, "audit": audit}
