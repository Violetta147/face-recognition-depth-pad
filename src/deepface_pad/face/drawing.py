from __future__ import annotations

import cv2
import numpy as np

from .types import FaceDetection


def draw_detection(
    frame: np.ndarray,
    detection: FaceDetection,
    label: str,
    color: tuple[int, int, int] = (40, 210, 40),
) -> None:
    x1, y1, x2, y2 = np.rint(detection.bbox_xyxy).astype(int)
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    for x, y in np.rint(detection.landmarks_5).astype(int):
        cv2.circle(frame, (x, y), 2, (0, 220, 255), -1)
    baseline_y = max(20, y1 - 8)
    cv2.putText(
        frame,
        label,
        (x1, baseline_y),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        color,
        2,
        cv2.LINE_AA,
    )


def draw_hud(frame: np.ndarray, lines: list[str]) -> None:
    height = 16 + 26 * len(lines)
    overlay = frame.copy()
    cv2.rectangle(overlay, (8, 8), (410, height), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.65, frame, 0.35, 0, dst=frame)
    for index, line in enumerate(lines):
        cv2.putText(
            frame,
            line,
            (18, 32 + index * 26),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.62,
            (245, 245, 245),
            1,
            cv2.LINE_AA,
        )

