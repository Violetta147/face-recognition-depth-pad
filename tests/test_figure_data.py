import numpy as np
import pandas as pd
import pytest

from deepface_pad.figure_data import safe_destination, verify_scores
from deepface_pad.metrics import aggregate_video_scores, evaluate_scores


def test_figure_inputs_reject_changed_threshold_and_missing_samples(tmp_path):
    frame = pd.DataFrame({"sample_id":["a","b","c","d"],"video_id":["v0","v0","v1","v1"],
                          "label":[0,0,1,1],"score":[.1,.2,.7,.8]})
    video = aggregate_video_scores(frame)
    metric = evaluate_scores(video.label.to_numpy(),video.score.to_numpy(),threshold=.5).to_dict()
    verify_scores(frame,video,frame,.5,metric)
    with pytest.raises(ValueError,match="metrics"):
        verify_scores(frame,video,frame,.9,metric)
    with pytest.raises(AssertionError):
        verify_scores(frame.iloc[:-1],video,frame,.5,metric)
    assert safe_destination(tmp_path,"depth/a.npy") == tmp_path / "depth/a.npy"
    with pytest.raises(ValueError,match="escapes"):
        safe_destination(tmp_path,"../outside.npy")


def test_restoration_rejects_existing_changed_depth_without_overwriting(tmp_path):
    from deepface_pad.figure_data import restore_selected_inputs
    (tmp_path / "rgb.png").write_bytes(b"kept")
    np.save(tmp_path / "depth.npy",np.ones((32,32),dtype=np.float32))
    rows = pd.DataFrame([{"sample_id":"a","image_path":"rgb.png","depth_path":"depth.npy","label":0}])
    before = (tmp_path / "depth.npy").read_bytes()
    with pytest.raises(ValueError,match="differs"):
        restore_selected_inputs(rows,tmp_path,"unused.zip","unused.tar",{"a":"wrong"})
    assert (tmp_path / "depth.npy").read_bytes() == before
