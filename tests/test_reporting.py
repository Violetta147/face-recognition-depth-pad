import pytest

from deepface_pad.reporting import select_depth_cases


def test_select_depth_cases_prioritises_errors_and_borderline_correct():
    rows = [
        {"sample_id": "wrong-far", "score": 0.1, "threshold": 0.8, "correct": False},
        {"sample_id": "wrong-near", "score": 0.7, "threshold": 0.8, "correct": False},
        {"sample_id": "correct-near", "score": 0.81, "threshold": 0.8, "correct": True},
        {"sample_id": "correct-far", "score": 0.99, "threshold": 0.8, "correct": True},
    ]

    selected = select_depth_cases(rows, 3)

    assert [row["sample_id"] for row in selected] == [
        "wrong-far",
        "correct-near",
        "correct-far",
    ]


def test_select_depth_cases_rejects_nonpositive_count():
    with pytest.raises(ValueError, match="positive"):
        select_depth_cases([], 0)
