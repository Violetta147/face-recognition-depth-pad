import ast
import base64
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import hashlib
import io
import json
import multiprocessing
import os
from pathlib import Path
import sys
import tarfile
from threading import Barrier
from types import SimpleNamespace

import cv2
import numpy as np
import pandas as pd
import pytest
import torch

from deepface_pad.oulu_npu import expected_ids


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
try:
    import cdcn_prnet_expanded as expanded
    import cdcn_prnet_locked_test as locked
finally:
    sys.path.pop(0)


@pytest.fixture
def test_protocol(tmp_path, monkeypatch):
    protocol = tmp_path / "Protocols.tar"
    records = "".join(f"{1 if a == 1 else -1 if a < 4 else -2},{p}_{s}_{u:02d}_{a}\n"
                      for p, s, u, a in sorted(expected_ids(1, None, "test"))).encode()
    with tarfile.open(protocol, "w") as archive:
        member = tarfile.TarInfo("Protocols/Protocol_1/Test.txt")
        member.size = len(records)
        archive.addfile(member, io.BytesIO(records))
    monkeypatch.setitem(locked.LOCK, "protocol_sha256", locked.sha(protocol))
    return protocol


def test_test_preparation_restores_all_official_test_videos_only(tmp_path, test_protocol, monkeypatch):
    cache, assets = tmp_path / "cache", tmp_path / "assets"
    members = expanded.full_membership(test_protocol, splits=("Test",))["Test"]
    (cache / "Test").mkdir(parents=True)
    for video in members:
        (cache / "Test" / f"{video}.zip").touch()

    def restore(path, root, split, video, access, slots, *, stage_zip):
        assert split == "Test" and stage_zip
        return [{"video_id": video, "split": split, "access": access, "slot": slot,
                 "frame_id": slot + 1, "prnet_sum_32": 10, "train_target_zero": access != 1}
                for slot in slots]

    monkeypatch.setattr(expanded, "restore_video", restore)
    expanded.prepare(tmp_path, cache, assets, None, None, full=True, splits=["Test"], restore_only=True)
    videos = locked.load_test_videos(assets, test_protocol)
    assert len(videos) == 600
    assert sum(len(rows) for rows in videos.values()) == 4800
    assert sum(rows[0]["access"] == 1 for rows in videos.values()) == 120
    manifest_path = assets / "smoke_summary.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["frames"].pop()
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="Invalid or incomplete assets"):
        locked.load_test_videos(assets, test_protocol)
    with pytest.raises(ValueError, match="by itself"):
        expanded.prepare(tmp_path, cache, assets, None, None, full=True, splits=["Dev", "Test"])


def test_score_publishes_frozen_threshold_and_rejects_checkpoint_or_report_changes(
        tmp_path, test_protocol, monkeypatch):
    run, output = tmp_path / locked.RUN_NAME, tmp_path / "output"
    work = tmp_path / "scoring"
    run.mkdir()
    output.mkdir()
    checkpoint = run / "checkpoint.pt"
    torch.save({"weight": torch.tensor([1.0])}, checkpoint)
    monkeypatch.setitem(locked.LOCK, "checkpoint_sha256", locked.sha(checkpoint))
    threshold = locked.LOCK["threshold_from_dev"]
    report = {key: locked.LOCK[key] for key in ("checkpoint_sha256", "assets_manifest_sha256", "seed", "batch")}
    report.update(mode="full", train_videos=1200, dev_videos=900, dev_frames_per_video=8,
                  architecture_source_commit=locked.OFFICIAL_CDCN_PROVENANCE["git_commit"],
                  dev={"threshold_from_dev": threshold / 2},
                  history=[{"epoch": epoch} for epoch in range(1, 101)])
    report_path = run / "pilot_result.json"
    report_path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match="locked 100-epoch run"):
        locked.verify_run(run, test_protocol)
    report["dev"]["threshold_from_dev"] = threshold
    report_path.write_text(json.dumps(report))
    (output / "test_lock.json").write_text(json.dumps(locked.verify_run(run, test_protocol)))
    (tmp_path / "smoke_summary.json").write_text("{}")

    model = SimpleNamespace(to=lambda device: model, load_state_dict=lambda state: None)
    monkeypatch.setattr(locked, "OfficialCDCN", lambda theta: model)
    videos = {f"video{i}": [] for i in range(4)}
    monkeypatch.setattr(locked, "load_test_videos", lambda *args: videos)

    def score(model, assets, found_videos, batch, device, *, split):
        assert split == "Test" and batch == 56 and found_videos == videos
        return pd.DataFrame({"video_id": list(videos), "label": [1, 1, 0, 0],
                             "score": [threshold, threshold * 2, threshold, threshold * 2]})

    monkeypatch.setattr(locked, "score_videos", score)
    locked.evaluate(run, tmp_path, test_protocol, work, output, torch.device("cpu"))
    metrics = json.loads((output / "test_metrics.json").read_text())
    assert metrics["threshold_from_dev"] == threshold
    assert metrics["test"]["live_rejected"] == metrics["test"]["attack_accepted"] == 1
    assert metrics["test"]["acer_pooled"] == 0.5
    assert locked.sha(output / "test_scores.csv") == metrics["test_scores_sha256"]
    with pytest.raises(FileExistsError):
        locked.evaluate(run, tmp_path, test_protocol, work, output, torch.device("cpu"))
    checkpoint.write_text("invalid checkpoint")
    with pytest.raises(ValueError, match="checkpoint SHA-256"):
        locked.verify_run(run, test_protocol)


