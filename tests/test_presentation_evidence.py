import json
import os
from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZipFile

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


def test_exported_deck_preserves_results_notes_and_editable_tables(evidence):
    root = Path(__file__).resolve().parents[1]
    deck = Path(os.environ.get("PAD_REPORT_PPTX", root / "artifacts/presentations/DeepFace_PAD_Bao_cao_03-10-2026.pptx"))
    if not deck.is_file():
        pytest.skip("Presentation binary is local and ignored because it contains biometric pixels")
    ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
    with ZipFile(deck) as package:
        slides = [ElementTree.fromstring(package.read(f"ppt/slides/slide{n}.xml")) for n in range(1, 23)]
        notes = [ElementTree.fromstring(package.read(f"ppt/notesSlides/notesSlide{n}.xml")) for n in range(1, 23)]
    text = lambda xml: " ".join(node.text or "" for node in xml.findall(".//a:t", ns))
    assert all(author in text(slides[0]) for author in evidence["authors"])
    assert sum(len(slide.findall(".//a:tbl", ns)) for slide in slides) == 9
    for result in evidence["results"]:
        assert f'{result["auc"]:.6f}' in text(slides[9])
    for video in evidence["false_rejected_videos"]:
        assert video["video"] in text(slides[11])
    for spec, note in zip(evidence["slides"], notes):
        assert spec["notes"] in text(note)
