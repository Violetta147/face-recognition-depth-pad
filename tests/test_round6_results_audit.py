import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("audit_round6_results", ROOT/"scripts/audit_round6_results.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


@pytest.fixture
def scores(tmp_path):
    manifest = pd.DataFrame({"sample_id":["a","b","c","d"],"video_id":["v0","v0","v1","v1"],
                             "label":[0,0,1,1],"split":["val"]*4})
    frames = manifest.drop(columns="split").assign(score=[.1,.2,.8,.9])
    video = audit.aggregate_video_scores(frames)
    metrics = audit.evaluate_scores(video.label.to_numpy(),video.score.to_numpy()).to_dict()
    frames.to_csv(tmp_path/"val_frame_scores.csv",index=False)
    video.to_csv(tmp_path/"val_scores.csv",index=False)
    (tmp_path/"metrics.json").write_text(json.dumps(metrics))
    return tmp_path,manifest,metrics["threshold"]


def test_saved_scores_replay_without_inference(scores):
    folder,manifest,threshold = scores
    metrics,errors = audit.verify_scores(folder,manifest,"val",threshold)
    assert metrics["acer"] == 0 and metrics["auc"] == 1
    assert len(errors) == 2 and errors.error.sum() == 0


@pytest.mark.parametrize("fault",["duplicate","label","aggregation","metric","threshold","nonfinite"])
def test_score_audit_rejects_changed_outputs(scores,fault):
    folder,manifest,threshold = scores
    path = folder/"val_frame_scores.csv"
    frames = pd.read_csv(path)
    if fault == "duplicate": frames.loc[1,"sample_id"] = "a"
    elif fault == "label": frames.loc[0,"label"] = 1
    elif fault == "aggregation":
        video = pd.read_csv(folder/"val_scores.csv")
        video.loc[0,"score"] = .99
        video.to_csv(folder/"val_scores.csv",index=False)
    elif fault == "metric": (folder/"metrics.json").write_text('{"threshold":0,"acer":1}')
    elif fault == "threshold": threshold = .5
    else: frames.loc[0,"score"] = np.inf
    frames.to_csv(path,index=False)
    with pytest.raises((ValueError,KeyError)):
        audit.verify_scores(folder,manifest,"val",threshold)


def test_audit_rejects_changed_freeze_before_reading_runs(tmp_path):
    (tmp_path/"comparison_freeze.json").write_text('{}')
    (tmp_path/"registration.json").write_text('{}')
    (tmp_path/"pretest.json").write_text('{"freeze_sha256":"different"}')
    with pytest.raises(ValueError,match="freeze changed"):
        audit.audit(tmp_path,tmp_path,tmp_path/"missing.csv",tmp_path/"pretest.json",tmp_path/"evidence")