def test_test_notebook_bundles_current_code():
    notebook = ROOT / "notebooks/Face_PAD_OULU_NPU_CDCN_PRNet_Locked_Test.ipynb"
    cells = json.loads(notebook.read_text(encoding="utf-8"))["cells"]
    for cell in cells[1:]:
        compile("".join(cell["source"]), str(notebook), "exec")
    cell = "".join(cells[2]["source"])
    scope = {}
    exec(cell.split("\nimport base64", 1)[0], scope)
    with tarfile.open(fileobj=io.BytesIO(base64.b64decode(scope["BUNDLE"])), mode="r:gz") as archive:
        for script in ("cdcn_prnet_locked_test", "cdcn_prnet_train_pilot", "cdcn_prnet_expanded"):
            name = f"scripts/{script}.py"
            assert archive.extractfile(name).read() == (ROOT / name).read_bytes()


def test_parallel_revision_uses_existing_test_cache():
    notebook = ROOT / "notebooks/Face_PAD_OULU_NPU_CDCN_PRNet_Locked_Test.ipynb"
    cell = "".join(json.loads(notebook.read_text(encoding="utf-8"))["cells"][3]["source"])
    function = next(node for node in ast.parse(cell).body
                    if isinstance(node, ast.FunctionDef) and node.name == "test_cache_worker_hashes")
    scope = {}
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(notebook), "exec"), scope)
    workers = {name: hashlib.sha256((ROOT / "scripts" / name).read_text(encoding="utf-8").encode()).hexdigest()
               for name in ("cdcn_prnet_smoke.py", "cdcn_prnet_expanded.py")}
    normalize = scope[function.name]
    # Recorded by the serial notebook for the private Test TAR.
    config = {"protocol": locked.LOCK["protocol_sha256"], "profile": "p1-test8-mtcnn-prnet",
              "archive": {"name": "Test_files.tar", "bytes": 39211162112,
                          "prefix_sha256": "f8aaf9090246f0378a792467a635e811d30afdde685e68a905837ec4fc78c50e"},
              "workers": normalize(workers)}
    assert hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()[:20] == "6566c176f4d084b28ef0"
    changed = workers | {"cdcn_prnet_smoke.py": "f" * 64}
    assert normalize(changed) == changed


