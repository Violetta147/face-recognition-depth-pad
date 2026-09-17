from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ThresholdReport:
    threshold: float
    true_accept_rate: float
    true_reject_rate: float
    balanced_accuracy: float


def select_threshold(scores: np.ndarray, genuine: np.ndarray) -> ThresholdReport:
    values = np.asarray(scores, dtype=np.float64).reshape(-1)
    labels = np.asarray(genuine, dtype=bool).reshape(-1)
    if values.size == 0 or values.size != labels.size:
        raise ValueError("scores and genuine must be non-empty and have equal length")
    if labels.all() or (~labels).all():
        raise ValueError("Both genuine and impostor comparisons are required")
    candidates = np.unique(
        np.concatenate(([values.min() - 1e-6], values, [values.max() + 1e-6]))
    )
    best: ThresholdReport | None = None
    for threshold in candidates:
        accepted = values >= threshold
        tar = float(accepted[labels].mean())
        trr = float((~accepted[~labels]).mean())
        report = ThresholdReport(float(threshold), tar, trr, (tar + trr) / 2.0)
        if best is None or (report.balanced_accuracy, report.threshold) > (
            best.balanced_accuracy,
            best.threshold,
        ):
            best = report
    assert best is not None
    return best

