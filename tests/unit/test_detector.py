import numpy as np

from deepface_pad.face.detector import SCRFDDetector


def test_nms_removes_overlapping_lower_score_box() -> None:
    boxes = np.array([[0, 0, 10, 10], [1, 1, 11, 11], [30, 30, 40, 40]], dtype=float)
    scores = np.array([0.9, 0.8, 0.7])
    assert SCRFDDetector._nms(boxes, scores, 0.4) == [0, 2]


def test_nms_handles_empty_input() -> None:
    assert SCRFDDetector._nms(np.empty((0, 4)), np.empty(0), 0.4) == []
