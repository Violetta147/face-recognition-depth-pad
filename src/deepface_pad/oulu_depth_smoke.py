"""Select and verify a small 3DDFA V2 smoke set from the locked OULU RGB caches."""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import zipfile

import pandas as pd
import numpy as np

from .depth_jobs import materialize_depth_manifest, prepare_depth_jobs
from .depth_qa import audit_depth_targets
from .progress import Progress


RGB_CACHES = {
    "train": ("rgb-p1-train-1cf7521de73c02df19be.zip",
              "d47bdff66a6c4da7b0f7e9a575d0e1d2570f7dcf9e8b6054633d590cc9df4124", 9600),
    "val": ("rgb-p1-val-de54e155f6572c87ca2f.zip",
            "cb749e10d8547e5e2dd6715250e359993da7b0d32df76013edd9a9acaa32df6d", 7200),
}


def select_smoke(frame):
    """One bona fide frame per phone/session, plus one per attack instrument."""
    data = frame.copy()
    data[["phone", "session", "subject", "access"]] = data.video_id.str.split("_", expand=True)
    data = data.sort_values(["phone", "session", "subject", "video_id", "frame_index"])
    live = data.loc[data.label.eq(1)].groupby(["phone", "session"], sort=True)
    attack = data.loc[data.label.eq(0)].groupby("access", sort=True)
    if len(live) != 12 or set(attack.groups) != {"2", "3", "4", "5"}:
        raise ValueError("expected six cameras × two sessions and four attack instruments")
    # Select the same interior frame position within every chosen video.
    picks = [group.loc[group.video_id.eq(group.video_id.iloc[0])].iloc[3]
             for _, group in [*live, *attack]]
    return pd.DataFrame(picks, columns=frame.columns).reset_index(drop=True)


def prepare_smoke(cache_dir, root):
    root.mkdir(parents=True, exist_ok=True)
    splits = []
    for split, (name, manifest_hash, expected_size) in RGB_CACHES.items():
        with Progress(f"Verify and restore {split} smoke RGB", 16, "frames") as progress:
            with zipfile.ZipFile(cache_dir / name) as archive:
                index = json.loads(archive.read("CACHE_INDEX.json"))
                identity = index["identity"]
                if (identity["protocol"], identity["split"], identity["frames_per_video"], identity["pilot"]) != (1, split, 8, False):
                    raise ValueError(f"wrong snapshot identity: {name}")
                raw = archive.read(f"p1/{split}.csv")
                if hashlib.sha256(raw).hexdigest() != manifest_hash:
                    raise ValueError(f"unexpected manifest hash: {name}")
                frame = pd.read_csv(io.BytesIO(raw), keep_default_na=False, dtype={"video_id": str})
                if len(frame) != expected_size or set(frame.split) != {split}:
                    raise ValueError(f"unexpected manifest population: {name}")
                selected = select_smoke(frame)
                for done, row in enumerate(selected.itertuples(index=False), 1):
                    destination = (root / row.image_path).resolve()
                    if not destination.is_relative_to(root.resolve()) or destination.suffix != ".png":
                        raise ValueError(f"invalid image path: {row.image_path}")
                    image = archive.read(row.image_path)
                    if hashlib.sha256(image).hexdigest() != row.image_sha256 or index["sha256"][row.image_path] != row.image_sha256:
                        raise ValueError(f"unexpected RGB hash: {row.sample_id}")
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(image)
                    progress.update(done)
                splits.append(selected)
    manifest = root / "rgb_smoke.csv"
    pd.concat(splits, ignore_index=True).to_csv(manifest, index=False, lineterminator="\n")
    counts = prepare_depth_jobs(manifest, root, root / "depth")
    return manifest, counts


def verify_smoke(manifest: Path, root: Path) -> dict:
    ledger = root / "depth/depth_status.csv"
    derived = root / "rgb_smoke_with_depth.csv"
    counts = materialize_depth_manifest(manifest, ledger, root, derived)
    report = audit_depth_targets(derived, root, include_checksums=True)
    frame = pd.read_csv(derived)
    for row in frame.itertuples(index=False):
        value = np.load(root / row.depth_path, allow_pickle=False)
        if value.shape != (32, 32) or value.dtype != np.float32 or (
            row.label == 1 and (np.ptp(value) <= 0 or value.min() < 0 or value.max() > 1)
        ):
            raise ValueError(f"invalid target: {row.sample_id}")
    if not report["valid"]:
        raise ValueError(report["issues"])
    return {"counts": counts, "audit": report}
