"""Prepare a restartable Train/Dev sample for an expanded CDCN pilot."""
from __future__ import annotations

import argparse
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from contextlib import ExitStack
import csv
from functools import partial
import json
import multiprocessing
import os
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
FULL_COUNTS = {"Train": 1200, "Dev": 900}
FULL_TRAIN_SLOTS = tuple(range(24))


def full_membership(protocol, *, splits=("Train", "Dev")):
    from deepface_pad.oulu_npu import protocol_videos

    names = {"Train": "train", "Dev": "val", "Test": "test"}
    return {
        split: {video.id: video.access for video in protocol_videos(protocol, 1, None, names[split])}
        for split in splits
    }


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


def video_assets(rows, split, video, access, slots=PILOT_SLOTS):
    if (len(rows) != len(slots) or [row["slot"] for row in rows] != list(slots)
            or len({row["frame_id"] for row in rows}) != len(slots)
            or any(row["split"] != split or row["video_id"] != video or row["access"] != access
                   or row["frame_id"] < 1 or row["prnet_sum_32"] <= 0
                   or row["train_target_zero"] != (access != 1) for row in rows)):
        raise ValueError(f"Invalid or incomplete assets for {split}/{video}")
    return [name for row in rows for name in frame_assets(split, video, row["frame_id"])]


def publish_video(cache_path, root, split, video, access, rows, slots=PILOT_SLOTS):
    names = video_assets(rows, split, video, access, slots)
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


def restore_video(cache_path, root, split, video, access, slots=PILOT_SLOTS, *, stage_zip=False):
    with ExitStack() as stack:
        source = cache_path
        if stage_zip:
            directory = stack.enter_context(tempfile.TemporaryDirectory(prefix="restore-zip-", dir=root.parent))
            source = Path(directory) / cache_path.name
            try:
                shutil.copyfile(cache_path, source)
            except OSError as exc:
                raise OSError(exc.errno, "Could not stage cache ZIP to the runtime disk", cache_path) from exc
        archive = stack.enter_context(zipfile.ZipFile(source))
        rows = json.loads(archive.read("frames.json"))
        names = video_assets(rows, split, video, access, slots)
        if sorted(archive.namelist()) != sorted(["frames.json", *names]):
            raise ValueError(f"Unexpected entries in {cache_path}")
        for name in names:
            destination = root / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(archive.read(name))
    return rows


def staged_video(archive, member, directory):
    local = directory / PurePosixPath(member.name).name
    with archive.extractfile(member) as source, local.open("wb") as target:
        shutil.copyfileobj(source, target, 4 * 1024 * 1024)
    return local


def prepare_video(local, access, split, output, models, slots, *, spread_train=False):
    try:
        rows = emit_video(local, access, split, output, models, slots, spread_train=spread_train)
        video_assets(rows, split, local.stem, access, slots)
    except ValueError as exc:
        return [], {"split": split, "video": local.stem, "error": str(exc)}
    return rows, None


_PROCESS_MODELS = None


