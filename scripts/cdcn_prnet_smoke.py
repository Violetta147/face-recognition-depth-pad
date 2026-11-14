"""Reconstruct CDCN-style MTCNN/PRNet input assets for a bounded smoke set."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import importlib.metadata
from itertools import chain
import json
import math
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import types

import cv2
import numpy as np
from scipy.spatial import QhullError

from deepface_pad.progress import Progress

PRNET_COMMIT = "fc12fe5e1f1462bdea52409b213d0cf1c8cf6c5b"
DEPTH_COMMIT = "c6d10f2eb6ab962ab314f81ea4aa00af1d93dbbb"
WEIGHT_SHA = "59d338bf0c21b10be813f17f84042c9d3a5bf318e588855ff2b2c041c25bb91a"
INDEX_SHA = "cb88192fcf744b8e26d1ea6a2681cd90f102a2d977ab1bac3026bdf4ce785744"
SMOKE_PACKAGES = (
    "tensorflow==2.16.2",
    "tf-keras==2.16.0",
    "tf-slim==1.1.0",
    "mtcnn==1.0.0",
    "numpy==1.26.4",
    "scikit-image==0.24.0",
    "scipy==1.17.1",
    "opencv-python-headless==4.11.0.86",
)
SMOKE_SLOTS = (0, 3, 7)
PILOT_SLOTS = tuple(range(8))


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def load_models(prnet, renderer):
    os.environ["TF_USE_LEGACY_KERAS"] = "1"
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    import tensorflow.compat.v1 as tf
    from mtcnn import MTCNN

    # TF 2.16's compatibility loader expects the old package location.
    sys.modules["tf_keras.legacy_tf_layers"] = importlib.import_module("tf_keras.src.legacy_tf_layers")
    sys.modules["tf_keras.legacy_tf_layers.normalization"] = importlib.import_module(
        "tf_keras.src.legacy_tf_layers.normalization"
    )
    detector = MTCNN(device="CPU:0")
    session_graph = tf.Graph()
    with session_graph.as_default():
        # Load the pinned predictor with a TF1-in-TF2 compatibility import.
        path = prnet / "predictor.py"
        code = path.read_text(encoding="utf-8").replace(
            "import tensorflow as tf\nimport tensorflow.contrib.layers as tcl\nfrom tensorflow.contrib.framework import arg_scope",
            "import tensorflow.compat.v1 as tf\nimport tf_slim as tcl\nfrom tf_slim import arg_scope",
        ).replace("num_outputs/2", "num_outputs//2")
        predictor = types.ModuleType("predictor")
        sys.modules["predictor"] = predictor
        sys.path.insert(0, str(prnet))
        try:
            exec(compile(code, str(path), "exec"), predictor.__dict__)
            from api import PRN
            model = PRN(is_dlib=False, prefix=str(prnet))
        finally:
            sys.path.pop(0)
            sys.modules.pop("predictor", None)
    render = types.ModuleType("depth_image")
    path = renderer / "utils/depth_image.py"
    exec(compile(path.read_bytes(), str(path), "exec"), render.__dict__)
    return detector, model, render.generate_depth_image


def reconstruct(frame, detector, model, render):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    faces = detector.detect_faces(rgb)
    if not faces:
        raise ValueError("MTCNN did not detect a face")
    x, y, w, h = max(faces, key=lambda item: item["box"][2] * item["box"][3])["box"]
    positions = model.process(rgb, np.array([x, x + w, y, y + h]))
    vertices = model.get_vertices(positions)
    depth = render(vertices, model.get_landmarks(positions), rgb.shape, isMedFilter=True)
    return (x, y, w, h), depth


def crop_bounds(box, shape, scale=1.3):
    x, y, w, h = box
    height, width = shape[:2]
    # Keep the loader's operation order at floating-point pixel boundaries.
    center_x, center_y = (x + (x + w)) / 2, (y + (y + h)) / 2
    half_w, half_h = scale * w / 2, scale * h / 2
    left = max(0, math.floor(center_x - half_w))
    right = min(width, math.floor(center_x + half_w))
    top = max(0, math.floor(center_y - half_h))
    bottom = min(height, math.floor(center_y + half_h))
    if left >= right or top >= bottom:
        raise ValueError("empty scaled face box")
    return slice(top, bottom), slice(left, right)


def select_videos(protocol, split, wide_sample=False):
    with tarfile.open(protocol, "r:") as archive:
        raw = archive.extractfile(f"Protocols/Protocol_1/{split}.txt").read().decode("utf-8-sig")
    rows = [(int(label), name.strip()) for label, name in csv.reader(raw.splitlines()) if label.strip()]
    # One video for each phone/session combination and each selected class.
    phone_sessions = [(1, 1), (4, 2)] if wide_sample else [(1, 1)]
    choices = [(phone, session, access) for phone, session in phone_sessions for access in (1, 2, 4)]
    videos = {}
    for phone, session, access in choices:
        for label, name in rows:
            fields = [int(item) for item in name.split("_")]
            if (fields[0], fields[1], fields[3]) == (phone, session, access):
                if (label == 1) != (access == 1):
                    raise ValueError(f"label mismatch: {name}")
                videos[name] = access
                break
        else:
            raise ValueError(f"missing smoke stratum: {split} {phone} {session} {access}")
    return videos


def emit_video(path, access, split, output, models, slots=SMOKE_SLOTS, *, spread_train=False):
    cap = cv2.VideoCapture(str(path))
    try:
        count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if count < (len(slots) if spread_train else 10):
            raise ValueError(f"cannot determine frame count: {path.name}")
        rows, used = [], set()
        # Dev keeps the public loader's stride. Train can sample across the whole AVI.
        for slot in slots:
            nominal = 1 + slot * count // len(slots) if spread_train else 1 + slot * (count // 10)
            stop = min(nominal + 50, count + 1)
            if spread_train:
                stop = 1 + (slot + 1) * count // len(slots)
                candidates = chain(range(nominal, stop), range(stop, min(stop + 50, count + 1)),
                                   range(nominal - 1, max(0, nominal - 51), -1))
            else:
                candidates = range(nominal, stop)
            tried = set()
            for frame_id in candidates:
                if frame_id in used:
                    continue
                if frame_id in tried:
                    continue
                tried.add(frame_id)
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id - 1)
                ok, frame = cap.read()
                if not ok or abs(cap.get(cv2.CAP_PROP_POS_FRAMES) - frame_id) >= 0.5:
                    continue
                try:
                    box, depth = reconstruct(frame, *models)
                    roi = crop_bounds(box, frame.shape)
                except (ValueError, QhullError):
                    continue
                if depth.shape != frame.shape[:2] or depth.dtype != np.uint8:
                    raise ValueError("expected a full-scene uint8 depth map")
                ok, encoded_map = cv2.imencode(".jpg", depth)
                if not ok:
                    raise OSError("could not encode depth JPEG")
                map32 = cv2.resize(cv2.imdecode(encoded_map, cv2.IMREAD_GRAYSCALE)[roi], (32, 32))
                if not map32.any() or (access == 1 and not np.ptp(map32)):
                    continue
                # Match the assets the public loader reloads before resizing.
                stem = f"{path.stem}_{frame_id:03d}"
                scene_path = output / split / "images" / path.stem / f"{stem}_scene.jpg"
                map_path = output / split / "maps" / path.stem / f"{stem}_depth1D.jpg"
                scene_path.parent.mkdir(parents=True, exist_ok=True)
                map_path.parent.mkdir(parents=True, exist_ok=True)
                if not cv2.imwrite(str(scene_path), frame):
                    raise OSError(f"could not write {scene_path}")
                map_path.write_bytes(encoded_map.tobytes())
                scene_path.with_suffix(".dat").write_text("\n".join(map(str, box)) + "\n")
                used.add(frame_id)
                rows.append({"video_id": path.stem, "split": split, "access": access, "slot": slot,
                             "frame_id": frame_id, "nominal": nominal,
                             "prnet_sum_32": int(map32.sum()), "train_target_zero": access != 1})
                break
        return rows
    finally:
        cap.release()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path)
    parser.add_argument("--image", type=Path)
    parser.add_argument("--wide-sample", action="store_true", help="also sample phone 4, session 2")
    parser.add_argument("--training-pilot", action="store_true", help="prepare eight frames per video")
    parser.add_argument("--prnet", type=Path, required=True)
    parser.add_argument("--renderer", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if (args.data is None) == (args.image is None):
        parser.error("supply either --data or --image")
    versions = {}
    for key, repo, expected in (("prnet", args.prnet, PRNET_COMMIT), ("renderer", args.renderer, DEPTH_COMMIT)):
        commit = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
        if commit != expected:
            raise ValueError(f"{key} checkout must be {expected}")
        versions[key] = commit
    weight = args.prnet / "Data/net-data/256_256_resfcn256_weight.data-00000-of-00001"
    if sha(weight) != WEIGHT_SHA or sha(weight.with_suffix(".index")) != INDEX_SHA:
        raise ValueError("public PRNet checkpoint SHA-256 differs")
    args.output.mkdir(parents=True, exist_ok=False)
    with Progress("Load MTCNN and PRNet"):
        models = load_models(args.prnet, args.renderer)
    if args.image:
        image = cv2.imread(str(args.image))
        if image is None:
            raise ValueError(f"cannot decode {args.image}")
        box, depth = reconstruct(image, *models)
        if not depth.any():
            raise ValueError("PRNet returned an empty map")
        cv2.imwrite(str(args.output / "depth.png"), depth)
        print("PRNET_IMAGE_PASS", box, int(depth.max()), int(np.count_nonzero(depth)), flush=True)
        return
    rows, failures = [], []
    slots = PILOT_SLOTS if args.training_pilot else SMOKE_SLOTS
    started = time.monotonic()
    for split in ("Train", "Dev"):
        videos = select_videos(args.data / "Protocols.tar", split, args.wide_sample)
        archive_path = args.data / f"{split}_files.tar"
        print(f"{split}: look for AVI members in {archive_path.name}", flush=True)
        with Progress(f"{split} TAR and depth", len(videos), "videos") as progress, \
                tarfile.open(archive_path, "r:") as archive, tempfile.TemporaryDirectory() as temp:
            remaining = set(videos)
            for member in archive:
                name = PurePosixPath(member.name)
                if not member.isfile() or name.suffix.lower() != ".avi" or name.stem not in remaining:
                    continue
                local = Path(temp) / name.name
                with archive.extractfile(member) as source, local.open("wb") as dest:
                    shutil.copyfileobj(source, dest, 4 * 1024 * 1024)
                observations = emit_video(local, videos[name.stem], split, args.output, models, slots)
                rows.extend(observations)
                with (args.output / "frames.jsonl").open("a", encoding="utf-8") as journal:
                    for observation in observations:
                        journal.write(json.dumps(observation) + "\n")
                if len(observations) != len(slots):
                    failures.append({"video_id": name.stem, "frames": len(observations)})
                local.unlink()
                remaining.remove(name.stem)
                progress.update(len(videos) - len(remaining))
                print(f"{split}: {len(videos) - len(remaining)}/{len(videos)} videos | {time.monotonic()-started:.1f}s", flush=True)
                if not remaining:
                    break
            failures.extend({"video_id": video, "error": "missing AVI member"} for video in sorted(remaining))
    packages = [spec.split("==")[0] for spec in SMOKE_PACKAGES]
    report = {"frames": rows, "failures": failures, "source": versions, "weight_sha256": WEIGHT_SHA,
              "weight_index_sha256": INDEX_SHA, "protocol_sha256": sha(args.data / "Protocols.tar"),
              "wide_sample": args.wide_sample, "slots": list(slots),
              "packages": {name: importlib.metadata.version(name) for name in packages},
              "seconds": time.monotonic() - started}
    (args.output / "smoke_summary.json").write_text(json.dumps(report, indent=2))
    if failures:
        raise ValueError(f"Smoke incomplete: {failures}")
    print("CDCN_PRNET_SMOKE_PASS", len(rows), "frames", flush=True)


if __name__ == "__main__":
    main()
