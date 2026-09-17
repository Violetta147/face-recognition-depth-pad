from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .aligner import blur_score
from .types import FaceDetection


@dataclass(frozen=True)
class QualityResult:
    accepted: bool
    reason: str | None
    blur: float


def check_enrollment_quality(
    aligned_face: np.ndarray,
    detection: FaceDetection,
    min_face_size: int,
    min_blur: float,
    min_confidence: float,
) -> QualityResult:
    score = blur_score(aligned_face)
    if detection.confidence < min_confidence:
        return QualityResult(False, "LOW_CONFIDENCE", score)
    if min(detection.width, detection.height) < min_face_size:
        return QualityResult(False, "FACE_TOO_SMALL", score)
    if score < min_blur:
        return QualityResult(False, "TOO_BLURRY", score)
    return QualityResult(True, None, score)

