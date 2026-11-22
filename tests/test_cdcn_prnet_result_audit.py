import hashlib
import json
from pathlib import Path
import sys

import pandas as pd
import pytest

from deepface_pad.oulu_npu import expected_ids

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_cdcn_prnet_locked_result import audit, checked_scores
from audit_cdc_n_p1_scores import score
sys.path.pop(0)


@pytest.fixture
def result_source(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    frames = {}
    for split, name in (("val", "dev"), ("test", "test")):
        records = [{"video_id": f"{p}_{s}_{u:02}_{a}", "label": int(a == 1),
                    "score": 0.8 if a == 1 else 0.1}
                   for p, s, u, a in sorted(expected_ids(1, None, split))]
        frames[name] = pd.DataFrame(records)
        frames[name].to_csv(source / f"{name}_scores.csv", index=False)
    evaluated = score(frames["dev"], frames["test"])
    report = {"mode": "full", "train_videos": 1200, "dev_videos": 900, "dev_frames_per_video": 8,
              "seed": 43, "batch": 56, "history": [{"epoch": 1}],
              "checkpoint_sha256": "checkpoint", "assets_manifest_sha256": "assets",
              "dev": evaluated["dev"] | {"threshold_from_dev": evaluated["threshold_from_dev"]}}
    (source / "pilot_result.json").write_text(json.dumps(report))
    sha = lambda name: hashlib.sha256((source / name).read_bytes()).hexdigest()
    lock = {"protocol": 1, "training_run": "test-run", "epoch": 1, "seed": 43, "batch": 56,
            "checkpoint_sha256": "checkpoint", "assets_manifest_sha256": "assets",
            "threshold_from_dev": evaluated["threshold_from_dev"],
            "dev_report_sha256": sha("pilot_result.json")}
    (source / "test_lock.json").write_text(json.dumps(lock))
    metrics = lock | {"split": "Test", "videos": 600, "frames_per_video": 8,
                      "test": evaluated["test"], "test_scores_sha256": sha("test_scores.csv")}
    (source / "test_metrics.json").write_text(json.dumps(metrics))
    return source


def test_audit_recomputes_locked_results_and_groups(result_source, tmp_path):
    output = tmp_path / "audit"
    result = audit(result_source, output)
    assert result["status"] == "verified"
    # Strict > rejects the live scores equal to the saved ROC threshold.
    assert result["test"]["live_rejected"] == 120
    assert result["test"]["attack_accepted"] == 0
    assert len(result["by_phone"]) == 6
    assert len(result["by_subject"]) == 20
    assert len(pd.read_csv(output / "test_errors.csv")) == 120
    assert result["by_access"][0]["apcer_pooled"] is None


def test_audit_rejects_replaced_scores_and_changed_lock(result_source, tmp_path):
    scores = result_source / "test_scores.csv"
    scores.write_bytes(scores.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="source hash"):
        audit(result_source, tmp_path / "audit")
    lock_path = result_source / "test_lock.json"
    lock = json.loads(lock_path.read_text()) | {"threshold_from_dev": 0.5}
    lock_path.write_text(json.dumps(lock))
    with pytest.raises(ValueError, match="frozen lock"):
        audit(result_source, tmp_path / "audit")


def test_score_membership_and_labels_are_checked(result_source):
    path = result_source / "test_scores.csv"
    frame = pd.read_csv(path)
    frame.loc[0, "label"] = 0
    frame.to_csv(path, index=False)
    with pytest.raises(ValueError, match="Labels conflict"):
        checked_scores(path, "test")
    frame.iloc[1:].to_csv(path, index=False)
    with pytest.raises(ValueError, match="membership"):
        checked_scores(path, "test")
