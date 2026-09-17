from __future__ import annotations

import argparse
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
from deepface_pad.face.quality import check_enrollment_quality  # noqa: E402
from deepface_pad.face.recognizer import ArcFaceONNXEmbedder  # noqa: E402
from deepface_pad.utils.config import load_config, resolve_project_path  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Enroll a face from multiple frames")
    parser.add_argument("--person-id", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--config", default="configs/demo.yaml")
    parser.add_argument("--source")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config(PROJECT_ROOT / args.config)
    detector = build_detector(config["detector"], PROJECT_ROOT)
    rec = config["recognition"]
    enrollment = config["enrollment"]
    embedder = ArcFaceONNXEmbedder(
        model_path=resolve_project_path(rec["model_path"], PROJECT_ROOT),
        model_version=rec["model_version"],
        device=config["detector"]["device"],
    )
    gallery_path = resolve_project_path(rec["gallery_path"], PROJECT_ROOT)
    gallery = FaceGallery.load(gallery_path)
    source = args.source if args.source is not None else config["camera"]["source"]
    source = int(source) if str(source).isdecimal() else source
    capture = cv2.VideoCapture(source)
    if not capture.isOpened():
        raise RuntimeError(f"Cannot open camera/video source: {source}")

    embeddings = []
    target = int(enrollment["target_samples"])
    last_sample_ms = 0.0
    status = "Show exactly one clear face"
    try:
        while len(embeddings) < target:
            ok, frame = capture.read()
            if not ok:
                break
            if config["camera"].get("mirror", True):
                frame = cv2.flip(frame, 1)
            detections = detector.detect(frame)
            if len(detections) != 1:
                status = "Need exactly one face"
            else:
                face = detections[0]
                crop = align_face(frame, face.landmarks_5)
                quality = check_enrollment_quality(
                    crop,
                    face,
                    int(rec["min_face_size"]),
                    float(rec["blur_threshold"]),
                    float(enrollment["min_detection_confidence"]),
                )
                current_ms = time.monotonic() * 1000
                interval_ok = current_ms - last_sample_ms >= float(
                    enrollment["min_sample_interval_ms"]
                )
                if quality.accepted and interval_ok:
                    embeddings.append(embedder.embed(crop))
                    last_sample_ms = current_ms
                    status = f"Captured {len(embeddings)}/{target}"
                elif not quality.accepted:
                    status = f"Rejected: {quality.reason} (blur={quality.blur:.0f})"
                draw_detection(frame, face, f"{face.confidence:.2f}")
            draw_hud(frame, [status, "Move head slightly | q: cancel", "Raw frames are not saved"])
            cv2.imshow("DeepFace-PAD Enrollment", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                return 1
    finally:
        capture.release()
        cv2.destroyAllWindows()

    if len(embeddings) < target:
        raise RuntimeError(f"Source ended after only {len(embeddings)}/{target} samples")
    entry = gallery.enroll(
        args.person_id, args.name, embeddings, embedder.model_version
    )
    gallery.save(gallery_path)
    print(
        f"Enrolled {entry.display_name} ({entry.person_id}) from "
        f"{entry.sample_count} samples into {gallery_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
