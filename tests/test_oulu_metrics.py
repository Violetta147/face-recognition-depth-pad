import pandas as pd
import pytest

from deepface_pad.oulu_metrics import oulu_metrics


def test_worst_attack_group_and_frozen_threshold():
    frame = pd.DataFrame({
        "video_id": ["a", "b", "c", "d", "e", "f"],
        "label": [1, 1, 0, 0, 0, 0],
        "score": [.8, .4, .9, .1, .2, .3],
        "attack_type": ["live", "live", "print1", "print2", "replay1", "replay2"],
    })
    result = oulu_metrics(frame, .5)
    assert result["apcer"] == .5 and result["apcer_pooled"] == .25
    assert result["bpcer"] == .5 and result["acer"] == .5
    assert result["counts"]["print_accepted"] == 1
    assert result["counts"]["replay_accepted"] == 0
    assert oulu_metrics(frame)["threshold"] == .4
    with pytest.raises(ValueError, match="finite"):
        oulu_metrics(frame, float("nan"))
    with pytest.raises(ValueError, match="binary"):
        oulu_metrics(frame.assign(label=[1, .5, 0, 0, 0, 0]))
