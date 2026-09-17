from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import cv2

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from deepface_pad.face.detector import build_detector  # noqa: E402
from deepface_pad.utils.config import load_config  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Headless camera stability smoke test; saves no frames")
    parser.add_argument("--config", default="configs/demo.yaml")
    parser.add_argument("--duration", type=float, default=300.0)
    parser.add_argument("--source")
    args = parser.parse_args()
    if args.duration <= 0:
        raise ValueError("duration must be positive")
    config = load_config(PROJECT_ROOT / args.config)
    detector = build_detector(config["detector"], PROJECT_ROOT)
    raw_source = args.source if args.source is not None else config["camera"]["source"]
    source = int(raw_source) if str(raw_source).isdecimal() else raw_source
    capture = cv2.VideoCapture(source)
    if not capture.isOpened():
        raise RuntimeError(f"Cannot open camera/video source: {source}")
    started, frames, faces, failures = time.perf_counter(), 0, 0, 0
    try:
        while time.perf_counter() - started < args.duration:
            ok, frame = capture.read()
            if not ok:
                failures += 1
                if failures >= 10:
                    raise RuntimeError("Camera returned 10 consecutive unreadable frames")
                continue
            failures = 0
            frames += 1
            faces += len(detector.detect(frame))
    finally:
        capture.release()
    elapsed = time.perf_counter() - started
    print(
        f"PASS duration={elapsed:.1f}s frames={frames} faces={faces} "
        f"effective_fps={frames / elapsed:.2f} raw_frames_saved=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

