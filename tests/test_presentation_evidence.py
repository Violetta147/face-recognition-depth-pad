import json
from pathlib import Path

import pytest


@pytest.fixture
def evidence():
    path = Path(__file__).resolve().parents[1] / "reports/rounds1_4_presentation_content.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_presentation_metrics_agree_with_video_error_counts(evidence):
    for model in evidence["results"]:
        apcer = 100 * model["false_accepts"] / evidence["paired_errors"]["attack_videos"]
        bpcer = 100 * model["false_rejects"] / evidence["paired_errors"]["live_videos"]
        assert model["apcer"] == pytest.approx(apcer, abs=0.0001)
        assert model["bpcer"] == pytest.approx(bpcer, abs=0.0001)
        assert model["acer"] == pytest.approx((apcer + bpcer) / 2, abs=0.0001)
    paired = evidence["paired_errors"]
    assert sum(paired[key] for key in ("both_correct", "both_wrong", "fixed_by_e2", "new_error_e2")) == 360
    assert len(evidence["false_rejected_videos"]) == paired["both_wrong"]
    for row in evidence["false_rejected_videos"]:
        assert row["e1"] < evidence["results"][1]["threshold"]
        assert row["e2"] < evidence["results"][2]["threshold"]


def test_presentation_cost_units_and_coverage(evidence):
    e1, e2 = evidence["efficiency"]
    assert e2["parameters"] - e1["parameters"] == 1265
    for row in evidence["efficiency"]:
        assert row["fps"] == pytest.approx(1000 / row["p50_ms"], abs=0.001)
    assert [slide["id"] for slide in evidence["slides"]] == list(range(1, evidence["total_slides"] + 1))
    assert all(slide["notes"] for slide in evidence["slides"])
    assert sum(slide["time_seconds"] for slide in evidence["slides"]) <= 15 * 60
    assert all("OFFICIAL" in evidence["runs"][name] for name in ("E1", "E2"))
