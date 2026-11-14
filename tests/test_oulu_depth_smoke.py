import hashlib
import json
import zipfile

import numpy as np
import pandas as pd
import pytest

from deepface_pad import oulu_depth_smoke as smoke
from deepface_pad.depth_jobs import process_pending_depth_jobs


def test_smoke_prepares_and_audits_targets(tmp_path, monkeypatch):
    caches = {}
    for split, subject in (("train", "01"), ("val", "21")):
        rows = []
        images = {}
        for phone in range(1, 7):
            for session in range(1, 3):
                for access in range(1, 6):
                    video = f"{phone}_{session}_{subject}_{access}"
                    for index in range(8):
                        sample = f"{video}_{index}"
                        name = f"{split}/{sample}.png"
                        value = sample.encode()
                        images[name] = hashlib.sha256(value).hexdigest()
                        rows.append(dict(sample_id=sample, video_id=video, frame_index=index, split=split,
                                         image_path=name, image_sha256=images[name], label=int(access == 1),
                                         depth_path=""))
        manifest = pd.DataFrame(rows).to_csv(index=False).encode()
        name = f"{split}.zip"
        with zipfile.ZipFile(tmp_path / name, "w") as archive:
            archive.writestr("CACHE_INDEX.json", json.dumps({
                "identity": dict(protocol=1, split=split, frames_per_video=8, pilot=False), "sha256": images,
            }))
            archive.writestr(f"p1/{split}.csv", manifest)
            for row in rows:
                archive.writestr(row["image_path"], row["sample_id"].encode())
        caches[split] = (name, hashlib.sha256(manifest).hexdigest(), len(rows))
    monkeypatch.setattr(smoke, "RGB_CACHES", caches)

    root = tmp_path / "runtime"
    manifest, counts = smoke.prepare_smoke(tmp_path, root)
    assert counts["pending_3ddfa"] == 24
    assert counts["complete_attack_zero"] == 8
    frame = pd.read_csv(manifest)
    assert frame.frame_index.eq(3).all()
    assert frame.groupby(["split", "label"]).size().tolist() == [4, 12, 4, 12]
    with pytest.raises(ValueError, match="expected complete_bona_fide"):
        smoke.verify_smoke(manifest, root)
    depth = root / "depth"
    process_pending_depth_jobs(depth / "3ddfa_pending.csv", depth / "depth_status.csv",
                               lambda _: np.arange(32 * 32, dtype=np.float32).reshape(32, 32))
    assert smoke.verify_smoke(manifest, root)["counts"] == {"rows": 32, "bona_fide": 24, "attack": 8}
