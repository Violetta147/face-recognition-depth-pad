from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .metrics import aggregate_video_scores, evaluate_scores


def evaluate_file(scores_path: str | Path, output_path: str | Path, threshold: float | None = None, aggregation: str = "mean") -> dict[str, float]:
    scores = pd.read_csv(scores_path)
    if scores["video_id"].duplicated().any():
        scores = aggregate_video_scores(scores, aggregation)
    metrics = evaluate_scores(scores.label.to_numpy(), scores.score.to_numpy(), threshold).to_dict()
    Path(output_path).write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics
