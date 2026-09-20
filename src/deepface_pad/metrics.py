from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class PadMetrics:
    threshold: float
    apcer: float
    bpcer: float
    acer: float
    eer: float
    auc: float

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


def aggregate_video_scores(
    frame_scores: pd.DataFrame, method: str = "mean"
) -> pd.DataFrame:
    required = {"video_id", "label", "score"}
    missing = required.difference(frame_scores.columns)
    if missing:
        raise ValueError(f"Missing score columns: {sorted(missing)}")
    if method not in {"mean", "median"}:
        raise ValueError("aggregation must be 'mean' or 'median'")
    label_counts = frame_scores.groupby("video_id")["label"].nunique()
    if (label_counts > 1).any():
        bad = label_counts[label_counts > 1].index.tolist()
        raise ValueError(f"Videos contain conflicting labels: {bad[:5]}")
    grouped = frame_scores.groupby("video_id", sort=True)
    scores = grouped["score"].mean() if method == "mean" else grouped["score"].median()
    return pd.DataFrame(
        {
            "video_id": scores.index,
            "label": grouped["label"].first().to_numpy(),
            "score": scores.to_numpy(),
        }
    ).reset_index(drop=True)


def error_rates(labels: np.ndarray, scores: np.ndarray, threshold: float) -> tuple[float, float, float]:
    labels = np.asarray(labels, dtype=int)
    scores = np.asarray(scores, dtype=float)
    if labels.shape != scores.shape or labels.ndim != 1:
        raise ValueError("labels and scores must be equally sized 1-D arrays")
    if not np.isin(labels, [0, 1]).all() or not np.isfinite(scores).all():
        raise ValueError("labels must be binary and scores finite")
    attacks, live = labels == 0, labels == 1
    if not attacks.any() or not live.any():
        raise ValueError("both attack and bona fide samples are required")
    apcer = float(np.mean(scores[attacks] >= threshold))
    bpcer = float(np.mean(scores[live] < threshold))
    return apcer, bpcer, (apcer + bpcer) / 2.0


def _thresholds(scores: np.ndarray) -> np.ndarray:
    unique = np.unique(np.asarray(scores, dtype=float))
    return np.r_[np.nextafter(unique[0], -np.inf), unique, np.nextafter(unique[-1], np.inf)]


def select_threshold(labels: np.ndarray, scores: np.ndarray) -> float:
    candidates = _thresholds(scores)
    rows = [(error_rates(labels, scores, float(t))[2], abs(error_rates(labels, scores, float(t))[0] - error_rates(labels, scores, float(t))[1]), float(t)) for t in candidates]
    return min(rows)[2]


def roc_auc(labels: np.ndarray, scores: np.ndarray) -> float:
    labels = np.asarray(labels, dtype=int)
    scores = np.asarray(scores, dtype=float)
    positive = scores[labels == 1]
    negative = scores[labels == 0]
    if not len(positive) or not len(negative):
        raise ValueError("both classes are required")
    wins = sum(np.sum(p > negative) + 0.5 * np.sum(p == negative) for p in positive)
    return float(wins / (len(positive) * len(negative)))


def equal_error_rate(labels: np.ndarray, scores: np.ndarray) -> float:
    rates = [error_rates(labels, scores, float(t))[:2] for t in _thresholds(scores)]
    apcer, bpcer = min(rates, key=lambda x: abs(x[0] - x[1]))
    return float((apcer + bpcer) / 2.0)


def evaluate_scores(labels: np.ndarray, scores: np.ndarray, threshold: float | None = None) -> PadMetrics:
    labels, scores = np.asarray(labels), np.asarray(scores)
    threshold = select_threshold(labels, scores) if threshold is None else float(threshold)
    apcer, bpcer, acer = error_rates(labels, scores, threshold)
    return PadMetrics(threshold, apcer, bpcer, acer, equal_error_rate(labels, scores), roc_auc(labels, scores))
