"""Archive prepared Colab data on private Drive and restore it to local disk."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import uuid
import zipfile

from .progress import Progress

INDEX = "CACHE_INDEX.json"
SPLIT_ARCHIVES = {"train": ("Train_files.tar", 37753662976), "val": ("Dev_files.tar", 28151992320),
                  "test": ("Test_files.tar", 39211162112)}


def file_hash(path):
    with path.open("rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest()


def copy_progress(source, target, label, expected_bytes=None):
    source, target = Path(source), Path(target)
    stat = source.stat()
    if expected_bytes is not None and stat.st_size != expected_bytes:
        raise ValueError(f"unexpected size for {source}: {stat.st_size} bytes")
    if target.is_file() and target.stat().st_size == stat.st_size and target.stat().st_mtime_ns == stat.st_mtime_ns:
        print(f"Reusing {target}", flush=True)
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{uuid.uuid4().hex}.part")
    try:
        with (source.open("rb") as incoming, temporary.open("xb") as outgoing,
              Progress(label, stat.st_size, "bytes") as progress):
            copied = 0
            while block := incoming.read(16 * 2**20):
                outgoing.write(block)
                copied += len(block)
                progress.update(copied)
            if copied != stat.st_size or source.stat().st_mtime_ns != stat.st_mtime_ns:
                raise OSError(f"incomplete copy or source changed: {source}")
        os.utime(temporary, ns=(stat.st_atime_ns, stat.st_mtime_ns))
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
    return target


def save_cache(root, archive, paths, identity):
    root, archive = Path(root).resolve(), Path(archive)
    names = sorted({Path(path).resolve().relative_to(root).as_posix() for path in paths})
    if not names or INDEX in names:
        raise ValueError("cache requires explicit data files")
    archive.parent.mkdir(parents=True, exist_ok=True)
    temp = archive.with_name(f".{archive.name}.{uuid.uuid4().hex}.part")
    try:
        with zipfile.ZipFile(temp, "x", compression=zipfile.ZIP_STORED) as bundle:
            with Progress(f"Save {archive.name}", len(names), "files") as progress:
                hashes = {}
                for number, name in enumerate(names, 1):
                    path = root / name
                    digest = hashlib.sha256()
                    with path.open("rb") as incoming, bundle.open(name, "w", force_zip64=True) as outgoing:
                        while block := incoming.read(1024 * 1024):
                            digest.update(block)
                            outgoing.write(block)
                    hashes[name] = digest.hexdigest()
                    progress.update(number)
                bundle.writestr(INDEX, json.dumps({"identity": identity, "sha256": hashes}, sort_keys=True))
        temp.replace(archive)
    finally:
        temp.unlink(missing_ok=True)


def restore_cache(root, archive, identity):
    root = Path(root).resolve()
    with zipfile.ZipFile(archive) as bundle:
        index = json.loads(bundle.read(INDEX))
        if index["identity"] != identity:
            raise ValueError(f"cache settings differ: {archive}")
        hashes = index["sha256"]
        if sorted(bundle.namelist()) != sorted([INDEX, *hashes]):
            raise ValueError(f"unexpected cache members: {archive}")
        for name in hashes:
            destination = (root / name).resolve()
            if destination == root or not destination.is_relative_to(root):
                raise ValueError(f"invalid cache path: {name}")
        with Progress(f"Restore {Path(archive).name}", len(hashes), "files") as progress:
            # Load manifests and ledgers after the PNG/NPY files have been verified.
            for number, name in enumerate(sorted(hashes, key=lambda value: (Path(value).suffix not in {".png", ".npy"}, value)), 1):
                destination = (root / name).resolve()
                expected = hashes[name]
                if destination.is_file() and file_hash(destination) == expected:
                    progress.update(number)
                    continue
                if destination.exists():
                    raise ValueError(f"local cache differs, choose a fresh destination: {destination}")
                destination.parent.mkdir(parents=True, exist_ok=True)
                temp = destination.with_name(f".{destination.name}.{uuid.uuid4().hex}.part")
                try:
                    with bundle.open(name) as source, temp.open("xb") as target:
                        shutil.copyfileobj(source, target, length=1024 * 1024)
                    if file_hash(temp) != expected:
                        raise ValueError(f"cache checksum mismatch: {name}")
                    temp.replace(destination)
                finally:
                    temp.unlink(missing_ok=True)
                progress.update(number)


def depth_identity(root, rgb_manifest, worker_metadata, config_files):
    import csv

    metadata = json.loads(worker_metadata.read_text(encoding="utf-8"))
    required = {"git_commit", "config_sha256", "worker_script_sha256", "backend", "mode", "output_size"}
    if not required.issubset(metadata):
        raise ValueError("3DDFA worker metadata is incomplete")
    if not config_files or len({path.name for path in config_files}) != len(config_files):
        raise ValueError("provide unique names for 3DDFA model weights/config assets")
    assets = {path.name: file_hash(path) for path in config_files}
    if assets.get(metadata.get("config_file")) != metadata["config_sha256"]:
        raise ValueError("3DDFA config asset must match the worker metadata")
    with rgb_manifest.open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    rgb = hashlib.sha256()
    with Progress("Verify RGB for depth cache", len(rows), "frames") as progress:
        for number, row in enumerate(rows, 1):
            image = (root / row["image_path"]).resolve()
            if not image.is_relative_to(root):
                raise ValueError(f"RGB path outside data root: {image}")
            digest = file_hash(image)
            if row.get("image_sha256") and row["image_sha256"] != digest:
                raise ValueError(f"RGB content changed: {image}")
            rgb.update(digest.encode("ascii"))
            progress.update(number)
    return {"kind": "depth", "rgb_manifest_sha256": file_hash(rgb_manifest), "rgb_content_sha256": rgb.hexdigest(),
            "worker": metadata, "assets": assets}


def prepare_oulu_split(data, workspace, backups, split, frames, pilot, run, backup=True):
    import csv
    import cv2
    from .oulu_npu import CROP_VERSION, expected_ids

    name, expected_bytes = SPLIT_ARCHIVES[split]
    source = data / name
    protocol = data / "Protocols.tar"
    detector = workspace / "yunet.onnx"
    archives = workspace / "archives"
    cache = workspace / "cache"
    stat = source.stat()
    if stat.st_size != expected_bytes:
        raise ValueError(f"unexpected size for {source}: {stat.st_size}")
    identity = {"crop_version": CROP_VERSION, "archive": name, "archive_bytes": stat.st_size,
                "archive_mtime_ns": stat.st_mtime_ns, "detector_sha256": file_hash(detector),
                "opencv": cv2.__version__, "frames_per_video": frames, "protocol": 1, "fold": None,
                "pilot": pilot, "split": split, "protocol_sha256": file_hash(protocol)}
    key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()[:20]
    snapshot = backups / f"rgb-p1-{split}-{key}.zip"
    manifest = cache / ("p1-pilot" if pilot else "p1") / f"{split}.csv"
    summary = manifest.with_suffix(".json")
    if snapshot.is_file() and not (summary.is_file() and manifest.is_file()):
        local_snapshot = copy_progress(snapshot, workspace / snapshot.name, f"Download {snapshot.name}")
        restore_cache(cache, local_snapshot, identity)
        local_snapshot.unlink()
    count = 30 if pilot else len(expected_ids(1, None, split))

    def matches():
        if not summary.is_file() or not manifest.is_file():
            return False
        meta = json.loads(summary.read_text(encoding="utf-8"))
        return (all(meta.get(field) == value for field, value in identity.items())
                and (meta["videos"], meta["frames"]) == (count, count * frames)
                and meta["manifest_sha256"] == file_hash(manifest))

    if not matches():
        copy_progress(protocol, archives / protocol.name, "Copy protocol lists")
        copy_progress(source, archives / name, f"Copy {name}", expected_bytes)
        run("deepface_pad.oulu_npu", "--drive", archives, "--root", cache, "--detector", detector,
            "--split", split, "--frames", frames, *(["--pilot"] if pilot else []))
        if not matches():
            raise ValueError(f"unexpected prepared manifest: {manifest}")
    if backup and not pilot and not snapshot.is_file():
        with manifest.open(encoding="utf-8", newline="") as file:
            rows = list(csv.DictReader(file))
        paths = [manifest, summary]
        with Progress(f"{split}: verify RGB before saving", len(rows), "frames") as progress:
            for number, row in enumerate(rows, 1):
                image = cache / row["image_path"]
                if file_hash(image) != row["image_sha256"]:
                    raise ValueError(f"invalid crop: {image}")
                paths.extend([image, image.with_name("frames.json")])
                progress.update(number)
        local_snapshot = workspace / snapshot.name
        save_cache(cache, local_snapshot, paths, identity)
        copy_progress(local_snapshot, snapshot, f"Upload {snapshot.name}")
        local_snapshot.unlink()
    print(f"{split}: {count:,} videos / {count * frames:,} frames | {manifest}", flush=True)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("save", "restore"))
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--rgb-manifest", type=Path, required=True)
    parser.add_argument("--worker-metadata", type=Path, required=True)
    parser.add_argument("--asset", type=Path, action="append", required=True)
    parser.add_argument("--depth-dir", type=Path)
    parser.add_argument("--derived-manifest", type=Path)
    parser.add_argument("--local-dir", type=Path, help="temporary local disk for the snapshot ZIP")
    args = parser.parse_args()
    root = args.root.resolve()
    identity = depth_identity(root, args.rgb_manifest, args.worker_metadata, args.asset)
    identity["data_root"] = str(root)
    if args.action == "save":
        if args.depth_dir is None or not args.depth_dir.is_dir() or args.depth_dir.resolve() == root:
            parser.error("save requires --depth-dir")
        paths = [path for path in args.depth_dir.rglob("*") if path.is_file()
                 and path.suffix in {".npy", ".csv", ".json"}]
        if args.derived_manifest:
            from .depth_jobs import depth_provenance_path

            paths.extend([args.derived_manifest, depth_provenance_path(args.derived_manifest)])
        with tempfile.TemporaryDirectory(dir=args.local_dir) as temp:
            local = Path(temp) / args.archive.name
            save_cache(root, local, paths, identity)
            copy_progress(local, args.archive, f"Upload {args.archive.name}")
    else:
        with tempfile.TemporaryDirectory(dir=args.local_dir) as temp:
            local = Path(temp) / args.archive.name
            copy_progress(args.archive, local, f"Download {args.archive.name}")
            restore_cache(root, local, identity)


if __name__ == "__main__":
    main()
