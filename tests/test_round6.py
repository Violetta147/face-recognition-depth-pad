import copy
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import torch
import yaml

import deepface_pad.round6 as r6

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def batch(tmp_path, monkeypatch):
    output = tmp_path / "output"
    output.mkdir()
    manifest = tmp_path / "manifest.csv"
    rows = [{"sample_id": f"{split}_{i}", "video_id": f"{split}_v{i//2}",
             "label": i//2, "split": split} for split in ("val", "test") for i in range(4)]
    pd.DataFrame(rows).to_csv(manifest, index=False)
    snapshot = {"files": {"manifest": "locked"}, "depth_audit": {"artifact_checksums": []}}
    reg = {"environment": {"gpu": "fixture"}, "configs": {}, "depth": r6.depth_identity(snapshot)}
    folders = {}
    for key in r6.KEYS:
        cfg = yaml.safe_load((ROOT / f"configs/round6/{key}.yaml").read_text())
        cfg["data"]["manifest"] = str(manifest)
        cfg["runs_dir"] = str(tmp_path / "runs")
        reg["configs"][key] = cfg
        folders[key] = tmp_path / "runs" / f"{cfg['experiment_id']}_seed{cfg['seed']}_fixture"
    b = r6.Batch(tmp_path, output)
    r6.immutable_json(b.registration_path, reg)
    monkeypatch.setattr(b, "current", lambda **kw: copy.deepcopy(reg))
    for key in r6.KEYS:
        folder = folders[key]
        folder.mkdir(parents=True)
        cfg = copy.deepcopy(reg["configs"][key])
        is_e3 = key.startswith("E3_")
        metric = "classification_bce" if is_e3 else "val_loss"
        epochs = 16 if is_e3 else 30
        if is_e3:
            initial = folders["E1_" + str(cfg["seed"])] / "best.ckpt"
            cfg["training"]["init_checkpoint"] = str(initial)
            cfg["round6_initializer_sha256"] = r6.manifest_checksum(initial)
            r6.immutable_json(folder / "initial_checkpoint.json", {
                "path": str(initial), "sha256": r6.manifest_checksum(initial)})
        (folder / "config.yaml").write_text(yaml.safe_dump(cfg))
        (folder / "environment.txt").write_text("fixture")
        r6.immutable_json(folder / "round6_binding.json", {
            "registration_sha256": r6.manifest_checksum(b.registration_path),
            "environment": reg["environment"]})
        r6.immutable_json(folder / "depth_input_snapshot.json", snapshot)
        r6.immutable_json(folder / "manifest_checksum.json", {"sha256": r6.DEPTH_MANIFEST})
        log = pd.DataFrame({"stage": ["joint"]*epochs, "epoch": range(1, epochs+1),
                            "train_loss": [1.]*epochs, "val_loss": [1.]*epochs,
                            "val_selection_loss": np.arange(epochs, 0, -1, dtype=float)})
        log.to_csv(folder / "train_log.csv", index=False)
        selected = {"epoch": epochs, "selection_metric": metric, "selection_value": 1.}
        r6.immutable_json(folder / "checkpoint_selection.json", {
            "reported_stage": "joint", "stages": [selected]})
        torch.save({"model": {}, "config": cfg, **selected}, folder / "best.ckpt")
        shutil.copyfile(folder / "best.ckpt", folder / "best_stage_01_joint.ckpt")
        frames = pd.DataFrame(rows[:4]).drop(columns="split")
        frames["score"] = [.1, .2, .8, .9]
        frames.to_csv(folder / "val_frame_scores.csv", index=False)
        video = r6.aggregate_video_scores(frames)
        video.to_csv(folder / "val_scores.csv", index=False)
        metrics = r6.evaluate_scores(video.label.to_numpy(), video.score.to_numpy()).to_dict()
        r6.immutable_json(folder / "metrics.json", metrics)
        r6.immutable_json(folder / "threshold.json", {"source": "validation", "threshold": metrics["threshold"]})
        r6.immutable_json(output / f"{key}-run.json", {"run": str(folder)})
    return b, reg, folders


def test_six_templates_preserve_historical_hyperparameters_and_new_seeds():
    for key in r6.KEYS:
        cfg = yaml.safe_load((ROOT / f"configs/round6/{key}.yaml").read_text())
        variant, seed = key.split("_")
        base = yaml.safe_load((ROOT / "configs" / (
            "casia_e1_cdcn_official.yaml" if variant == "E1" else "casia_e3_joint_bce.yaml")).read_text())
        assert cfg.pop("seed") == int(seed) in r6.SEEDS
        assert cfg.pop("experiment_id") == "ROUND6_" + base.pop("experiment_id")
        base.pop("seed")
        base["training"].pop("init_checkpoint", None)
        if variant == "E3":
            assert cfg.pop("round6_initializer") == "E1_" + seed
        assert cfg == base
    assert json.loads((ROOT / "configs/round6/depth_reference.json").read_text())["count"] == 12000


def test_train_and_test_gates_closed_without_touching_files(tmp_path):
    b = r6.Batch(tmp_path, tmp_path)
    with pytest.raises(ValueError, match="RUN_TRAIN"):
        b.train_pair(43)
    with pytest.raises(ValueError, match="OPEN_TEST"):
        b.test()


def test_exact_six_run_freeze_and_paired_initializer(batch):
    b, reg, folders = batch
    assert set(b.freeze()["runs"]) == set(r6.KEYS)
    assert b.verify_freeze() == b.freeze()
    for seed in r6.SEEDS:
        cfg = b.config_for(f"E3_{seed}", folders, reg)
        assert cfg["training"]["init_checkpoint"] == str(folders[f"E1_{seed}"] / "best.ckpt")


@pytest.mark.parametrize("fault", ["seed", "initializer", "log", "selection", "threshold", "depth", "environment", "frame"])
def test_freeze_rejects_wrong_or_stale_artifacts(batch, fault):
    b, reg, folders = batch
    folder = folders["E3_44"]
    if fault == "seed":
        cfg = yaml.safe_load((folder / "config.yaml").read_text())
        cfg["training"]["init_checkpoint"] = str(folders["E1_43"] / "best.ckpt")
        (folder / "config.yaml").write_text(yaml.safe_dump(cfg))
    elif fault == "initializer":
        (folder / "initial_checkpoint.json").write_text(json.dumps({"path":"wrong", "sha256":"wrong"}))
    elif fault == "log":
        log = pd.read_csv(folder / "train_log.csv").iloc[:-1]
        log.to_csv(folder / "train_log.csv", index=False)
    elif fault == "selection":
        p = r6.read(folder / "checkpoint_selection.json")
        p["stages"][0]["epoch"] = 1
        (folder / "checkpoint_selection.json").write_text(json.dumps(p))
    elif fault == "threshold":
        (folder / "threshold.json").write_text('{"threshold":0.1,"source":"test"}')
    elif fault == "depth":
        (folder / "depth_input_snapshot.json").write_text('{"files":{},"depth_audit":{"artifact_checksums":[]}}')
    elif fault == "environment":
        (folder / "round6_binding.json").write_text('{}')
    else:
        frames = pd.read_csv(folder / "val_frame_scores.csv")
        frames.loc[0, "sample_id"] = "test_leak"
        frames.to_csv(folder / "val_frame_scores.csv", index=False)
    with pytest.raises(ValueError):
        b.freeze()
    assert not b.freeze_path.exists()


def test_freeze_requires_all_six_and_no_test_before_freeze(batch):
    b, _, folders = batch
    pointer = b.output / "E3_45-run.json"
    payload = pointer.read_text()
    pointer.unlink()
    with pytest.raises(FileNotFoundError):
        b.freeze()
    pointer.write_text(payload)
    (folders["E1_43"] / "test_scores.csv").write_text("premature")
    with pytest.raises(ValueError, match="before"):
        b.freeze()


def test_freeze_detects_changed_checkpoint_and_partial_test(batch):
    b, _, folders = batch
    b.freeze()
    (folders["E1_43"] / "test_scores.csv").write_text("partial")
    with pytest.raises(ValueError, match="partial"):
        b.test(allow_test=True)
    (folders["E1_43"] / "test_scores.csv").unlink()
    with (folders["E1_43"] / "best.ckpt").open("ab") as stream:
        stream.write(b"changed")
    with pytest.raises(ValueError, match="checkpoint"):
        b.verify_freeze()


def test_source_lock_and_immutable_records(tmp_path):
    p = tmp_path / "source.py"
    p.write_text("locked")
    (tmp_path / "SOURCE_COMMIT.txt").write_text("a"*40)
    lock = {"commit":"a"*40, "files":{"source.py":r6.manifest_checksum(p)}}
    r6.immutable_json(tmp_path / "SOURCE_LOCK.json", lock)
    assert r6.verify_source(tmp_path) == lock
    with pytest.raises(ValueError, match="immutable"):
        r6.immutable_json(tmp_path / "SOURCE_LOCK.json", {})
    p.write_text("changed")
    with pytest.raises(ValueError, match="source changed"):
        r6.verify_source(tmp_path)


def test_current_rejects_environment_drift(tmp_path, monkeypatch):
    b = r6.Batch(tmp_path, tmp_path)
    r6.immutable_json(b.registration_path, {"source":{}, "environment":{"cuda":"old"}})
    monkeypatch.setattr(r6, "verify_source", lambda root: {})
    monkeypatch.setattr(r6, "environment", lambda: {"cuda":"new"})
    with pytest.raises(ValueError, match="environment"):
        b.current(inspect_depth=False)


def test_summary_sample_sd_paired_delta_and_negative_result():
    rows = pd.DataFrame([{"variant":v, "seed":s, **{m: x for m in r6.METRICS}}
                         for s, a, b in [(43,.01,.04),(44,.02,.05),(45,.06,.03)]
                         for v,x in [("E1",a),("E3",b)]])
    summary, paired = r6.summarize(rows)
    assert summary.loc["E1", ("acer","std")] == pytest.approx(np.std([.01,.02,.06], ddof=1))
    assert paired.delta_E3_minus_E1.tolist() == pytest.approx([.03,.03,-.03])
    assert paired.attrs["delta_mean"] == pytest.approx(.01)  # retain unfavorable mean
    assert paired.attrs["delta_sample_sd_ddof1"] == pytest.approx(np.std([.03,.03,-.03],ddof=1))
    with pytest.raises(ValueError, match="all six"):
        r6.summarize(rows.iloc[:-1])


def test_registration_checks_real_manifest_counts_and_depth_reference(tmp_path, monkeypatch):
    root = tmp_path / "source"
    shutil.copytree(ROOT / "configs/round6", root / "configs/round6")
    manifests = root / "data/manifests"
    manifests.mkdir(parents=True)
    source = manifests / "casia_fasd_debug.csv"
    derived = manifests / "casia_fasd_debug_with_depth.csv"
    source.write_text("fixed source")
    rows = []
    for split, subjects in [("train",16),("val",4),("test",30)]:
        for subject in range(subjects):
            for video in range(12):
                for frame in range(20):
                    rows.append({"split":split,"subject_id":f"{split}_{subject}",
                        "video_id":f"{split}_{subject}_{video}",
                        "sample_id":f"{split}_{subject}_{video}_{frame}"})
    pd.DataFrame(rows).to_csv(derived, index=False)
    monkeypatch.setattr(r6, "SOURCE_MANIFEST", r6.manifest_checksum(source))
    monkeypatch.setattr(r6, "DEPTH_MANIFEST", r6.manifest_checksum(derived))
    monkeypatch.setattr(r6, "verify_source", lambda root: {"commit":"f"*40})
    monkeypatch.setattr(r6, "environment", lambda: {"gpu":"CPU fixture only"})
    snapshot = {"files":{}, "depth_audit":{"artifact_checksums":[]}}
    monkeypatch.setattr(r6, "inspect_training_inputs", lambda cfg: (True, snapshot))
    reference = root / "configs/round6/depth_reference.json"
    reference.write_text(json.dumps({"artifact_digest":r6.digest([])}))
    b = r6.Batch(root, tmp_path / "output")
    reg = b.register(tmp_path / "data", tmp_path / "runs")
    assert reg == b.register(tmp_path / "data", tmp_path / "runs")
    assert len(reg["configs"]) == 6 and reg["epochs"] == 138
    assert b.current() == reg
    snapshot["depth_audit"]["artifact_checksums"].append({"changed":True})
    with pytest.raises(ValueError, match="cache"):
        b.register(tmp_path / "data", tmp_path / "runs")
    snapshot["depth_audit"]["artifact_checksums"].clear()
    source.write_text("changed source")
    with pytest.raises(ValueError, match="source manifest"):
        b.register(tmp_path / "data", tmp_path / "runs")


def test_all_six_test_outputs_are_receipted_and_reuse_is_verified(batch, monkeypatch):
    b, _, folders = batch
    b.freeze()
    scored = []
    def fake_score(command, **kwargs):
        # Synthetic scoring fixture; never runs inference or a CASIA checkpoint.
        folder = Path(command[command.index("--run-dir")+1])
        scored.append(folder)
        cfg = yaml.safe_load((folder / "config.yaml").read_text())
        mf = pd.read_csv(cfg["data"]["manifest"])
        frames = mf[mf.split == "test"].drop(columns="split").copy()
        frames["score"] = [.1,.2,.8,.9]
        frames.to_csv(folder / "test_frame_scores.csv", index=False)
        video = r6.aggregate_video_scores(frames)
        video.to_csv(folder / "test_scores.csv", index=False)
        threshold = r6.read(folder / "threshold.json")["threshold"]
        metrics = r6.evaluate_scores(video.label.to_numpy(), video.score.to_numpy(), threshold).to_dict()
        (folder / "test_metrics.json").write_text(json.dumps(metrics))
    monkeypatch.setattr(r6.subprocess, "run", fake_score)
    rows = b.test(allow_test=True)
    assert len(scored) == len(rows) == 6
    pd.testing.assert_frame_equal(rows, b.test(allow_test=True))
    assert len(scored) == 6
    receipt = b.output / "E3_45-test.json"
    receipt.write_text('{}')
    with pytest.raises(ValueError, match="immutable"):
        b.test(allow_test=True)
