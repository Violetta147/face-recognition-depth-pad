import cv2
import numpy as np

from deepface_pad.face.aligner import ARCFACE_TEMPLATE_112, align_face


def test_alignment_returns_arcface_shape() -> None:
    image = np.zeros((140, 140, 3), dtype=np.uint8)
    for point in ARCFACE_TEMPLATE_112:
        cv2.circle(image, tuple(np.rint(point).astype(int)), 2, (255, 255, 255), -1)
    result = align_face(image, ARCFACE_TEMPLATE_112)
    assert result.shape == (112, 112, 3)
    assert result.dtype == np.uint8


def test_alignment_rejects_wrong_landmark_shape() -> None:
    image = np.zeros((112, 112, 3), dtype=np.uint8)
    try:
        align_face(image, np.zeros((4, 2), dtype=np.float32))
    except ValueError as exc:
        assert "shape" in str(exc)
    else:
        raise AssertionError("Expected invalid landmarks to fail")

