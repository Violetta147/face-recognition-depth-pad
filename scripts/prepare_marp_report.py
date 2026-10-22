"""Prepare local, portable Marp assets without changing the source evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET
import zipfile


ROOT = Path(__file__).resolve().parents[1]
NS = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main",
      "a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
FIGURES = {
    "pipeline.png": "01_pipeline.png",
    "dataset.png": "03_dataset_split.png",
    "schedule.png": "02_training_schedule.png",
    "test_error_rates.png": "06_test_error_rates.png",
    "paired_errors.png": "12_paired_errors.png",
    "quality_errors.png": "13_quality_errors.png",
    "test_metrics.png": "05_test_metrics.png",
    "roc.png": "07_ROC.png",
    "error_matrix.png": "14_error_video_matrix.png",
}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def clean_template(source: Path, destination: Path):
    """Remove sample content, retain the supplied masters' background artwork."""
    with zipfile.ZipFile(source) as zin, zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            content = zin.read(item.filename)
            is_slide = item.filename.startswith("ppt/slides/slide")
            is_layout = item.filename.startswith(("ppt/slideLayouts/slideLayout", "ppt/slideMasters/slideMaster"))
            if item.filename.endswith(".xml") and (is_slide or is_layout):
                root = ET.fromstring(content)
                tree = root.find("p:cSld/p:spTree", NS)
                if tree is not None:
                    for shape in list(tree):
                        kind = shape.tag.rsplit("}", 1)[-1]
                        if is_slide and kind not in ("nvGrpSpPr", "grpSpPr"):
                            tree.remove(shape)
                        elif is_layout and shape.findall(".//a:t", NS):
                            tree.remove(shape)
                content = ET.tostring(root, encoding="utf-8", xml_declaration=True)
            zout.writestr(item, content)


def prepare(root=ROOT):
    root = Path(root)
    deck = root / "reports/slides_round5"
    assets = deck / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    sources = {name: root / "artifacts/figure-notebook-20261016/numeric-final/png" / file
               for name, file in FIGURES.items()}
    sources.update({
        "cdcn_architecture.png": root / "diagrams/Sơ đồ kiến trúc CDCN đa tỉ lệ.png",
        "head_architecture.png": root / "diagrams/Kiến trúc CDCN cải tiến với Learned Depth Head.png",
        "case_s32_v2.png": root / "artifacts/figure-notebook-20261016/qualitative-preview/png/17_case_01_casia_s32_v2.png",
    })
    missing = [str(p) for p in sources.values() if not p.is_file()]
    if missing:
        raise FileNotFoundError("Missing verified figure inputs:\n" + "\n".join(missing))
    manifest = {"source_template": "reports/Template-DUT-Total.pptx",
                "template_sha256": digest(root / "reports/Template-DUT-Total.pptx"),
                "image_processing": "Exact byte copies. No crop, recolor or contrast changes.",
                "figures": []}
    for name, source in sources.items():
        target = assets / name
        shutil.copy2(source, target)
        manifest["figures"].append({"asset": name, "source": source.relative_to(root).as_posix(),
                                    "sha256": digest(source)})
    work = root / "artifacts/marp-report-20261016"
    work.mkdir(parents=True, exist_ok=True)
    clean_template(root / "reports/Template-DUT-Total.pptx", work / "DUT-backgrounds-only.pptx")
    (assets / "provenance.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Prepared {len(sources)} unchanged figure assets in {assets}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    prepare()
