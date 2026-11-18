import base64
import io
import json
from pathlib import Path
import sys
import tarfile
from types import SimpleNamespace

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
