"""Audit saved Round 6 scores and frozen artifacts without inference or training."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from deepface_pad.metrics import aggregate_video_scores, evaluate_scores
from deepface_pad.round6 import DEPTH_MANIFEST, KEYS, METRICS, SOURCE_MANIFEST, depth_identity, digest, summarize


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def close(actual, expected):
    return bool(np.isclose(actual, expected, rtol=1e-10, atol=1e-12))


def verify_scores(folder, manifest, split, threshold):
    """Replay metrics and exact sample/label membership from saved score CSVs."""
    frames = pd.read_csv(folder / f"{split}_frame_scores.csv")
    wanted = manifest.loc[manifest.split == split, ["sample_id", "video_id", "label"]]
    actual = frames[["sample_id", "video_id", "label"]]
    require(not frames.sample_id.duplicated().any(), f"{split}: duplicate sample IDs")
    require(actual.sort_values("sample_id").reset_index(drop=True).equals(
        wanted.sort_values("sample_id").reset_index(drop=True)), f"{split}: wrong IDs/labels")
    require(np.isfinite(frames.score).all(), f"{split}: nonfinite scores")
    video = aggregate_video_scores(frames, "mean")
    saved = pd.read_csv(folder / f"{split}_scores.csv").sort_values("video_id").reset_index(drop=True)
    require(saved[["video_id","label"]].equals(video[["video_id","label"]])
            and np.allclose(saved.score, video.score, rtol=1e-10, atol=1e-12),
            f"{split}: video aggregation differs")
    metrics = evaluate_scores(video.label.to_numpy(), video.score.to_numpy(),
                              None if split == "val" else threshold).to_dict()
    stored = read(folder / ("metrics.json" if split == "val" else "test_metrics.json"))
    require(close(metrics["threshold"], threshold), f"{split}: threshold differs from validation")
    require(all(close(stored[k], v) for k,v in metrics.items()), f"{split}: metrics differ")
    errors = video.assign(error=(video.score >= threshold).astype(int) != video.label)
    return metrics, errors


def audit(report_dir, runs_dir, manifest_path, pretest_receipt, evidence_dir):
    report_dir, runs_dir, evidence_dir = map(Path, (report_dir, runs_dir, evidence_dir))
    manifest_path = Path(manifest_path)
    expected = read(pretest_receipt)
    frozen = read(report_dir / "comparison_freeze.json")
    registration = read(report_dir / "registration.json")
    freeze_sha = sha(report_dir / "comparison_freeze.json")
    require(freeze_sha == expected["freeze_sha256"], "freeze changed after pre-test review")
    require(expected["checks"]["no_test_artifacts_before_test"] is True, "missing pre-test review")
    require(frozen["registration_sha256"] == sha(report_dir / "registration.json"), "registration hash changed")
    require(frozen["candidate"] == "E3" and frozen["selection_source"] == "validation", "candidate changed")
    require(set(frozen["runs"]) == set(KEYS) == set(registration["configs"]), "expected exactly six runs")
    require(sha(manifest_path) == DEPTH_MANIFEST, "manifest hash differs from locked CASIA split")
    manifest = pd.read_csv(manifest_path)
    counts = manifest.groupby("split").agg(frames=("sample_id","size"), videos=("video_id","nunique"),
                                            subjects=("subject_id","nunique"))
    require(counts.to_dict() == {"frames":{"train":3840,"val":960,"test":7200},
        "videos":{"train":192,"val":48,"test":360},"subjects":{"train":16,"val":4,"test":30}}, "protocol counts changed")
    require(not (manifest.groupby("subject_id").split.nunique() > 1).any(), "subject leakage")
    require((manifest.groupby("video_id").size() == 20).all(), "expected 20 frames/video")
    result = {"status":"PASS: frozen Round 6 development-test audit", "source_commit":registration["source"]["commit"],
              "freeze_sha256":freeze_sha,"registration_sha256":sha(report_dir/"registration.json"),
              "manifest_sha256":sha(manifest_path),"environment":registration["environment"],
              "runs":{},"paired_video_errors":{},"summary":{},"paired_delta":{},
              "scope":"Saved CSV/JSON/hash audit only; no training, checkpoint inference or fresh GPU/cache audit."}
    errors, rows, val_rows = {}, [], []
    for key in KEYS:
        record = frozen["runs"][key]
        folder = runs_dir / Path(record["run"]).name
        require(all(sha(folder/name) == value for name,value in record["hashes"].items()), f"{key}: frozen hash changed")
        receipt = read(report_dir / f"{key}-test.json")
        require(receipt["freeze_sha256"] == freeze_sha, f"{key}: wrong test freeze receipt")
        require(set(receipt["hashes"]) == {"test_metrics.json","test_scores.csv","test_frame_scores.csv"}, "test receipt incomplete")
        require(all(sha(folder/name) == value for name,value in receipt["hashes"].items()), f"{key}: test output hash changed")
        cfg = yaml.safe_load((folder / "config.yaml").read_text(encoding="utf-8"))
        expected_cfg = json.loads(json.dumps(registration["configs"][key]))
        variant, seed = key.split("_")
        require(cfg["seed"] == int(seed) and cfg["source_commit"] == result["source_commit"], "seed/source mismatch")
        if variant == "E3":
            peer = "E1_"+seed
            initial = read(folder / "initial_checkpoint.json")
            require(initial == {"path":frozen["runs"][peer]["run"]+"/best.ckpt",
                                "sha256":frozen["runs"][peer]["hashes"]["best.ckpt"]}, "wrong paired initializer")
            expected_cfg["training"]["init_checkpoint"] = initial["path"]
            expected_cfg["round6_initializer_sha256"] = initial["sha256"]
        require(cfg == expected_cfg, f"{key}: config differs from registration")
        binding = read(folder / "round6_binding.json")
        require(binding == {"registration_sha256":result["registration_sha256"],
                            "environment":registration["environment"]}, "environment binding changed")
        snapshot = read(folder / "depth_input_snapshot.json")
        require(depth_identity(snapshot) == registration["depth"], "depth snapshot differs")
        require(snapshot["files"]["source_manifest"]["sha256"] == SOURCE_MANIFEST, "source manifest differs")
        log = pd.read_csv(folder / "train_log.csv")
        epochs = 30 if variant == "E1" else 16
        require(len(log) == epochs and log.epoch.tolist() == list(range(1,epochs+1)), "incomplete epochs")
        require(np.isfinite(log[["train_loss","val_loss","val_selection_loss"]].to_numpy()).all(), "nonfinite losses")
        selection = read(folder / "checkpoint_selection.json")
        require(len(selection["stages"]) == 1 and selection["reported_stage"] == "joint", "wrong stages")
        stage = selection["stages"][0]
        best = log.loc[log.val_selection_loss.idxmin()]
        require(stage["epoch"] == int(best.epoch) and close(stage["selection_value"],best.val_selection_loss), "wrong selected epoch/loss")
        require(stage["selection_metric"] == ("val_loss" if variant == "E1" else "classification_bce"), "wrong selection criterion")
        require(record["hashes"]["best.ckpt"] == record["hashes"]["best_stage_01_joint.ckpt"], "stage checkpoint differs")
        threshold = read(folder / "threshold.json")
        require(threshold["source"] == "validation", "threshold source is not validation")
        val, _ = verify_scores(folder, manifest, "val", threshold["threshold"])
        test, errors[key] = verify_scores(folder, manifest, "test", threshold["threshold"])
        counts_test = errors[key].label.value_counts().to_dict()
        require(counts_test == {0:270,1:90}, "wrong test class denominators")
        result["runs"][key] = {"run_id":folder.name,"epochs_trained":epochs,"checkpoint_selection":stage,
            "validation":val,"test":test,"attack_videos":270,"live_videos":90,
            "false_accepts":int(errors[key].query('label == 0').error.sum()),
            "false_rejects":int(errors[key].query('label == 1').error.sum()),
            "hashes":{**record["hashes"],**receipt["hashes"]}}
        rows.append({"variant":variant,"seed":int(seed),"run":folder.name,**test})
        val_rows.append({"key":key,"run":folder.name,"selected_epoch":stage["epoch"],"selection_loss":stage["selection_value"],**val})
        # Local recovery copies contain reviewed metadata/score CSVs, no weights or images.
        target = evidence_dir / folder.name
        target.mkdir(parents=True, exist_ok=True)
        for name in (*record["hashes"], *receipt["hashes"]):
            if name.endswith(".ckpt") or name == "depth_input_snapshot.json":
                continue
            shutil.copy2(folder/name, target/name)
        shutil.copy2(report_dir/f"{key}-test.json", target/"test_receipt.json")
    frame = pd.DataFrame(rows)
    summary, paired = summarize(frame)
    saved = pd.read_csv(report_dir / "development-test.csv")
    require(saved[["variant","seed","run"]].equals(frame[["variant","seed","run"]]), "development-test run set/order differs")
    require(np.allclose(saved[["threshold",*METRICS]],frame[["threshold",*METRICS]],rtol=1e-10,atol=1e-12), "development-test metrics differ")
    val_saved = pd.read_csv(report_dir/"validation.csv").set_index("key")
    for row in val_rows:
        stored = val_saved.loc[row["key"]]
        require(stored["run"] == row["run"] and stored["selected_epoch"] == row["selected_epoch"], "validation table run differs")
        require(all(close(stored[m],row[m]) for m in ("selection_loss","threshold",*METRICS)), "validation table values differ")
    saved_summary = pd.read_csv(report_dir/"summary-mean-sample-sd.csv",header=[0,1],index_col=0)
    require(saved_summary.columns.equals(summary.columns) and saved_summary.index.equals(summary.index)
            and np.allclose(saved_summary,summary,rtol=1e-10,atol=1e-12), "mean/sample SD table differs")
    saved_paired = pd.read_csv(report_dir/"paired-video-acer.csv",index_col=0)
    require(saved_paired.index.equals(paired.index) and saved_paired.columns.equals(paired.columns)
            and np.allclose(saved_paired,paired,rtol=1e-10,atol=1e-12), "paired table differs")
    require(all(close(read(report_dir/"paired-summary.json")[k],v) for k,v in paired.attrs.items()), "paired mean/SD differs")
    for seed in (43,44,45):
        joined = errors[f"E1_{seed}"].merge(errors[f"E3_{seed}"],on=["video_id","label"],suffixes=("_E1","_E3"),validate="one_to_one")
        a,b = joined.error_E1,joined.error_E3
        result["paired_video_errors"][str(seed)] = {"corrected":int((a & ~b).sum()),"new_errors":int((~a & b).sum()),
            "both_wrong":int((a & b).sum()),"both_correct":int((~a & ~b).sum())}
    result["summary"] = {variant:{m:{"mean":float(summary.loc[variant,(m,"mean")]),"sample_sd_ddof1":float(summary.loc[variant,(m,"std")])}
        for m in METRICS} for variant in ("E1","E3")}
    result["paired_delta"] = {"definition":"video ACER E3 - E1; stored as rate, multiply by 100 for percentage points",
        "by_seed":{str(s):float(paired.loc[s,"delta_E3_minus_E1"]) for s in (43,44,45)},**paired.attrs}
    result["reviewed_hashes"] = {name:sha(report_dir/name) for name in (
        "comparison_freeze.json","registration.json","development-test.csv","validation.csv",
        "summary-mean-sample-sd.csv","paired-video-acer.csv","paired-summary.json")}
    for name in result["reviewed_hashes"]:
        shutil.copy2(report_dir/name,evidence_dir/name)
    shutil.copy2(manifest_path,evidence_dir/manifest_path.name)
    result["pretest_receipt_sha256"] = sha(pretest_receipt)
    result["depth_artifact_list_digest"] = digest(registration["depth"]["artifacts"])
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--reports",type=Path,required=True)
    p.add_argument("--runs",type=Path,required=True)
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--pretest-receipt",type=Path,required=True)
    p.add_argument("--evidence",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args = p.parse_args()
    result = audit(args.reports,args.runs,args.manifest,args.pretest_receipt,args.evidence)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:result[k] for k in ("status","summary","paired_delta","paired_video_errors")},indent=2))
