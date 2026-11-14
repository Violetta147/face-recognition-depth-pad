"""Read the official OULU-NPU lists and build a reusable face-frame cache."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import shutil
import tarfile
import tempfile
import time

import numpy as np
import pandas as pd

from .data import MANIFEST_COLUMNS, manifest_checksum
from .progress import Progress
from .webcam import yunet_boxes


SPLITS = {"train": "Train", "val": "Dev", "test": "Test"}
SUBJECTS = {"train": range(1, 21), "val": range(21, 36), "test": range(36, 56)}
ATTACK_TYPES = {1: "live", 2: "print1", 3: "print2", 4: "replay1", 5: "replay2"}
FRAME_SIZE = 256
CROP_VERSION = 1


@dataclass(frozen=True)
class Video:
    id: str
    phone: int
    session: int
    subject: int
    access: int

    @classmethod
    def parse(cls, name: str) -> Video:
        stem = PurePosixPath(name).stem
        match = re.fullmatch(r"([1-6])_([1-3])_(\d{1,2})_([1-5])", stem)
        if match is None:
            raise ValueError(f"invalid OULU video ID: {name}")
        return cls(stem, *map(int, match.groups()))


def expected_ids(protocol: int, fold: int | None, split: str) -> set[tuple[int, ...]]:
    if protocol not in (1, 2, 3, 4) or (fold not in range(1, 7) if protocol >= 3 else fold is not None):
        raise ValueError("protocol 1/2 use no fold; protocol 3/4 require fold 1..6")
    test = split == "test"
    sessions = ([3] if test else [1, 2]) if protocol in (1, 4) else range(1, 4)
    access = ([1, 3, 5] if test else [1, 2, 4]) if protocol in (2, 4) else range(1, 6)
    phones = [phone for phone in range(1, 7) if fold is None or (phone == fold) == test]
    return {(p, s, u, a) for p in phones for s in sessions for u in SUBJECTS[split] for a in access}


def protocol_videos(archive: Path, protocol: int, fold: int | None, split: str) -> list[Video]:
    expected = expected_ids(protocol, fold, split)
    suffix = "" if fold is None else f"_{fold}"
    target = f"Protocols/Protocol_{protocol}/{SPLITS[split]}{suffix}.txt"
    with tarfile.open(archive, "r:") as tar:
        matches = [m for m in tar if m.name.removeprefix("./") == target and m.isfile()]
        if len(matches) != 1:
            raise ValueError(f"expected exactly one {target} in {archive.name}")
        records = tar.extractfile(matches[0]).read().decode("utf-8-sig").splitlines()
    videos = []
    found = set()
    for label_text, name in csv.reader(line for line in records if line.strip()):
        video = Video.parse(name.strip())
        key = (video.phone, video.session, video.subject, video.access)
        label = 1 if video.access == 1 else -2 if split == "test" and video.access >= 4 else -1
        if key in found or int(label_text) != label:
            raise ValueError(f"duplicate ID or conflicting label in {target}: {video.id}")
        found.add(key)
        videos.append(video)
    if found != expected:
        raise ValueError(f"unexpected membership in {target}: {len(expected - found)} missing, {len(found - expected)} extra")
    return sorted(videos, key=lambda video: (video.access, video.phone, video.session, video.subject))


def select_videos(videos: list[Video], pilot: bool) -> list[Video]:
    if not pilot:
        return videos
    # One video per phone/access pair, distributed over the available subjects and sessions.
    groups: dict[tuple[int, int], list[Video]] = {}
    for video in videos:
        groups.setdefault((video.phone, video.access), []).append(video)
    return [group[(phone * 7 + access * 11) % len(group)] for (phone, access), group in groups.items()]


def read_eyes(payload: bytes) -> dict[int, tuple[float, float, float, float]]:
    eyes = {}
    for line in payload.decode("utf-8-sig").splitlines():
        fields = line.replace(",", " ").split()
        if not fields:
            continue
        if len(fields) != 5:
            raise ValueError(f"invalid eye coordinates: {line!r}")
        index, *coordinates = fields
        values = tuple(map(float, coordinates))
        if all(math.isfinite(value) and value > 0 for value in values):
            eyes[int(index)] = values
    return eyes


def face_crop(frame, detector, eyes):
    import cv2

    height, width = frame.shape[:2]
    side = 320
    _, detections = detector.detect(cv2.resize(frame, (side, side)))
    boxes = yunet_boxes(detections, width, height, side)
    if boxes:
        x, y, w, h = max(boxes, key=lambda box: box[2] * box[3])
        center_x, center_y = x + w / 2, y + h / 2
        crop_side = 1.25 * max(w, h)
        source = "yunet"
    elif eyes is not None:
        lx, ly, rx, ry = eyes
        distance = math.hypot(lx - rx, ly - ry)
        if distance < 8 or max(lx, rx) >= width or max(ly, ry) >= height:
            return None, None
        center_x, center_y = (lx + rx) / 2, (ly + ry) / 2 + .45 * distance
        crop_side = 2.8 * distance
        source = "eyes"
    else:
        return None, None
    size = min(width, height, max(1, round(crop_side)))
    left = max(0, min(width - size, round(center_x - size / 2)))
    top = max(0, min(height - size, round(center_y - size / 2)))
    return cv2.resize(frame[top:top + size, left:left + size], (FRAME_SIZE, FRAME_SIZE),
                      interpolation=cv2.INTER_AREA if size >= FRAME_SIZE else cv2.INTER_LINEAR), source


def sample_crops(path: Path, detector, eyes: dict, count: int):
    import cv2

    capture = cv2.VideoCapture(str(path))
    try:
        frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        if not capture.isOpened() or frames < count:
            raise ValueError(f"cannot decode {count} frames from {path.name} ({frames} reported)")
        # Preserve one crop per bin where possible. Fill empty bins with distinct
        # valid frames from the same video, after reserving the in-bin choices.
        edges = np.linspace(0, frames, count + 1, dtype=int)
        used, failed, selected, missing = set(), set(), [], []

        def find_crop(indices, middle):
            for index in sorted(indices, key=lambda i: (abs(i - middle), i)):
                if index in used or index in failed:
                    continue
                if capture.set(cv2.CAP_PROP_POS_FRAMES, index):
                    ok, frame = capture.read()
                    if ok and abs(capture.get(cv2.CAP_PROP_POS_FRAMES) - (index + 1)) < .5:
                        crop, method = face_crop(frame, detector, eyes.get(index))
                        if crop is not None:
                            used.add(index)
                            return index, crop, method
                failed.add(index)
            return None

        for start, end in zip(edges[:-1], edges[1:]):
            middle = (int(start) + int(end) - 1) / 2
            item = find_crop(range(start, end), middle)
            if item is None:
                missing.append((start, end, middle))
            else:
                selected.append(item)
        for start, end, middle in missing:
            item = find_crop(range(frames), middle)
            if item is None:
                raise ValueError(f"{path.name}: fewer than {count} distinct valid face crops; empty bin [{start}, {end})")
            index, crop, method = item
            selected.append((index, crop, method + "_nearby"))
        yield from sorted(selected, key=lambda item: item[0])
    finally:
        capture.release()


def atomic_text(path: Path, value: str) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(value, encoding="utf-8")
    temporary.replace(path)


def write_json(path: Path, value: dict) -> None:
    atomic_text(path, json.dumps(value, indent=2, allow_nan=False) + "\n")


def prepare(protocol_archive: Path, media_archive: Path, detector_path: Path, root: Path,
            protocol: int, fold: int | None, split: str, pilot: bool, count: int = 20) -> Path:
    import cv2

    if count < 1 or (pilot and split == "test"):
        raise ValueError("positive frame count required; the pilot uses train/dev only")
    started = time.perf_counter()
    cv2.setNumThreads(1)
    videos = select_videos(protocol_videos(protocol_archive, protocol, fold, split), pilot)
    namespace = f"p{protocol}" + (f"-fold{fold}" if fold is not None else "") + ("-pilot" if pilot else "")
    manifest_dir = root / namespace
    manifest_dir.mkdir(parents=True, exist_ok=True)
    archive_stat = media_archive.stat()
    binding = {"crop_version": CROP_VERSION, "archive": media_archive.name,
               "archive_bytes": archive_stat.st_size, "archive_mtime_ns": archive_stat.st_mtime_ns,
               "detector_sha256": manifest_checksum(detector_path), "opencv": cv2.__version__,
               "frames_per_video": count}
    cache_key = hashlib.sha256(json.dumps(binding, sort_keys=True).encode()).hexdigest()[:16]
    cache = root / "crops" / split / cache_key
    cache.mkdir(parents=True, exist_ok=True)
    detector = cv2.FaceDetectorYN.create(str(detector_path), "", (320, 320), .7, .3, 5000)
    all_rows = []
    needed = {video.id for video in videos}
    with tarfile.open(media_archive, "r:") as tar, tempfile.TemporaryDirectory(dir=root) as temp:
        members = {}
        with Progress(f"{split}: index {media_archive.name}", archive_stat.st_size, "byte offset") as progress:
            for member in tar:
                progress.update(member.offset_data)
                path = PurePosixPath(member.name)
                key = (path.stem, path.suffix.lower())
                if member.isfile() and path.stem in needed and key[1] in {".avi", ".txt"}:
                    if key in members:
                        raise ValueError(f"duplicate member {key} in {media_archive.name}")
                    members[key] = member
            progress.update(archive_stat.st_size)
        missing = sorted(needed - {name for name, ext in members if ext == ".avi"})
        if missing:
            raise ValueError(f"{media_archive.name} missing {len(missing)} videos, first: {missing[:5]}")
        videos.sort(key=lambda video: members[video.id, ".avi"].offset)
        reused = 0
        with Progress(f"{split}: verify/crop", len(videos), "videos") as progress:
            for number, video in enumerate(videos, 1):
                folder = cache / video.id
                folder.mkdir(exist_ok=True)
                record = folder / "frames.json"
                rows = json.loads(record.read_text(encoding="utf-8")) if record.is_file() else []
                if len(rows) != count or not all((root / row["image_path"]).is_file() and
                                                 manifest_checksum(root / row["image_path"]) == row["image_sha256"]
                                                 for row in rows):
                    eye_file = members.get((video.id, ".txt"))
                    eyes = read_eyes(tar.extractfile(eye_file).read()) if eye_file else {}
                    local_path = Path(temp) / f"{video.id}.avi"
                    try:
                        with tar.extractfile(members[video.id, ".avi"]) as source, local_path.open("wb") as output:
                            shutil.copyfileobj(source, output, length=4 * 1024 * 1024)
                        with local_path.open("rb") as stream:
                            video_sha = hashlib.file_digest(stream, "sha256").hexdigest()
                        rows = []
                        for index, crop, method in sample_crops(local_path, detector, eyes, count):
                            image = folder / f"{index:04d}.png"
                            if not cv2.imwrite(str(image), crop, [cv2.IMWRITE_PNG_COMPRESSION, 1]):
                                raise OSError(f"could not write {image}")
                            rows.append({"sample_id": f"oulu_{video.id}_{index:04d}", "split": split,
                                         "subject_id": str(video.subject), "video_id": video.id, "frame_index": index,
                                         "image_path": image.relative_to(root).as_posix(), "depth_path": "",
                                         "label": int(video.access == 1), "attack_type": ATTACK_TYPES[video.access],
                                         "image_sha256": manifest_checksum(image), "video_sha256": video_sha,
                                         "crop_method": method})
                        atomic_text(record, json.dumps(rows))
                    finally:
                        local_path.unlink(missing_ok=True)
                else:
                    reused += 1
                all_rows.extend(rows)
                progress.update(number)
    frame = pd.DataFrame(all_rows, columns=[*MANIFEST_COLUMNS, "image_sha256", "video_sha256", "crop_method"])
    frame.sort_values(["video_id", "frame_index"], inplace=True)
    path = manifest_dir / f"{split}.csv"
    atomic_text(path, frame.to_csv(index=False, lineterminator="\n"))
    summary = {**binding, "protocol": protocol, "fold": fold, "pilot": pilot, "split": split,
               "protocol_sha256": manifest_checksum(protocol_archive), "manifest_sha256": manifest_checksum(path),
               "videos": len(videos), "subjects": int(frame.subject_id.nunique()), "frames": len(frame),
               "video_counts": dict(Counter(ATTACK_TYPES[video.access] for video in videos)),
               "crop_counts": dict(Counter(frame.crop_method)), "reused_videos": reused,
               "seconds": round(time.perf_counter() - started, 3)}
    write_json(path.with_suffix(".json"), summary)
    print(json.dumps(summary, indent=2), flush=True)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--drive", required=True, type=Path)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--detector", required=True, type=Path)
    parser.add_argument("--protocol", default=1, type=int)
    parser.add_argument("--fold", type=int)
    parser.add_argument("--split", required=True, choices=SPLITS)
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument("--frames", type=int, default=20)
    args = parser.parse_args()
    prepare(args.drive / "Protocols.tar", args.drive / f"{SPLITS[args.split]}_files.tar", args.detector,
            args.root, args.protocol, args.fold, args.split, args.pilot, args.frames)


if __name__ == "__main__":
    main()
