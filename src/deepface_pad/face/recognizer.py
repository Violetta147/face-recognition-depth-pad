from __future__ import annotations

from pathlib import Path
from typing import Protocol

import cv2
import numpy as np


def l2_normalize(vector: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    value = np.asarray(vector, dtype=np.float32).reshape(-1)
    norm = float(np.linalg.norm(value))
    if norm <= eps:
        raise ValueError("Cannot normalize a zero embedding")
    return value / norm


def cosine_similarity(left: np.ndarray, right: np.ndarray) -> float:
    return float(np.dot(l2_normalize(left), l2_normalize(right)))


class Embedder(Protocol):
    @property
    def model_version(self) -> str: ...

    def embed(self, aligned_face_bgr: np.ndarray) -> np.ndarray: ...


class ArcFaceONNXEmbedder:
    """ArcFace ONNX inference without requiring the InsightFace Python package."""

    def __init__(
        self,
        model_path: str | Path,
        model_version: str,
        device: str = "cpu",
    ) -> None:
        try:
            import onnxruntime as ort
        except ImportError as exc:
            raise RuntimeError("Install runtime dependencies with `uv sync --extra runtime`.") from exc

        model_path = Path(model_path)
        if not model_path.is_file():
            raise FileNotFoundError(f"ArcFace model not found: {model_path}. Run scripts/download_models.py")
        available = ort.get_available_providers()
        providers = (
            ["CUDAExecutionProvider", "CPUExecutionProvider"]
            if device.lower().startswith("cuda") and "CUDAExecutionProvider" in available
            else ["CPUExecutionProvider"]
        )
        session_options = ort.SessionOptions()
        session_options.log_severity_level = 3
        self._session = ort.InferenceSession(
            str(model_path), sess_options=session_options, providers=providers
        )
        self._input_name = self._session.get_inputs()[0].name
        self._output_name = self._session.get_outputs()[0].name
        self._model_version = model_version

    @property
    def model_version(self) -> str:
        return self._model_version

    def embed(self, aligned_face_bgr: np.ndarray) -> np.ndarray:
        if aligned_face_bgr.shape[:2] != (112, 112):
            aligned_face_bgr = cv2.resize(
                aligned_face_bgr, (112, 112), interpolation=cv2.INTER_LINEAR
            )
        blob = cv2.dnn.blobFromImage(
            aligned_face_bgr, 1.0 / 127.5, (112, 112), (127.5, 127.5, 127.5), swapRB=True
        )
        feature = self._session.run([self._output_name], {self._input_name: blob})[0].reshape(-1)
        return l2_normalize(feature)
