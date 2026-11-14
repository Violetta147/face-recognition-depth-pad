import ast
import base64
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile
import time
import shutil

import cv2
import numpy as np
import pytest
import torch


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks/Face_PAD_OULU_NPU_CDCN_PRNet_Train_Pilot.ipynb"
sys.path.insert(0, str(ROOT / "scripts"))
try:
    import cdcn_prnet_train_pilot as pilot
    import cdcn_prnet_batch_probe as batch_probe
finally:
    sys.path.pop(0)


def make_assets(root):
    frames = []
    for split, subject in (("Train", 1), ("Dev", 21)):
        for access in (1, 2, 4):
            video = f"1_1_{subject:02}_{access}"
            for kind in ("images", "maps"):
                (root / split / kind / video).mkdir(parents=True)
            for slot in range(8):
                frame = slot + 1
                prefix = f"{video}_{frame:03d}"
                scene = root / split / "images" / video / f"{prefix}_scene.jpg"
                depth = root / split / "maps" / video / f"{prefix}_depth1D.jpg"
                cv2.imwrite(str(scene), np.full((32, 32, 3), 70 + slot, np.uint8))
                cv2.imwrite(str(depth), np.full((32, 32), 100, np.uint8))
                scene.with_suffix(".dat").write_text("0\n0\n32\n32\n")
                frames.append({"slot": slot, "split": split, "access": access, "frame_id": frame,
                               "video_id": video, "prnet_sum_32": 102400, "train_target_zero": access != 1})
    path = root / "smoke_summary.json"
    path.write_text(json.dumps({"slots": list(range(8)), "wide_sample": False,
                                "frames": frames, "failures": []}))
    return path


def test_train_targets_and_dev_denominators_are_distinct(tmp_path):
    make_assets(tmp_path)
    splits = pilot.load_videos(tmp_path)
    for video, rows in splits["Train"].items():
        image, target = pilot.sample_training_frame(tmp_path, rows, np.random.default_rng(43))
        assert image.shape == (3, 256, 256)
        assert target.shape == (1, 32, 32)
        assert bool(target.any()) == video.endswith("_1")
    assert pilot.load_frame(tmp_path, splits["Dev"]["1_1_21_4"][0], 1.3)[1].sum() == 102400
    ratios = pilot.frame_ratios(torch.ones(2, 1, 32, 32), torch.tensor([1024.0, 2048.0]))
    assert ratios.mean().item() == 0.75
    with pytest.raises(ValueError, match="positive"):
        pilot.frame_ratios(torch.ones(1, 1, 32, 32), torch.zeros(1))


def test_duplicate_frame_fails_manifest_validation(tmp_path):
    path = make_assets(tmp_path)
    manifest = json.loads(path.read_text())
    manifest["frames"][0]["frame_id"] = 2
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="duplicate frames"):
        pilot.load_videos(tmp_path)


def test_notebook_compiles_and_bundles_pilot_code():
    content = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    for cell in content["cells"]:
        if cell["cell_type"] == "code":
            compile("".join(cell["source"]), NOTEBOOK.name, "exec")
    bundle_cell = ast.parse("".join(content["cells"][2]["source"]))
    bundle = base64.b64decode(ast.literal_eval(bundle_cell.body[1].value))
    with tarfile.open(fileobj=io.BytesIO(bundle), mode="r:gz") as archive:
        for name in ("scripts/cdcn_prnet_smoke.py", "scripts/cdcn_prnet_train_pilot.py", "scripts/cdcn_prnet_batch_probe.py",
                     "scripts/audit_cdc_n_p1_scores.py", "src/deepface_pad/models/cdcn_official.py"):
            assert archive.extractfile(name).read() == (ROOT / name).read_bytes()


def test_notebook_restores_snapshot_without_preprocessing(tmp_path):
    source, data, work, run = (tmp_path / name for name in ("assets", "data", "work", "run"))
    make_assets(source)
    data.mkdir()
    run.mkdir()
    (work / "scripts").mkdir(parents=True)
    worker = ROOT / "scripts/cdcn_prnet_smoke.py"
    shutil.copyfile(worker, work / "scripts" / worker.name)
    for name in ("Protocols.tar", "Train_files.tar", "Dev_files.tar"):
        (data / name).write_bytes(b"fixture")
    sha = hashlib.sha256(b"fixture").hexdigest()
    key = {"profile": "p1-3-videos-per-split-8-frames", "protocol": sha,
           "archives": {name: {"bytes": 7, "prefix_sha256": sha} for name in ("Train_files.tar", "Dev_files.tar")},
           "preparer": hashlib.sha256(worker.read_text(encoding="utf-8").encode()).hexdigest()}
    cache_name = hashlib.sha256(json.dumps(key, sort_keys=True).encode()).hexdigest()[:20]
    cache = run.parent / "prepared-cache" / cache_name
    cache.mkdir(parents=True)
    zipped = Path(shutil.make_archive(str(tmp_path / "fixture"), "zip", source))
    digest = pilot.sha(zipped)
    zipped.rename(cache / f"assets-{digest}.zip")
    (cache / "snapshot.json").write_text(json.dumps({"key": key, "sha256": digest}))
    cell = json.loads(NOTEBOOK.read_text(encoding="utf-8"))["cells"][3]
    state = {"Path": Path, "DATA": data, "WORK": work, "RUN": run, "hashlib": hashlib,
             "shutil": shutil, "time": time, "Progress": pilot.Progress}
    exec("".join(cell["source"]), state)
    assert len(pilot.load_videos(state["assets"])["Dev"]) == 3
    assert (run / "preparation.json").read_bytes() == (source / "smoke_summary.json").read_bytes()


def test_batch_probe_measures_training_updates_and_retains_partial_results(tmp_path, monkeypatch):
    class TinyDepthModel(torch.nn.Module):
        def __init__(self, theta):
            super().__init__()
            assert theta == 0.7
            self.conv = torch.nn.Conv2d(3, 1, 1)

        def forward(self, image):
            return {"depth": self.conv(image)}

    make_assets(tmp_path)
    images, targets = batch_probe.prepare_pool(tmp_path, 43)
    assert images.shape == (24, 3, 256, 256)
    assert targets.flatten(1).any(dim=1).sum() == 8
    monkeypatch.setattr(batch_probe, "OfficialCDCN", TinyDepthModel)
    monkeypatch.setattr(batch_probe, "prepare_pool", lambda *args: (images[:, :, :32, :32], targets))
    original = batch_probe.measure_batch

    def measure(pool, batch, *args):
        if batch == 4:
            raise torch.cuda.OutOfMemoryError("fixture")
        return original(pool, batch, *args)

    monkeypatch.setattr(batch_probe, "measure_batch", measure)
    out = tmp_path / "probe.json"
    batch_probe.probe(tmp_path, out, [2, 4, 5], 1, 2, 43, torch.device("cpu"))
    report = json.loads(out.read_text())
    assert [row["status"] for row in report["batches"]] == ["ok", "out_of_memory", "ok"]
    assert report["batches"][0]["frames_per_second"] > 0
    assert len(report["batches"][0]["update_seconds"]) == 2
