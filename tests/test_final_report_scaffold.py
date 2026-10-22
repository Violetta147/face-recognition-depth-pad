import importlib.util
import re
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET


def check_scaffold(tmp_path):
    root = Path(__file__).resolve().parents[1]
    source = root / "reports/bao_cao_cuoi_ky/ban_thao/BAO_CAO_CUOI_KY_KHUNG.md"
    content = source.read_text(encoding="utf-8")
    assert re.findall(r"<!-- PAGE (\d+) \|", content) == [f"{n:02d}" for n in range(1, 19)]
    assert "—" not in content
    spec = importlib.util.spec_from_file_location("scaffold", root / "scripts/build_final_report_scaffold.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    target = tmp_path / "report.docx"
    module.build(source, target)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    with ZipFile(target) as package:
        xml = ET.fromstring(package.read("word/document.xml"))
        styles = ET.fromstring(package.read("word/styles.xml"))
        assert not any(name.startswith("word/media/") for name in package.namelist())
    for sid in ("Normal", "Title", "Heading1", "Heading2"):
        style = styles.find(f'.//w:style[@w:styleId="{sid}"]', ns)
        assert style.find(".//w:pBdr", ns) is None
        fonts = style.find(".//w:rFonts", ns)
        assert all("theme" not in key.lower() for key in fonts.attrib)
    paragraphs = ["".join(p.itertext()) for p in xml.findall(".//w:p", ns)]
    for heading in re.findall(r"^#{1,2} (.+)$", content, re.M):
        assert heading in paragraphs
    assert len(xml.findall('.//w:br[@w:type="page"]', ns)) == 17
    assert len(xml.findall(".//w:tbl", ns)) == 10
    assert 'TOC \\o "1-1"' in " ".join(xml.itertext())
    assert "[Điền]" in " ".join(xml.itertext())


class FinalReportScaffoldTest(unittest.TestCase):
    def test_complete_editable_report_without_fabricated_results(self):
        with tempfile.TemporaryDirectory() as temp:
            check_scaffold(Path(temp))

    def test_report_workspace_links_survive_file_moves(self):
        root = Path(__file__).resolve().parents[1]
        workspace = root / "reports/bao_cao_cuoi_ky"
        for source in (root / "README.md", workspace / "README.md"):
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", source.read_text(encoding="utf-8")):
                if "://" in target or target.startswith("#"):
                    continue
                with self.subTest(source=source.name, target=target):
                    self.assertTrue((source.parent / target.split("#", 1)[0]).exists())


if __name__ == "__main__":
    unittest.main()
