import numpy as np
import pytest

from deepface_pad.face.types import FaceDetection


def test_face_detection_contract() -> None:
    item = FaceDetection(
        np.array([1, 2, 11, 22]), np.zeros((5, 2)), confidence=0.9
    )
    assert item.width == 10
    assert item.height == 20


def test_face_detection_rejects_invalid_confidence() -> None:
    with pytest.raises(ValueError):
        FaceDetection(np.zeros(4), np.zeros((5, 2)), confidence=1.1)