def init_process(prnet, renderer, threads):
    global _PROCESS_MODELS
    for key in ("TF_NUM_INTRAOP_THREADS", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ[key] = str(threads)
    os.environ["TF_NUM_INTEROP_THREADS"] = "1"
    import cv2
    from threadpoolctl import threadpool_limits

    # NumPy/SciPy may have loaded before the spawned process runs the initializer.
    threadpool_limits(limits=threads)
    cv2.setNumThreads(threads)
    _PROCESS_MODELS = load_models(prnet, renderer)


def prepare_test_video(local, access, output):
    return prepare_video(local, access, "Test", output, _PROCESS_MODELS, PILOT_SLOTS)


def check_parallel_reference(pool, archive, scratch, output, rows):
    video, access = rows[0]["video_id"], rows[0]["access"]
    probe_output = scratch / "probe"
    for member in archive:
        name = PurePosixPath(member.name)
        if member.isfile() and name.suffix.lower() == ".avi" and name.stem == video:
            local = staged_video(archive, member, scratch)
            result, failure = pool.submit(prepare_test_video, local, access, probe_output).result()
            local.unlink()
            # The scorer consumes the scene and bbox, and the sum of the cropped PRNet map.
            names = video_assets(rows, "Test", video, access)
            inputs = [name for name in names if name.endswith(("_scene.jpg", "_scene.dat"))]
            if failure or result != rows or any(sha(probe_output / name) != sha(output / name) for name in inputs):
                print(f"PARALLEL_REFERENCE_DIFFERS {video} | Switching to serial preparation", flush=True)
                return False
            print(f"PARALLEL_REFERENCE_MATCH {video} | 8 frames", flush=True)
            return True
    raise ValueError(f"Cached Test video {video} is missing from {archive.name}")


def parallel_jobs(pool, archive, scratch, output, waiting, workers):
    pending = {}
    for member in archive:
        name = PurePosixPath(member.name)
        if not member.isfile() or name.suffix.lower() != ".avi" or name.stem not in waiting:
            continue
        access = waiting.pop(name.stem)
        local = staged_video(archive, member, scratch)
        pending[pool.submit(prepare_test_video, local, access, output)] = (local, access)
        if len(pending) >= workers:
            done, _ = wait(pending, return_when=FIRST_COMPLETED)
            for future in done:
                local, access = pending.pop(future)
                yield local, access, future.result()
        if not waiting:
            break
    while pending:
        done, _ = wait(pending, return_when=FIRST_COMPLETED)
        for future in done:
            local, access = pending.pop(future)
            yield local, access, future.result()


def serial_jobs(archive, scratch, output, waiting, *, split, models, slots, spread_train):
    for member in archive:
        name = PurePosixPath(member.name)
        if not member.isfile() or name.suffix.lower() != ".avi" or name.stem not in waiting:
            continue
        access = waiting.pop(name.stem)
        local = staged_video(archive, member, scratch)
        yield local, access, prepare_video(local, access, split, output, models, slots, spread_train=spread_train)
        if not waiting:
            break


def prepare(data, cache, output, prnet, renderer, baseline=None, full=False,
            dev_cache=None, splits=("Train", "Dev"), stage_dir=None, restore_only=False, workers=1):
    test_only = tuple(splits) == ("Test",)
    if workers < 1 or (workers > 1 and not test_only):
        raise ValueError("Use one or more workers for Test and one for Train/Dev")
    if "Test" in splits and not (test_only and full and baseline is None and dev_cache is None):
        raise ValueError("Test preparation requires --full --splits Test by itself")
    protocol = data / "Protocols.tar"
    protocol_digest = sha(protocol)
    if full:
        selected = full_membership(protocol, splits=("Test",)) if test_only else full_membership(protocol)
    else:
        selected = {split: select_group(protocol, split) for split in SUBJECT_COUNTS}
    if len(set(splits)) != len(splits) or (full and baseline is not None):
        raise ValueError("Choose unique splits and use --dev-cache to seed full preparation")
    output.mkdir(parents=True, exist_ok=full)
    manifest_path = output / "smoke_summary.json"
    if full:
        manifest_path.unlink(missing_ok=True)
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
    for split in splits:
        videos = selected[split]
        spread_train = full and split == "Train"
        slots = FULL_TRAIN_SLOTS if spread_train else PILOT_SLOTS
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
                    restored = (restore_video(target, output, split, video, access, slots, stage_zip=full)
                                if target.exists() else None)
                    if restored is None and split == "Dev" and dev_cache is not None:
                        source = dev_cache / f"{video}.zip"
                        if source.is_file():
                            restored = restore_video(source, output, split, video, access, slots, stage_zip=full)
                            publish_video(target, output, split, video, access, restored, slots)
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
        if restore_only:
            failures.extend({"split": split, "video": video, "error": "missing or invalid cache"}
                            for video in waiting)
            continue
        if models is None:
            with Progress("Verify MTCNN and PRNet sources"):
                for source, expected in ((prnet, PRNET_COMMIT), (renderer, DEPTH_COMMIT)):
                    commit = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
                    if commit != expected:
                        raise ValueError(f"Unexpected revision for {source}")
                weight = prnet / "Data/net-data/256_256_resfcn256_weight.data-00000-of-00001"
                if sha(weight) != WEIGHT_SHA or sha(weight.with_suffix(".index")) != INDEX_SHA:
                    raise ValueError("Unexpected PRNet checkpoint")
        count = len(waiting)
        archive_path = data / f"{split}_files.tar"
        if stage_dir is not None:
            from deepface_pad.colab_cache import copy_progress

            archive_path = copy_progress(archive_path, stage_dir / archive_path.name, f"Stage {archive_path.name}")
        with ExitStack() as resources:
            scratch = Path(resources.enter_context(tempfile.TemporaryDirectory(prefix="prepare-", dir=output)))
            rendered = scratch / "rendered" if workers > 1 else output
            job = None
            if workers > 1:
                cpus = len(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else (os.cpu_count() or 1)
                workers = min(workers, cpus, count)
            if workers > 1:
                threads = max(1, cpus // workers)
                pool = resources.enter_context(ProcessPoolExecutor(
                    max_workers=workers, mp_context=multiprocessing.get_context("spawn"),
                    initializer=init_process, initargs=(prnet, renderer, threads),
                ))
                if rows:
                    ref = [row for row in rows if row["video_id"] == rows[0]["video_id"]]
                    with Progress("Compare parallel preprocessing with cached Test frames"), \
                            tarfile.open(archive_path, "r:") as reference_archive:
                        if check_parallel_reference(pool, reference_archive, scratch, output, ref):
                            job = partial(parallel_jobs, pool, workers=workers)
                else:
                    job = partial(parallel_jobs, pool, workers=workers)
            if job is None:
                workers, rendered = 1, output
                if models is None:
                    with Progress("Load MTCNN and PRNet"):
                        models = load_models(prnet, renderer)
                job = partial(serial_jobs, split=split, models=models, slots=slots, spread_train=spread_train)

            print(f"PREP_WORKERS {workers} | {count} {split} videos remaining", flush=True)
            archive = resources.enter_context(tarfile.open(archive_path, "r:"))
            progress = resources.enter_context(Progress(f"{split} prepare missing videos", count, "videos"))
            for done, (local, access, (observations, failure)) in enumerate(
                    job(archive, scratch, rendered, waiting), 1):
                if failure:
                    failures.append(failure)
                    print(json.dumps(failure), flush=True)
                else:
                    if rendered != output:
                        for name in video_assets(observations, split, local.stem, access, slots):
                            target = output / name
                            target.parent.mkdir(parents=True, exist_ok=True)
                            (rendered / name).replace(target)
                    publish_video(split_cache / f"{local.stem}.zip", output, split, local.stem, access, observations, slots)
                    rows.extend(observations)
                local.unlink()
                progress.update(done)
        failures.extend({"split": split, "video": video, "error": "missing AVI"} for video in sorted(waiting))
    manifest = {"profile": "full" if full else "expanded", "slots": list(PILOT_SLOTS), "failures": failures,
                "protocol_sha256": protocol_digest, "source": {"prnet": PRNET_COMMIT, "renderer": DEPTH_COMMIT},
                "weight_sha256": WEIGHT_SHA, "weight_index_sha256": INDEX_SHA,
                "frames": sorted(rows, key=lambda row: (row["split"], row["video_id"], row["slot"]))}
    if full:
        manifest["train_slots"] = list(FULL_TRAIN_SLOTS)
    temporary_manifest = manifest_path.with_suffix(".json.part")
    temporary_manifest.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    temporary_manifest.replace(manifest_path)
    if failures:
        raise ValueError(f"Preparation incomplete for {len(failures)} videos. See {output / 'smoke_summary.json'}")
    print("CDCN_EXPANDED_DATA_READY", len(rows), "frames", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("data", "cache", "output", "prnet", "renderer"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--dev-cache", type=Path)
    parser.add_argument("--stage-dir", type=Path)
    parser.add_argument("--restore-only", action="store_true")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--splits", nargs="+", choices=("Train", "Dev", "Test"), default=("Train", "Dev"))
    prepare(**vars(parser.parse_args()))
