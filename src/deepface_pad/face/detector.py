from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any, Protocol

import cv2
import numpy as np

from .types import FaceDetection


class Detector(Protocol):
    def detect(self, frame_bgr: np.ndarray) -> list[FaceDetection]: ...


class SCRFDDetector:
    """SCRFD ONNX inference without the compile-time InsightFace dependency."""

    def __init__(
        self,
        model_path: str | Path,
        device: str = "cpu",
        detection_size: Sequence[int] = (640, 640),
        confidence_threshold: float = 0.6,
    ) -> None:
        try:
            import onnxruntime as ort
        except ImportError as exc:
            raise RuntimeError("Install with `uv sync --extra runtime`.") from exc
        model_path = Path(model_path)
        if not model_path.is_file():
            raise FileNotFoundError(
                f"SCRFD model not found: {model_path}. Run scripts/download_models.py"
            )
        if len(detection_size) != 2:
            raise ValueError("detection_size must contain width and height")
        available = ort.get_available_providers()
        providers = (
            ["CUDAExecutionProvider", "CPUExecutionProvider"]
            if device.lower().startswith("cuda") and "CUDAExecutionProvider" in available
            else ["CPUExecutionProvider"]
        )
        session_options = ort.SessionOptions()
        # Official SCRFD files retain 640x640 output annotations even though the
        # graph supports smaller input; hide those harmless shape warnings.
        session_options.log_severity_level = 3
        self._session = ort.InferenceSession(
            str(model_path), sess_options=session_options, providers=providers
        )
        self._input_name = self._session.get_inputs()[0].name
        self._output_names = [item.name for item in self._session.get_outputs()]
        self._size = tuple(map(int, detection_size))
        self.confidence_threshold = float(confidence_threshold)
        self._center_cache: dict[tuple[int, int, int], np.ndarray] = {}

    def detect(self, frame_bgr: np.ndarray) -> list[FaceDetection]:
        _validate_frame(frame_bgr)
        input_w, input_h = self._size
        image_h, image_w = frame_bgr.shape[:2]
        ratio = min(input_w / image_w, input_h / image_h)
        resized_w, resized_h = int(image_w * ratio), int(image_h * ratio)
        canvas = np.zeros((input_h, input_w, 3), dtype=np.uint8)
        canvas[:resized_h, :resized_w] = cv2.resize(frame_bgr, (resized_w, resized_h))
        blob = cv2.dnn.blobFromImage(
            canvas, 1.0 / 128.0, self._size, (127.5, 127.5, 127.5), swapRB=True
        )
        outputs = self._session.run(self._output_names, {self._input_name: blob})
        scores, boxes, keypoints = self._decode(outputs)
        results: list[FaceDetection] = []
        for index in self._nms(boxes, scores, 0.4):
            box = boxes[index] / ratio
            points = keypoints[index] / ratio
            box[[0, 2]] = np.clip(box[[0, 2]], 0, image_w - 1)
            box[[1, 3]] = np.clip(box[[1, 3]], 0, image_h - 1)
            points[:, 0] = np.clip(points[:, 0], 0, image_w - 1)
            points[:, 1] = np.clip(points[:, 1], 0, image_h - 1)
            results.append(FaceDetection(box, points, float(scores[index])))
        return results

    def _decode(self, outputs: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        feature_maps = 3
        if len(outputs) not in {9, 15}:
            raise RuntimeError(f"Unexpected SCRFD output count: {len(outputs)}")
        all_scores, all_boxes, all_points = [], [], []
        for level, stride in enumerate((8, 16, 32)):
            raw_scores = outputs[level].reshape(-1)
            raw_boxes = outputs[level + feature_maps].reshape(-1, 4) * stride
            raw_points = outputs[level + feature_maps * 2].reshape(-1, 10) * stride
            height, width = self._size[1] // stride, self._size[0] // stride
            key = (height, width, stride)
            centers = self._center_cache.get(key)
            if centers is None:
                grid_x, grid_y = np.meshgrid(np.arange(width), np.arange(height))
                centers = np.stack((grid_x, grid_y), axis=-1).astype(np.float32)
                centers = np.repeat((centers * stride).reshape(-1, 2), 2, axis=0)
                self._center_cache[key] = centers
            positive = np.where(raw_scores >= self.confidence_threshold)[0]
            if positive.size == 0:
                continue
            center, distance = centers[positive], raw_boxes[positive]
            all_scores.append(raw_scores[positive])
            all_boxes.append(
                np.column_stack(
                    (
                        center[:, 0] - distance[:, 0],
                        center[:, 1] - distance[:, 1],
                        center[:, 0] + distance[:, 2],
                        center[:, 1] + distance[:, 3],
                    )
                )
            )
            all_points.append(raw_points[positive].reshape(-1, 5, 2) + center[:, None, :])
        if not all_scores:
            return np.empty(0), np.empty((0, 4)), np.empty((0, 5, 2))
        return np.concatenate(all_scores), np.vstack(all_boxes), np.vstack(all_points)

    @staticmethod
    def _nms(boxes: np.ndarray, scores: np.ndarray, threshold: float) -> list[int]:
        order, keep = scores.argsort()[::-1], []
        while order.size:
            current = int(order[0])
            keep.append(current)
            if order.size == 1:
                break
            rest = order[1:]
            xx1 = np.maximum(boxes[current, 0], boxes[rest, 0])
            yy1 = np.maximum(boxes[current, 1], boxes[rest, 1])
            xx2 = np.minimum(boxes[current, 2], boxes[rest, 2])
            yy2 = np.minimum(boxes[current, 3], boxes[rest, 3])
            intersection = np.maximum(0, xx2 - xx1) * np.maximum(0, yy2 - yy1)
            area_current = max(0, boxes[current, 2] - boxes[current, 0]) * max(0, boxes[current, 3] - boxes[current, 1])
            area_rest = np.maximum(0, boxes[rest, 2] - boxes[rest, 0]) * np.maximum(0, boxes[rest, 3] - boxes[rest, 1])
            iou = intersection / np.maximum(area_current + area_rest - intersection, 1e-9)
            order = rest[iou <= threshold]
        return keep


def build_detector(config: dict[str, Any], project_root: Path | None = None) -> Detector:
    backend = str(config.get("backend", "onnx_scrfd")).lower()
    if backend != "onnx_scrfd":
        raise ValueError(f"Unsupported detector backend: {backend}")
    model_path = Path(config["model_path"])
    if project_root is not None and not model_path.is_absolute():
        model_path = project_root / model_path
    return SCRFDDetector(
        model_path,
        str(config.get("device", "cpu")),
        config.get("detection_size", (640, 640)),
        float(config.get("confidence_threshold", 0.6)),
    )


def _validate_frame(frame_bgr: np.ndarray) -> None:
    if not isinstance(frame_bgr, np.ndarray) or frame_bgr.ndim != 3 or frame_bgr.shape[2] != 3 or not frame_bgr.size:
        raise ValueError("frame_bgr must be a non-empty HxWx3 NumPy array")
