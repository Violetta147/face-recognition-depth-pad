from __future__ import annotations

import cv2
import numpy as np


# ArcFace canonical five-point template for a 112x112 crop.
ARCFACE_TEMPLATE_112 = np.array(
    [
        [38.2946, 51.6963],
        [73.5318, 51.5014],
        [56.0252, 71.7366],
        [41.5493, 92.3655],
        [70.7299, 92.2041],
    ],
    dtype=np.float32,
)


def align_face(
    frame_bgr: np.ndarray, landmarks_5: np.ndarray, output_size: int = 112
) -> np.ndarray:
    """Similarity-align a face using left/right eye, nose and mouth corners."""

    if output_size <= 0:
        raise ValueError("output_size must be positive")
    landmarks = np.asarray(landmarks_5, dtype=np.float32)
    if landmarks.shape != (5, 2):
        raise ValueError("landmarks_5 must have shape (5, 2)")
    if frame_bgr.ndim != 3 or frame_bgr.shape[2] != 3:
        raise ValueError("frame_bgr must be a three-channel image")

    target = ARCFACE_TEMPLATE_112 * (output_size / 112.0)
    transform, _ = cv2.estimateAffinePartial2D(
        landmarks, target, method=cv2.LMEDS
    )
    if transform is None:
        raise ValueError("Unable to estimate alignment transform")
    return cv2.warpAffine(
        frame_bgr,
        transform,
        (output_size, output_size),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0,
    )


def blur_score(image_bgr: np.ndarray) -> float:
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())

