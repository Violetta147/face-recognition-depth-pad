import numpy as np

from deepface_pad.evaluation.recognition_metrics import select_threshold


def test_threshold_separates_validation_scores() -> None:
    report = select_threshold(
        np.array([0.86, 0.91, 0.12, 0.30]),
        np.array([True, True, False, False]),
    )
    assert 0.30 < report.threshold <= 0.86
    assert report.balanced_accuracy == 1.0

