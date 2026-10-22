"""Fail-closed median-window state and a measured, single-face webcam demo."""
from __future__ import annotations

from collections import deque
import math
from statistics import median


def yunet_boxes(detections, width, height, side):
    """Map YuNet's square detector input back to the original camera frame."""
    boxes = []
    if detections is None:
        return boxes
    for row in detections:
        if not all(math.isfinite(float(x)) for x in row[:4]):
            continue
        x,y,w,h = map(float,row[:4])
        if w <= 0 or h <= 0:
            continue
        x0, y0 = max(0, math.floor(x*width/side)), max(0, math.floor(y*height/side))
        x1, y1 = min(width, math.ceil((x+w)*width/side)), min(height, math.ceil((y+h)*height/side))
        if x1 > x0 and y1 > y0:
            boxes.append((x0,y0,x1-x0,y1-y0))
    return boxes


def box_iou(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    intersection = max(0, min(ax+aw,bx+bw)-max(ax,bx)) * max(0, min(ay+ah,by+bh)-max(ay,by))
    union = aw*ah + bw*bh - intersection
    return intersection/union if union > 0 else 0.


class MedianGate:
    """Reset on missing/multiple faces, geometry change, invalid score or gap.

    Geometry continuity is a heuristic, not proof of identity continuity.
    First-decision time starts at the first eligible capture read call.
    """
    def __init__(self, threshold, window=5, maximum_gap=1., minimum_iou=.4):
        if window < 1 or window % 2 != 1 or not 0 <= threshold <= 1:
            raise ValueError("odd positive window and probability threshold required")
        if maximum_gap <= 0 or not 0 <= minimum_iou <= 1:
            raise ValueError("invalid tracking configuration")
        self.threshold, self.window = threshold, window
        self.maximum_gap, self.minimum_iou = maximum_gap, minimum_iou
        self.episode = 0
        self.clock = None
        self.reset()

    def reset(self):
        self.scores = deque(maxlen=self.window)
        self.box = self.last_at = self.started_at = None
        self.decided = False

    def update(self, score, box, captured_at, finished_at, face_count=1):
        if not math.isfinite(captured_at) or not math.isfinite(finished_at) or finished_at < captured_at:
            raise ValueError("invalid timestamps")
        if self.clock is not None and captured_at < self.clock:
            raise ValueError("nonmonotonic capture clock")
        self.clock = captured_at
        if face_count != 1 or box is None:
            self.reset()
            return self.result("no_face" if face_count == 0 else "multiple_faces")
        if score is None or not math.isfinite(score) or not 0 <= score <= 1:
            self.reset()
            return self.result("invalid_score")
        if self.box is not None and (captured_at-self.last_at > self.maximum_gap or box_iou(self.box,box) < self.minimum_iou):
            self.reset()
        if self.started_at is None:
            self.started_at = captured_at
            self.episode += 1
        self.box, self.last_at = box, captured_at
        self.scores.append(float(score))
        if len(self.scores) < self.window:
            return self.result("collecting")
        value = median(self.scores)
        first = not self.decided
        self.decided = True
        return self.result("live" if value >= self.threshold else "attack", value,
                           finished_at-self.started_at if first else None)

    def result(self, state, value=None, ttd=None):
        return {"state":state, "median_score":value, "window_count":len(self.scores),
                "episode":self.episode, "first_decision_seconds":ttd}
