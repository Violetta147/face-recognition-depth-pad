import json
from pathlib import Path
import sys
import zipfile

import pytest

from deepface_pad.colab_cache import copy_progress, depth_identity, file_hash, prepare_oulu_split, restore_cache, save_cache
from deepface_pad.progress import Progress, run_logged


def test_progress_heartbeat_and_error_log(tmp_path, capsys):
    import time

    with Progress("crop", total=20, unit="videos", interval=.01) as progress:
        progress.update(2)
        time.sleep(.05)
    output = capsys.readouterr().out
    assert "running 2/20 videos" in output and "finished 2/20 videos" in output
    log = tmp_path / "worker.log"
    with pytest.raises(RuntimeError, match="code 3"):
        run_logged([sys.executable, "-u", "-c", "import sys; print('bad Dev crop', file=sys.stderr); sys.exit(3)"],
                   label="Dev", log=log)
    assert "bad Dev crop" in log.read_text(encoding="utf-8")
    assert "bad Dev crop" in capsys.readouterr().out


def test_cache_restore_reuses_verified_files_and_rejects_mismatch(tmp_path):
    root = tmp_path / "prepared"
    root.mkdir()
    image, manifest = root / "frame.png", root / "val.csv"
    image.write_bytes(b"image")
    manifest.write_bytes(b"manifest")
    archive = tmp_path / "cache.zip"
    identity = {"protocol": 1, "frames_per_video": 8}
    save_cache(root, archive, [image, manifest], identity)
    local = copy_progress(archive, tmp_path / "runtime" / "cache.zip", "download")
    restored = tmp_path / "restored"
    with pytest.raises(ValueError, match="settings differ"):
        restore_cache(restored, local, identity | {"frames_per_video": 20})
    restore_cache(restored, local, identity)
    restore_cache(restored, local, identity)
    assert (restored / "val.csv").read_bytes() == b"manifest"
    (restored / "frame.png").write_bytes(b"changed")
    with pytest.raises(ValueError, match="local cache differs"):
        restore_cache(restored, local, identity)


def test_restore_rejects_escape_before_writing(tmp_path):
    archive = tmp_path / "cache.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("../unexpected", b"x")
        bundle.writestr("CACHE_INDEX.json", json.dumps({"identity": {}, "sha256": {"../unexpected": "x"}}))
    with pytest.raises(ValueError, match="invalid cache path"):
        restore_cache(tmp_path / "restored", archive, {})
    assert not (tmp_path / "unexpected").exists()


def test_depth_identity_uses_image_and_weights_content(tmp_path):
    image, weights, config = [tmp_path / name for name in ("frame.png", "weights.pth", "config.yml")]
    for path in (image, weights, config):
        path.write_bytes(b"original")
    manifest = tmp_path / "train.csv"
    manifest.write_text("image_path\nframe.png\n", encoding="utf-8")
    worker = tmp_path / "worker.json"
    worker.write_text(json.dumps({"git_commit": "abc", "config_file": config.name, "config_sha256": file_hash(config),
                                  "worker_script_sha256": "def", "backend": "onnx", "mode": "cpu", "output_size": 32}))
    first = depth_identity(tmp_path, manifest, worker, [config, weights])
    weights.write_bytes(b"changed")
    second = depth_identity(tmp_path, manifest, worker, [config, weights])
    assert first["assets"] != second["assets"]
    image.write_bytes(b"new crop")
    third = depth_identity(tmp_path, manifest, worker, [config, weights])
    assert second["rgb_content_sha256"] != third["rgb_content_sha256"]


def test_completed_rgb_split_is_restored_without_copying_raw_tar(tmp_path, monkeypatch):
    import csv
    import shutil

    cv2 = pytest.importorskip("cv2")
    from deepface_pad import colab_cache, oulu_npu

    data, workspace, backups = [tmp_path / name for name in ("data", "work", "backups")]
    data.mkdir()
    (data / "Train_files.tar").write_bytes(b"fixture TAR")
    (data / "Protocols.tar").write_bytes(b"fixture protocol")
    monkeypatch.setitem(colab_cache.SPLIT_ARCHIVES, "train", ("Train_files.tar", 11))
    monkeypatch.setattr(oulu_npu, "expected_ids", lambda *_: {1})
    cache = workspace / "cache"
    image = cache / "crops/train/key/video/0001.png"
    image.parent.mkdir(parents=True)
    image.write_bytes(b"rgb")
    image.with_name("frames.json").write_bytes(b"[]")
    manifest = cache / "p1/train.csv"
    manifest.parent.mkdir()
    with manifest.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["image_path", "image_sha256"])
        writer.writerow([image.relative_to(cache).as_posix(), file_hash(image)])
    (workspace / "yunet.onnx").write_bytes(b"detector")
    archive = data / "Train_files.tar"
    summary = {"crop_version": oulu_npu.CROP_VERSION, "archive": archive.name, "archive_bytes": 11,
               "archive_mtime_ns": archive.stat().st_mtime_ns,
               "detector_sha256": file_hash(workspace / "yunet.onnx"), "opencv": cv2.__version__,
               "frames_per_video": 1, "protocol": 1, "fold": None, "pilot": False, "split": "train",
               "protocol_sha256": file_hash(data / "Protocols.tar"), "videos": 1, "frames": 1,
               "manifest_sha256": file_hash(manifest)}
    manifest.with_suffix(".json").write_text(json.dumps(summary), encoding="utf-8")

    def unexpected_run(*args):
        pytest.fail(f"already prepared split should skip crop: {args}")

    prepare_oulu_split(data, workspace, backups, "train", 1, False, unexpected_run)
    assert len(list(backups.glob("*.zip"))) == 1
    shutil.rmtree(cache)
    assert prepare_oulu_split(data, workspace, backups, "train", 1, False, unexpected_run) == manifest
    assert image.read_bytes() == b"rgb"
    assert not (workspace / "archives/Train_files.tar").exists()
