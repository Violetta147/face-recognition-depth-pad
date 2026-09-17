from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class FaceDetection:
    """A detector result in coordinates of the original frame."""

    bbox_xyxy: np.ndarray
    landmarks_5: np.ndarray
    confidence: float

    def __post_init__(self) -> None:
        box = np.asarray(self.bbox_xyxy, dtype=np.float32)
        landmarks = np.asarray(self.landmarks_5, dtype=np.float32)
        if box.shape != (4,):
            raise ValueError("bbox_xyxy must have shape (4,)")
        if landmarks.shape != (5, 2):
            raise ValueError("landmarks_5 must have shape (5, 2)")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be in [0, 1]")
        object.__setattr__(self, "bbox_xyxy", box)
        object.__setattr__(self, "landmarks_5", landmarks)

    @property
    def width(self) -> float:
        return max(0.0, float(self.bbox_xyxy[2] - self.bbox_xyxy[0]))

    @property
    def height(self) -> float:
        return max(0.0, float(self.bbox_xyxy[3] - self.bbox_xyxy[1]))


@dataclass(frozen=True)
class RecognitionResult:
    person_id: str | None
    display_name: str | None
    similarity: float | None
    is_unknown: bool