@pytest.mark.parametrize("mismatch", [None, "cache", "parallel"])
def test_prepare_checks_same_runtime_and_cache_before_parallel_publishing(tmp_path, monkeypatch, capsys, mismatch):
    (tmp_path / "Protocols.tar").write_bytes(b"fixture")
    members = {f"1_3_36_{access}": access for access in (1, 2, 3)}
    with tarfile.open(tmp_path / "Test_files.tar", "w") as archive:
        for video in members:
            member = tarfile.TarInfo(f"Test/{video}.avi")
            member.size = 4
            archive.addfile(member, io.BytesIO(b"mock"))

    prnet, renderer = tmp_path / "PRNet", tmp_path / "renderer"
    weight = prnet / "Data/net-data/256_256_resfcn256_weight.data-00000-of-00001"
    weight.parent.mkdir(parents=True)
    weight.write_bytes(b"tf-data")
    weight.with_suffix(".index").write_bytes(b"tf-index")
    monkeypatch.setattr(expanded, "WEIGHT_SHA", expanded.sha(weight))
    monkeypatch.setattr(expanded, "INDEX_SHA", expanded.sha(weight.with_suffix(".index")))
    monkeypatch.setattr(expanded, "subprocess", SimpleNamespace(
        check_output=lambda command, text: expanded.PRNET_COMMIT if Path(command[2]) == prnet else expanded.DEPTH_COMMIT))
    monkeypatch.setattr(expanded, "full_membership", lambda protocol, splits: {"Test": members})
    monkeypatch.setattr(expanded, "load_models", lambda *args: ())
    monkeypatch.setattr(expanded, "init_process", lambda *args: None)
    monkeypatch.setattr(expanded.os, "cpu_count", lambda: 2)
    if hasattr(expanded.os, "sched_getaffinity"):
        monkeypatch.setattr(expanded.os, "sched_getaffinity", lambda pid: {0, 1})
    monkeypatch.setattr(expanded, "ProcessPoolExecutor", lambda max_workers, **options:
                        ThreadPoolExecutor(max_workers=max_workers))
    cache, output, baseline = tmp_path / "cache", tmp_path / "assets", tmp_path / "baseline"
    (cache / "Test").mkdir(parents=True)
    first = next(iter(members))
    barrier = Barrier(2, timeout=5)

    def emit(path, access, split, root, models, slots, *, spread_train):
        assert not spread_train
        if root.name in ("probe-parallel", "rendered"):
            barrier.wait()
        unequal = (mismatch == "cache" and root.name == "baseline"
                   or mismatch == "parallel" and root.name == "probe-parallel")
        depth_value = 101 if unequal else 100
        result = []
        for slot in slots:
            scene, box, depth = (root / name for name in expanded.frame_assets(split, path.stem, slot + 1))
            scene.parent.mkdir(parents=True, exist_ok=True)
            depth.parent.mkdir(parents=True, exist_ok=True)
            assert cv2.imwrite(str(scene), np.full((32, 32, 3), 60, dtype=np.uint8))
            assert cv2.imwrite(str(depth), np.full((32, 32), depth_value, dtype=np.uint8))
            box.write_text("0\n0\n32\n32\n")
            result.append({"video_id": path.stem, "split": split, "access": access, "slot": slot,
                           "frame_id": slot + 1, "prnet_sum_32": depth_value * 32 * 32,
                           "train_target_zero": access != 1})
        return result

    monkeypatch.setattr(expanded, "emit_video", emit)
    rows = emit(Path(f"{first}.avi"), 1, "Test", baseline, (), expanded.PILOT_SLOTS, spread_train=False)
    first_zip = cache / "Test" / f"{first}.zip"
    expanded.publish_video(first_zip, baseline, "Test", first, 1, rows)
    old_hash, old_mtime = expanded.sha(first_zip), first_zip.stat().st_mtime_ns
    if mismatch:
        label = "CACHED_TEST_DIFFERS" if mismatch == "cache" else "PARALLEL_TEST_DIFFERS"
        with pytest.raises(ValueError, match=f"{label}.*depth_sum"):
            expanded.prepare(tmp_path, cache, output, prnet, renderer, full=True, splits=["Test"], workers=2)
        assert len(list((cache / "Test").glob("*.zip"))) == 1
        assert not (output / "smoke_summary.json").exists()
    else:
        expanded.prepare(tmp_path, cache, output, prnet, renderer, full=True, splits=["Test"], workers=2)
        log = capsys.readouterr().out
        assert "PARALLEL_NUMERIC_MATCH 2 videos | 1 compared with cache" in log and "PREP_WORKERS 2" in log
        assert len(list((cache / "Test").glob("*.zip"))) == 3
        manifest = json.loads((output / "smoke_summary.json").read_text(encoding="utf-8"))
        assert not manifest["failures"] and len(manifest["frames"]) == 24
    assert old_hash == expanded.sha(first_zip) and old_mtime == first_zip.stat().st_mtime_ns
    assert not list(output.glob("prepare-*"))


def test_automatic_workers_respects_cpu_and_available_ram():
    notebook = ROOT / "notebooks/Face_PAD_OULU_NPU_CDCN_PRNet_Locked_Test.ipynb"
    cell = "".join(json.loads(notebook.read_text(encoding="utf-8"))["cells"][3]["source"])
    function = next(node for node in ast.parse(cell).body
                    if isinstance(node, ast.FunctionDef) and node.name == "automatic_workers")
    scope = {}
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(notebook), "exec"), scope)
    workers = scope[function.name]
    assert workers(8, 48 * 2**30) == 4
    assert workers(4, 25 * 2**30) == 2
    assert workers(8, 7 * 2**30) == 1
    assert workers(2, 12 * 2**30) == 1


def _read_avi_in_worker(path, access, output):
    return os.getpid(), path.read_bytes()


def test_parallel_jobs_run_in_spawned_processes(tmp_path, monkeypatch):
    tar = tmp_path / "Test_files.tar"
    waiting = {f"1_3_36_{access}": access for access in (1, 2, 3)}
    with tarfile.open(tar, "w") as archive:
        for video in waiting:
            payload = video.encode()
            member = tarfile.TarInfo(f"{video}.avi")
            member.size = len(payload)
            archive.addfile(member, io.BytesIO(payload))

    monkeypatch.setattr(expanded, "prepare_test_video", _read_avi_in_worker)
    with ProcessPoolExecutor(max_workers=2, mp_context=multiprocessing.get_context("spawn")) as pool:
        with tarfile.open(tar) as archive:
            jobs = list(expanded.parallel_jobs(pool, archive, tmp_path, tmp_path, waiting, 2))
    assert not waiting and len(jobs) == 3
    assert all(pid != os.getpid() and payload == path.stem.encode() for path, _, (pid, payload) in jobs)
