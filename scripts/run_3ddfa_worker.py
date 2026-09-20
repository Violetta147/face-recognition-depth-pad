"""Run the resumable pseudo-depth queue with an official 3DDFA V2 checkout."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

from deepface_pad.depth_jobs import process_pending_depth_jobs


def write_worker_metadata(
    destination: Path,
    root: Path,
    config: Path,
    *,
    onnx: bool,
    mode: str,
    output_size: int,
) -> dict[str, object]:
    try:
        commit = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError(f"cannot determine 3DDFA V2 git commit: {exc}") from exc
    payload: dict[str, object] = {
        "schema_version": 1,
        "implementation": "cleardusk/3DDFA_V2",
        "git_commit": commit,
        "config_file": config.name,
        "config_sha256": hashlib.sha256(config.read_bytes()).hexdigest(),
        "backend": "onnx" if onnx else "pytorch",
        "mode": mode,
        "output_size": output_size,
    }
    if destination.is_file():
        existing = json.loads(destination.read_text(encoding="utf-8"))
        if existing != payload:
            raise RuntimeError(
                f"worker metadata changed during a resumable queue: {destination}"
            )
        return payload
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(destination)
    return payload


def build_reconstructor(root: Path, config: Path, *, onnx: bool, mode: str):
    root = root.resolve()
    config = config.resolve()
    if not (root / "TDDFA.py").is_file():
        raise FileNotFoundError(f"not a 3DDFA_V2 checkout: {root}")
    sys.path.insert(0, str(root))
    # The official project stores model paths relative to its repository root.
    os.chdir(root)

    import cv2
    import yaml
    from utils.depth import depth as render_depth

    cfg = yaml.safe_load(config.read_text(encoding="utf-8"))
    if onnx:
        from FaceBoxes.FaceBoxes_ONNX import FaceBoxes_ONNX
        from TDDFA_ONNX import TDDFA_ONNX

        face_boxes = FaceBoxes_ONNX()
        tddfa = TDDFA_ONNX(**cfg)
    else:
        from FaceBoxes import FaceBoxes
        from TDDFA import TDDFA

        face_boxes = FaceBoxes()
        tddfa = TDDFA(gpu_mode=mode == "gpu", **cfg)

    def reconstruct(image_path: Path) -> np.ndarray:
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"cannot read image: {image_path}")
        boxes = face_boxes(image)
        if boxes is None or len(boxes) == 0:
            raise ValueError("no face detected")
        box = max(boxes, key=lambda item: max(0.0, item[2] - item[0]) * max(0.0, item[3] - item[1]))
        parameters, roi_boxes = tddfa(image, [box])
        vertices = tddfa.recon_vers(parameters, roi_boxes, dense_flag=True)[0]
        rendered = render_depth(
            image,
            [vertices],
            tddfa.tri,
            show_flag=False,
            with_bg_flag=False,
        )
        return rendered.astype(np.float32).mean(axis=2)

    return reconstruct


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--pending", required=True, help="3ddfa_pending.csv")
parser.add_argument("--ledger", required=True, help="depth_status.csv")
parser.add_argument("--3ddfa-root", dest="three_ddfa_root", required=True, help="official cleardusk/3DDFA_V2 checkout")
parser.add_argument("--config", help="3DDFA config; default: <3ddfa-root>/configs/mb1_120x120.yml")
parser.add_argument("--onnx", action="store_true", help="use FaceBoxes and TDDFA ONNX runtimes")
parser.add_argument("--mode", choices=["cpu", "gpu"], default="gpu")
parser.add_argument("--limit", type=int, help="process only N pending samples for a smoke test")
parser.add_argument("--output-size", type=int, default=32)
parser.add_argument("--failure-report", help="write failed sample_id,error rows")
parser.add_argument("--metadata", help="worker metadata JSON; default: <ledger>.worker.json")
args = parser.parse_args()

pending = Path(args.pending).resolve()
ledger = Path(args.ledger).resolve()
failure_report = Path(args.failure_report).resolve() if args.failure_report else None
root = Path(args.three_ddfa_root).resolve()
config = Path(args.config).resolve() if args.config else root / "configs" / "mb1_120x120.yml"
metadata = Path(args.metadata).resolve() if args.metadata else ledger.with_suffix(ledger.suffix + ".worker.json")
write_worker_metadata(
    metadata,
    root,
    config,
    onnx=args.onnx,
    mode=args.mode,
    output_size=args.output_size,
)
summary = process_pending_depth_jobs(
    pending,
    ledger,
    build_reconstructor(root, config, onnx=args.onnx, mode=args.mode),
    failure_report=failure_report,
    output_size=args.output_size,
    limit=args.limit,
)
print(", ".join(f"{key}={value}" for key, value in summary.items()))
