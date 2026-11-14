import hashlib
from pathlib import Path

import pandas as pd
import pytest

from deepface_pad.colab_cache import save_cache
from deepface_pad import oulu_depth_full as full


def test_restore_rgb_uses_locked_manifests_and_rejects_changed_local_copy(tmp_path, monkeypatch):
    sizes = {"train": (9600, 1), "val": (7200, 21)}
    archive_root = tmp_path / "drive"
    caches = {}
    for split, (size, subject) in sizes.items():
        source = tmp_path / split
        manifest = source / f"p1/{split}.csv"
        manifest.parent.mkdir(parents=True)
        pixels = source / f"{split}.png"
        pixels.write_bytes(split.encode())
        rows = pd.DataFrame({
            "sample_id": [f"{split}-{i}" for i in range(size)],
            "split": split, "subject_id": subject, "video_id": f"{split}-clip",
            "image_path": pixels.name, "label": [i % 5 == 0 for i in range(size)],
        })
        rows["label"] = rows.label.astype(int)
        rows.to_csv(manifest, index=False)
        digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
        summary = manifest.with_suffix(".json")
        summary.write_text(f'{{"manifest_sha256":"{digest}"}}')
        archive = archive_root / f"{split}.zip"
        save_cache(source, archive, [manifest, summary, pixels], {
            "protocol": 1, "split": split, "frames_per_video": 8, "pilot": False,
        })
        caches[split] = (archive.name, digest, size)
    monkeypatch.setattr(full, "RGB_CACHES", caches)

    work = tmp_path / "work"
    root = work / "cache"
    result = full.restore_rgb(archive_root, work, root)
    assert len(pd.read_csv(result)) == 16800
    assert (root / "train.png").read_bytes() == b"train"
    assert (root / "val.png").read_bytes() == b"val"
    assert full.restore_rgb(archive_root, work, root) == result
    (root / "p1/val.csv").write_text("changed")
    with pytest.raises(ValueError, match="local cache differs"):
        full.restore_rgb(archive_root, work, root)


def test_full_depth_enforces_coverage(tmp_path, monkeypatch):
    monkeypatch.setattr(full, "materialize_depth_manifest", lambda *_: {"rows": 32, "bona_fide": 24, "attack": 8})
    with pytest.raises(ValueError, match="unexpected depth coverage"):
        full.check_full_depth(Path("manifest.csv"), Path("ledger.csv"), tmp_path)
