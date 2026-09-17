from __future__ import annotations

import argparse
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKS = {
    "buffalo_s": ("det_500m.onnx", "w600k_mbf.onnx"),
    "buffalo_l": ("det_10g.onnx", "w600k_r50.onnx"),
}


def safe_extract(archive: zipfile.ZipFile, destination: Path) -> None:
    root = destination.resolve()
    for member in archive.infolist():
        target = (destination / member.filename).resolve()
        if root not in target.parents and target != root:
            raise ValueError(f"Unsafe archive member: {member.filename}")
    archive.extractall(destination)


def main() -> int:
    parser = argparse.ArgumentParser(description="Download an official InsightFace ONNX model pack")
    parser.add_argument("--pack", choices=sorted(PACKS), default="buffalo_s")
    parser.add_argument("--url", help="Override the official model-pack URL")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    url = args.url or f"https://github.com/deepinsight/insightface/releases/download/v0.7/{args.pack}.zip"
    destination = PROJECT_ROOT / "artifacts/models" / args.pack
    required = [destination / filename for filename in PACKS[args.pack]]
    if all(path.is_file() for path in required) and not args.force:
        print(f"Models already present in {destination}")
        return 0
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="deepface-pad-model-") as temporary:
        archive_path = Path(temporary) / f"{args.pack}.zip"
        print(f"Downloading {url}")
        with urllib.request.urlopen(url, timeout=120) as response, archive_path.open("wb") as output:
            shutil.copyfileobj(response, output)
        with zipfile.ZipFile(archive_path) as archive:
            safe_extract(archive, destination)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(f"Model archive is missing required files: {missing}")
    print(f"Installed SCRFD and ArcFace models in {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
