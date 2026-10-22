import pytest
from deepface_pad.webcam import MedianGate, yunet_boxes

BOX = (0,0,100,100)


def test_median_window_ttd_and_validation_threshold_equality():
    gate = MedianGate(.5,3)
    assert gate.update(.9,BOX,1.,1.1)["state"] == "collecting"
    assert gate.update(.5,BOX,1.2,1.3)["state"] == "collecting"
    result = gate.update(.1,BOX,1.4,1.6)
    assert result["state"] == "live" and result["median_score"] == .5
    assert result["first_decision_seconds"] == pytest.approx(.6)
    result = gate.update(.1,BOX,1.7,1.8)
    assert result["state"] == "attack" and result["first_decision_seconds"] is None


@pytest.mark.parametrize("reason",["no_face","multiple","gap","switch","nan"])
def test_resets_cannot_inherit_live_window(reason):
    gate = MedianGate(.5,3)
    for t in (0.,.1,.2): gate.update(.9,BOX,t,t+.01)
    score, box, count, t = .9, BOX, 1, .3
    if reason == "no_face": count,box = 0,None
    if reason == "multiple": count = 2
    if reason == "gap": t = 2.
    if reason == "switch": box = (300,300,100,100)
    if reason == "nan": score = float("nan")
    result = gate.update(score,box,t,t+.01,count)
    assert result["state"] != "live"
    assert result["window_count"] < 3
    assert result["first_decision_seconds"] is None


def test_clock_and_config_rejected():
    with pytest.raises(ValueError): MedianGate(.5,4)
    gate = MedianGate(.5,3)
    gate.update(.9,BOX,1.,1.1)
    with pytest.raises(ValueError,match="clock"): gate.update(.9,BOX,.9,1.)
    with pytest.raises(ValueError,match="timestamps"): gate.update(.9,BOX,2.,1.)


def test_yunet_mapping_clips_and_excludes_invalid_boxes():
    assert yunet_boxes(None,640,480,320) == []
    boxes = yunet_boxes([[10,20,100,200],[-10,-10,40,40],[400,20,10,10],
                         [10,10,-1,20],[float("nan"),0,1,1]],640,480,320)
    assert boxes == [(20,30,200,300),(0,0,60,45)]


def test_cpu_gap_accepts_slow_forwards_but_missing_face_still_resets():
    gate = MedianGate(.5,3,maximum_gap=5.)
    for t in (0.,2.): assert gate.update(.9,BOX,t,t+1.8)["state"] == "collecting"
    result = gate.update(.9,BOX,4.,5.8)
    assert result["state"] == "live"
    assert result["first_decision_seconds"] == pytest.approx(5.8)
    assert gate.update(None,None,6.,6.1,0)["state"] == "no_face"
    assert gate.update(.9,BOX,8.,9.8)["state"] == "collecting"
