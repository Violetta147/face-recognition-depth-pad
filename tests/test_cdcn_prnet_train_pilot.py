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
    import cdcn_prnet_expanded as expanded
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


def test_expanded_selection_and_video_cache(tmp_path, monkeypatch):
    protocol = tmp_path / "Protocols.tar"
    with tarfile.open(protocol, "w") as archive:
        for split, subjects in (("Train", range(1, 10)), ("Dev", range(21, 28))):
            data = "\n".join(f"{1 if access == 1 else -1},1_1_{subject:02}_{access}"
                             for subject in subjects for access in range(1, 6)).encode()
            entry = tarfile.TarInfo(f"Protocols/Protocol_1/{split}.txt")
            entry.size = len(data)
            archive.addfile(entry, io.BytesIO(data))
    train = expanded.select_group(protocol, "Train")
    dev = expanded.select_group(protocol, "Dev")
    assert len(train) == 40 and len(dev) == 30
    assert "1_1_08_5" in train and "1_1_09_1" not in train
    assert "1_1_26_5" in dev and "1_1_27_1" not in dev
    source = tmp_path / "source"
    make_assets(source)
    rows = pilot.load_videos(source)["Dev"]["1_1_21_4"]
    cache = tmp_path / "video.zip"
    original_stat = Path.stat
    stale_reads = []

    def stale_size(path, *args, **kwargs):
        result = original_stat(path, *args, **kwargs)
        if path.suffix == ".part" and not stale_reads:
            from types import SimpleNamespace
            stale_reads.append(path)
            return SimpleNamespace(st_size=0)
        return result

    monkeypatch.setattr(Path, "stat", stale_size)
    expanded.publish_video(cache, source, "Dev", "1_1_21_4", 4, rows)
    assert len(stale_reads) == 1
    restored = tmp_path / "restored"
    assert expanded.restore_video(cache, restored, "Dev", "1_1_21_4", 4) == rows
    np.testing.assert_array_equal(pilot.load_frame(source, rows[0], 1.3)[1],
                                  pilot.load_frame(restored, rows[0], 1.3)[1])
    with pytest.raises(ValueError, match="incomplete"):
        expanded.publish_video(tmp_path / "incomplete.zip", source, "Dev", "1_1_21_4", 4, rows[:-1])
    notebook = ROOT / "notebooks/Face_PAD_OULU_NPU_CDCN_PRNet_Expanded.ipynb"
    for cell in json.loads(notebook.read_text(encoding="utf-8"))["cells"]:
        if cell["cell_type"] == "code":
            compile("".join(cell["source"]), notebook.name, "exec")


def test_full_membership_requires_official_ids_and_split_frame_counts(tmp_path):
    from deepface_pad.oulu_npu import expected_ids

    protocol = tmp_path / "Protocols.tar"
    rows = []
    with tarfile.open(protocol, "w") as archive:
        for split, alias, slots in (("Train", "train", expanded.FULL_TRAIN_SLOTS), ("Dev", "val", range(8))):
            entries = []
            for phone, session, subject, access in sorted(expected_ids(1, None, alias)):
                video = f"{phone}_{session}_{subject:02}_{access}"
                entries.append(f"{1 if access == 1 else -1},{video}")
                rows.extend({"split": split, "video_id": video, "access": access, "slot": slot,
                             "frame_id": slot + 1, "train_target_zero": access != 1} for slot in slots)
            data = "\n".join(entries).encode()
            entry = tarfile.TarInfo(f"Protocols/Protocol_1/{split}.txt")
            entry.size = len(data)
            archive.addfile(entry, io.BytesIO(data))
    path = tmp_path / "smoke_summary.json"
    manifest = {"profile": "full", "failures": [], "slots": list(range(8)),
                "train_slots": list(expanded.FULL_TRAIN_SLOTS), "protocol_sha256": pilot.sha(protocol),
                "frames": rows}
    path.write_text(json.dumps(manifest))
    splits = pilot.load_videos(tmp_path, "full", protocol)
    assert {split: len(videos) for split, videos in splits.items()} == expanded.FULL_COUNTS
    assert len(rows) == 36000
    for row in rows[:24]:
        row["video_id"] = "7_1_01_1"
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="IDs differ"):
        pilot.load_videos(tmp_path, "full", protocol)


def test_full_notebook_compiles_with_cpu_prepare_and_batch_56():
    notebook = ROOT / "notebooks/Face_PAD_OULU_NPU_CDCN_PRNet_Full_Train_Dev.ipynb"
    cells = json.loads(notebook.read_text(encoding="utf-8"))["cells"]
    for cell in cells[1:]:
        compile("".join(cell["source"]), notebook.name, "exec")
    assert "BATCH = 56" in "".join(cells[4]["source"])
    assert '"--restore-only"' in "".join(cells[3]["source"])
    assert '"--device", "cuda"' in "".join(cells[4]["source"])


def test_threaded_train_epoch_keeps_short_final_batch(tmp_path, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from torch.nn import functional as F

    class Model(torch.nn.Conv2d):
        def forward(self, image):
            return {"depth": super().forward(image)}

    def sample(root, rows, rng):
        return torch.ones(3, 4, 4), torch.full((1, 4, 4), float(rows[0]))

    monkeypatch.setattr(pilot, "sample_training_frame", sample)
    model = Model(3, 1, 1)
    optimizer = torch.optim.Adam(model.parameters())
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=500)
    with ThreadPoolExecutor(max_workers=2) as pool:
        history = pilot.train_epochs(
            model, F.mse_loss, optimizer, scheduler, ["a", "b", "c"],
            {"a": [0], "b": [1], "c": [0]}, tmp_path, torch.device("cpu"),
            1, 2, np.random.default_rng(43), pool, 2,
        )
    assert history[0]["updates"] == 2
    assert all(int(state["step"]) == 2 for state in optimizer.state.values())
    assert 0 < history[0]["load_seconds"] <= history[0]["seconds"]
