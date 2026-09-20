import numpy as np
import pandas as pd

from deepface_pad.metrics import aggregate_video_scores, error_rates, evaluate_scores


def test_hand_calculated_error_rates():
    labels = np.array([0, 0, 1, 1])
    scores = np.array([0.2, 0.8, 0.4, 0.9])
    assert error_rates(labels, scores, 0.5) == (0.5, 0.5, 0.5)


def test_perfect_metrics():
    result = evaluate_scores(np.array([0, 0, 1, 1]), np.array([0.1, 0.2, 0.8, 0.9]))
    assert result.acer == 0
    assert result.eer == 0
    assert result.auc == 1


def test_video_aggregation():
    frame = pd.DataFrame({"video_id": ["a", "a", "b", "b"], "label": [0, 0, 1, 1], "score": [0.1, 0.3, 0.7, 0.9]})
    result = aggregate_video_scores(frame)
    assert result.score.tolist() == [0.2, 0.8]
