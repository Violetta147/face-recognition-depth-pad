from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

import cv2

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from deepface_pad.face.aligner import align_face  # noqa: E402
from deepface_pad.face.detector import build_detector  # noqa: E402
from deepface_pad.face.drawing import draw_detection, draw_hud  # noqa: E402
from deepface_pad.face.gallery import FaceGallery  # noqa: E402
from deepface_pad.face.recognizer import ArcFaceONNXEmbedder  # noqa: E402
from deepface_pad.utils.config import load_config, resolve_project_path  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Buoi 1/2 real-time face demo")
    parser.add_argument("--config", default="configs/demo.yaml")
    parser.add_argument(
        "--source", help="Camera index or video path; overrides config camera.source"
    )
    parser.add_argument(
        "--detect-only", action="store_true", help="Run the Buoi 1 detector demo"
    )
    return parser.parse_args()


def capture_source(raw: object) -> int | str:
    text = str(raw)
    return int(text) if text.isdecimal() else text


def main() -> int:
    args = parse_args()
    config = load_config(PROJECT_ROOT / args.config)
    camera_config = config["camera"]
    detector = build_detector(config["detector"], PROJECT_ROOT)
    recognition_config = config["recognition"]
    detect_only = args.detect_only
    gallery = FaceGallery()
    embedder = None
    if not detect_only:
        gallery_path = resolve_project_path(
            recognition_config["gallery_path"], PROJECT_ROOT
        )
        gallery = FaceGallery.load(gallery_path)
        embedder = ArcFaceONNXEmbedder(
            model_path=resolve_project_path(recognition_config["model_path"], PROJECT_ROOT),
            model_version=recognition_config["model_version"],
            device=config["detector"]["device"],
        )

    raw_source = args.source if args.source is not None else camera_config["source"]
    capture = cv2.VideoCapture(capture_source(raw_source))
    if not capture.isOpened():
        raise RuntimeError(f"Cannot open camera/video source: {raw_source}")
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, int(camera_config["width"]))
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, int(camera_config["height"]))
    capture.set(cv2.CAP_PROP_FPS, int(camera_config["fps"]))

    smoothed_fps = 0.0
    previous = time.perf_counter()
    last_log = 0.0
    frame_number = 0
    detections = []
    detection_interval = max(1, int(config["detector"].get("interval_frames", 1)))
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            if camera_config.get("mirror", True):
                frame = cv2.flip(frame, 1)
            started = time.perf_counter()
            if frame_number % detection_interval == 0:
                detections = detector.detect(frame)
            frame_number += 1
            recognition_ms = 0.0
            recognition_events = []
            state = "NO_FACE" if not detections else "DETECTED"
            for face in detections:
                label = f"FACE {face.confidence:.2f}"
                color = (40, 210, 40)
                if embedder is not None:
                    recognition_started = time.perf_counter()
                    crop = align_face(frame, face.landmarks_5)
                    result = gallery.match(
                        embedder.embed(crop), float(recognition_config["threshold"])
                    )
                    recognition_ms += (time.perf_counter() - recognition_started) * 1000
                    score = "n/a" if result.similarity is None else f"{result.similarity:.3f}"
                    if result.is_unknown:
                        label, color = f"UNKNOWN sim={score}", (30, 80, 240)
                        state = "UNKNOWN" if state != "RECOGNIZED" else state
                    else:
                        label = f"{result.display_name} sim={score}"
                        state = "RECOGNIZED"
                    recognition_events.append(
                        {
                            "state": "UNKNOWN" if result.is_unknown else "RECOGNIZED",
                            "person_id": result.person_id,
                            "similarity": result.similarity,
                        }
                    )
                draw_detection(frame, face, label, color)

            now = time.perf_counter()
            instant_fps = 1.0 / max(now - previous, 1e-9)
            smoothed_fps = instant_fps if smoothed_fps == 0 else 0.9 * smoothed_fps + 0.1 * instant_fps
            previous = now
            if not detect_only and time.monotonic() - last_log >= 1.0:
                logging.info(
                    json.dumps(
                        {
                            "event": "recognition",
                            "state": state,
                            "faces": len(detections),
                            "recognition_latency_ms": round(recognition_ms, 2),
                            "results": recognition_events,
                        },
                        ensure_ascii=False,
                    )
                )
                last_log = time.monotonic()
            draw_hud(
                frame,
                [
                    f"State: {state}",
                    f"Faces: {len(detections)} | FPS: {smoothed_fps:.1f}",
                    f"Pipeline: {(time.perf_counter() - started) * 1000:.1f} ms | Rec: {recognition_ms:.1f} ms",
                    "Press q to quit",
                ],
            )
            cv2.imshow("DeepFace-PAD - Buoi 1 & 2", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        capture.release()
        cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
