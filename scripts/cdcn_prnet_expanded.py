"""Prepare a restartable Train/Dev sample for an expanded CDCN pilot."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tarfile
import tempfile
import time
from uuid import uuid4
import zipfile

from cdcn_prnet_smoke import (
    DEPTH_COMMIT, INDEX_SHA, PILOT_SLOTS, PRNET_COMMIT, WEIGHT_SHA, emit_video, load_models, sha,
)
from deepface_pad.progress import Progress

SUBJECT_COUNTS = {"Train": 8, "Dev": 6}


def select_group(protocol, split):
    with tarfile.open(protocol, "r:") as archive:
        text = archive.extractfile(f"Protocols/Protocol_1/{split}.txt").read().decode("utf-8-sig")
    candidates = {}
    for label, video in csv.reader(line for line in text.splitlines() if line.strip()):
        phone, session, subject, access = map(int, video.strip().split("_"))
        if (phone, session) == (1, 1):
            if (int(label) == 1) != (access == 1) or video.strip() in candidates:
                raise ValueError(f"Inconsistent protocol entry: {video}")
            candidates[video.strip()] = (subject, access)
    subjects = sorted({subject for subject, _ in candidates.values()})[:SUBJECT_COUNTS[split]]
    selected = {video: access for video, (subject, access) in candidates.items() if subject in subjects}
    if len(subjects) != SUBJECT_COUNTS[split] or any(
        {access for person, access in candidates.values() if person == subject} != {1, 2, 3, 4, 5}
        for subject in subjects
    ):
        raise ValueError(f"Incomplete classes in {split}")
    return selected


def frame_assets(split, video, frame_id):
    name = f"{video}_{frame_id:03d}"
    return (f"{split}/images/{video}/{name}_scene.jpg", f"{split}/images/{video}/{name}_scene.dat",
            f"{split}/maps/{video}/{name}_depth1D.jpg")


def video_assets(rows, split, video, access):
    if (len(rows) != len(PILOT_SLOTS) or [row["slot"] for row in rows] != list(PILOT_SLOTS)
            or len({row["frame_id"] for row in rows}) != len(PILOT_SLOTS)
            or any(row["split"] != split or row["video_id"] != video or row["access"] != access
                   or row["frame_id"] < 1 or row["prnet_sum_32"] <= 0
                   or row["train_target_zero"] != (access != 1) for row in rows)):
        raise ValueError(f"Invalid or incomplete assets for {split}/{video}")
    return [name for row in rows for name in frame_assets(split, video, row["frame_id"])]


def publish_video(cache_path, root, split, video, access, rows):
    names = video_assets(rows, split, video, access)
    partial = cache_path.with_name(f"{cache_path.stem}-{uuid4().hex}.part")
    try:
        with tempfile.TemporaryDirectory() as directory:
            local = Path(directory) / "video.zip"
            with zipfile.ZipFile(local, "x") as archive:
                archive.writestr("frames.json", json.dumps(rows))
                for name in names:
                    archive.write(root / name, name)
            with zipfile.ZipFile(local) as archive:
                if archive.testzip() is not None:
                    raise OSError(f"Failed to verify {local}")
            shutil.copyfile(local, partial)
            expected_bytes = local.stat().st_size
            # A mounted Drive can briefly report a stale size after the writer closes.
            deadline = time.monotonic() + 5
            while partial.stat().st_size != expected_bytes:
                if time.monotonic() >= deadline:
                    raise OSError(f"Incomplete cache transfer: {partial}")
                time.sleep(0.25)
        partial.replace(cache_path)
    finally:
        partial.unlink(missing_ok=True)


def restore_video(cache_path, root, split, video, access):
    with zipfile.ZipFile(cache_path) as archive:
        rows = json.loads(archive.read("frames.json"))
        names = video_assets(rows, split, video, access)
        if sorted(archive.namelist()) != sorted(["frames.json", *names]):
            raise ValueError(f"Unexpected entries in {cache_path}")
        for name in names:
            destination = root / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(archive.read(name))
    return rows


def prepare(data, cache, output, prnet, renderer, baseline=None):
    protocol = data / "Protocols.tar"
    protocol_digest = sha(protocol)
    selected = {split: select_group(protocol, split) for split in SUBJECT_COUNTS}
    output.mkdir(parents=True, exist_ok=False)
    baseline_rows = {}
    if baseline:
        manifest = json.loads((baseline / "smoke_summary.json").read_text(encoding="utf-8"))
        if (manifest["failures"] or manifest["protocol_sha256"] != protocol_digest
                or manifest["weight_sha256"] != WEIGHT_SHA or manifest["weight_index_sha256"] != INDEX_SHA
                or manifest["source"] != {"prnet": PRNET_COMMIT, "renderer": DEPTH_COMMIT}):
            raise ValueError("Baseline snapshot provenance differs")
        for row in manifest["frames"]:
            baseline_rows.setdefault((row["split"], row["video_id"]), []).append(row)

    models = None
    rows, failures = [], []
    for split, videos in selected.items():
        split_cache = cache / split
        split_cache.mkdir(parents=True, exist_ok=True)
        waiting = {}
        with Progress(f"{split} restore completed videos", len(videos), "videos") as progress:
            for done, (video, access) in enumerate(sorted(videos.items()), 1):
                target = split_cache / f"{video}.zip"
                previous = baseline_rows.get((split, video))
                if not target.exists() and previous:
                    publish_video(target, baseline, split, video, access, previous)
                try:
                    restored = restore_video(target, output, split, video, access) if target.exists() else None
                except (zipfile.BadZipFile, KeyError, UnicodeError, ValueError) as exc:
                    print(f"Rebuild invalid cache {target.name}: {exc}", flush=True)
                    restored = None
                if restored is None:
                    waiting[video] = access
                else:
                    rows.extend(restored)
                progress.update(done)
        if not waiting:
            continue
        if models is None:
            with Progress("Load MTCNN and PRNet"):
                for source, expected in ((prnet, PRNET_COMMIT), (renderer, DEPTH_COMMIT)):
                    commit = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
                    if commit != expected:
                        raise ValueError(f"Unexpected revision for {source}")
                weight = prnet / "Data/net-data/256_256_resfcn256_weight.data-00000-of-00001"
                if sha(weight) != WEIGHT_SHA or sha(weight.with_suffix(".index")) != INDEX_SHA:
                    raise ValueError("Unexpected PRNet checkpoint")
                models = load_models(prnet, renderer)
        count = len(waiting)
        with Progress(f"{split} prepare missing videos", count, "videos") as progress, \
                tarfile.open(data / f"{split}_files.tar", "r:") as archive, tempfile.TemporaryDirectory() as tmp:
            for member in archive:
                name = PurePosixPath(member.name)
                if not member.isfile() or name.suffix.lower() != ".avi" or name.stem not in waiting:
                    continue
                local = Path(tmp) / name.name
                with archive.extractfile(member) as source, local.open("wb") as target:
                    shutil.copyfileobj(source, target, 4 * 1024 * 1024)
                access = waiting[name.stem]
                try:
                    observations = emit_video(local, access, split, output, models, PILOT_SLOTS)
                    video_assets(observations, split, name.stem, access)
                except ValueError as exc:
                    failure = {"split": split, "video": name.stem, "error": str(exc)}
                    failures.append(failure)
                    print(json.dumps(failure), flush=True)
                else:
                    publish_video(split_cache / f"{name.stem}.zip", output, split, name.stem, access, observations)
                    rows.extend(observations)
                local.unlink()
                waiting.pop(name.stem)
                progress.update(count - len(waiting))
                if not waiting:
                    break
        failures.extend({"split": split, "video": video, "error": "missing AVI"} for video in sorted(waiting))
    manifest = {"profile": "expanded", "slots": list(PILOT_SLOTS), "failures": failures,
                "protocol_sha256": protocol_digest, "source": {"prnet": PRNET_COMMIT, "renderer": DEPTH_COMMIT},
                "weight_sha256": WEIGHT_SHA, "weight_index_sha256": INDEX_SHA,
                "frames": sorted(rows, key=lambda row: (row["split"], row["video_id"], row["slot"]))}
    (output / "smoke_summary.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    if failures:
        raise ValueError(f"Preparation incomplete for {len(failures)} videos. See {output / 'smoke_summary.json'}")
    print("CDCN_EXPANDED_DATA_READY", len(rows), "frames", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("data", "cache", "output", "prnet", "renderer"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--baseline", type=Path)
    prepare(**vars(parser.parse_args()))
