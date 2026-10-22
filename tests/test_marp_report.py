"""Evidence and portability checks for the Markdown research deck."""
import importlib.util
import json
from pathlib import Path
import re
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "reports/slides_round5/Bao_cao_DeepFace_PAD.md"
spec = importlib.util.spec_from_file_location("prepare_marp_report", ROOT / "scripts/prepare_marp_report.py")
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)


class TestMarpReport(unittest.TestCase):
    def test_no_html_parser_required_for_powerpoint(self):
        text = SOURCE.read_text(encoding="utf-8")
        visible = re.sub(r"<!--.*?-->", "", text, flags=re.S)
        self.assertNotRegex(visible, r"</?[A-Za-z][^>]*>")
        self.assertGreaterEqual(len(re.findall(r"(?m)^> ", text)), 18)
        renderer = (ROOT / "scripts/render_marp_report.ps1").read_text(encoding="utf-8")
        self.assertNotIn("--html", renderer)

    def setUp(self):
        self.text = SOURCE.read_text(encoding="utf-8")
        self.body = self.text.partition("\n---\n")[2]

    def test_complete_deck_and_speaker_notes(self):
        slides = self.body.split("\n---\n")
        self.assertEqual(len(slides), 22)
        for slide in slides:
            self.assertRegex(slide, r"(?m)^#{1,2} ")
            self.assertIn("<!--", slide)
        for kind in ["content", "cover", "closing"]:
            self.assertIn(f'url("assets/dut-{kind}.png")', self.text)

    def test_local_image_dependencies_and_provenance(self):
        images = re.findall(r"!\[[^\]]*\]\((assets/[^)]+)\)", self.text)
        self.assertEqual(len(images), 12)
        self.assertEqual(len(set(images)), 12)
        manifest = json.loads((SOURCE.parent / "assets/provenance.json").read_text(encoding="utf-8"))
        for item in manifest["figures"]:
            with self.subTest(asset=item["asset"]):
                self.assertEqual(prepare.digest(SOURCE.parent / "assets" / item["asset"]), item["sha256"])
                self.assertEqual(prepare.digest(ROOT / item["source"]), item["sha256"])
        self.assertEqual(prepare.digest(ROOT / manifest["source_template"]), manifest["template_sha256"])

    def test_test_results_match_visible_summary(self):
        audit = json.loads((ROOT / "reports/ROUND_5_TEST_RESULTS_2026-10-16.json").read_text(encoding="utf-8"))
        self.assertEqual(audit["selected_by_validation"], "E3")
        for name in ["E1", "E2", "E3", "E3b", "E4"]:
            run = audit["runs"][name]
            formatted = f'{run["metrics"]["acer"] * 100:.2f}'.replace(".", ",") + "%"
            self.assertIn(formatted, self.body)
            self.assertEqual(run["attack_videos"], 270)
            self.assertEqual(run["live_videos"], 90)

    def test_selection_and_depth_metrics_match_visible_tables(self):
        audit = json.loads((ROOT / "reports/ROUND_5_FULL_VALIDATION_2026-10-16.json").read_text(encoding="utf-8"))
        self.assertEqual(audit["selected_variant"], "E3")
        for run in audit["runs"].values():
            value = run["checkpoint"]["selection_value"]
            self.assertIn(f"{value:.6f}".replace(".", ","), self.body)
            classes = run["depth_validation"]["by_class"]
            values = [classes["attack"]["frame_mean_mae_full"], classes["live"]["frame_mean_mae_full"],
                      classes["live"]["pixel_weighted_mae_target_mask"]]
            for value in values:
                self.assertIn(f"{value:.5f}".replace(".", ","), self.body)

    def test_material_limits_are_visible(self):
        visible = re.sub(r"<!--.*?-->", "", self.body, flags=re.S)
        for required in ["một seed", "test phát triển", "chưa giảm ACER", "trước test",
                         "không phải cm", "Một frame", "ngưỡng validation", "Sơ đồ minh họa"]:
            self.assertIn(required.lower(), visible.lower())

    def test_cleaning_preserves_backgrounds_and_source_bytes(self):
        p, a = prepare.NS["p"], prepare.NS["a"]
        xml = (f'<p:sld xmlns:p="{p}" xmlns:a="{a}"><p:cSld><p:spTree>'
               '<p:nvGrpSpPr/><p:grpSpPr/><p:sp><a:t>Sample text</a:t></p:sp>'
               '</p:spTree><p:bg/></p:cSld></p:sld>')
        with tempfile.TemporaryDirectory() as tmp:
            source, target = Path(tmp) / "source.pptx", Path(tmp) / "clean.pptx"
            with zipfile.ZipFile(source, "w") as z:
                z.writestr("ppt/slides/slide1.xml", xml)
                z.writestr("ppt/slideLayouts/slideLayout2.xml", xml)
                z.writestr("ppt/media/image1.png", b"original artwork")
            before = source.read_bytes()
            prepare.clean_template(source, target)
            self.assertEqual(source.read_bytes(), before)
            with zipfile.ZipFile(target) as z:
                self.assertEqual(z.read("ppt/media/image1.png"), b"original artwork")
                for name in ["ppt/slides/slide1.xml", "ppt/slideLayouts/slideLayout2.xml"]:
                    root = ET.fromstring(z.read(name))
                    self.assertIsNotNone(root.find("p:cSld/p:bg", prepare.NS))
                    self.assertEqual(root.findall(".//a:t", prepare.NS), [])


if __name__ == "__main__":
    unittest.main()
