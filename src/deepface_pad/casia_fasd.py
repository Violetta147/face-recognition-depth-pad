from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


VIDEO_METADATA = {
    "1": (1, "live", "normal"),
    "2": (1, "live", "low"),
    "HR_1": (1, "live", "high"),
    "3": (0, "warped_photo", "normal"),
    "4": (0, "warped_photo", "low"),
    "HR_2": (0, "warped_photo", "high"),
    "5": (0, "cut_photo", "normal"),
    "6": (0, "cut_photo", "low"),
    "HR_3": (0, "cut_photo", "high"),
    "7": (0, "video_replay", "normal"),
    "8": (0, "video_replay", "low"),
    "HR_4": (0, "video_replay", "high"),
}
EXPECTED_TOKENS = frozenset(VIDEO_METADATA)
FILENAME = re.compile(
    r"s(?P<subject>\d+)v(?P<video>(?:HR_)?\d+)f(?P<frame>\d+)\.png$"
)


@dataclass(frozen=True)
class CasiaFrame:
    source_split: str
    source_subject: int
    video_token: str
    frame_index: int
    image_path: str


def parse_frame_path(path: Path, root: Path) -> CasiaFrame | None:
    """Parse original Kaggle frames; return None for its bs/fs derivatives."""
    match = FILENAME.fullmatch(path.name)
    if not match:
        return None
    relative = path.relative_to(root)
    if len(relative.parts) != 3:
        raise ValueError(f"unexpected CASIA-FASD path: {relative}")
    source_split, folder_label = relative.parts[0], relative.parts[1]
    if source_split not in {"train", "test"} or folder_label not in {"live", "spoof"}:
        raise ValueError(f"unexpected split/label folders: {relative}")
    video_token = match.group("video")
    if video_token not in VIDEO_METADATA:
        raise ValueError(f"unknown CASIA-FASD video token: {video_token}")
    protocol_label = "live" if VIDEO_METADATA[video_token][0] == 1 else "spoof"
    # The Kaggle copy places HR_1 (high-quality bona fide) under spoof.
    if folder_label != protocol_label and video_token != "HR_1":
        raise ValueError(f"folder label contradicts protocol mapping: {relative}")
    return CasiaFrame(
        source_split=source_split,
        source_subject=int(match.group("subject")),
        video_token=video_token,
        frame_index=int(match.group("frame")),
        image_path=relative.as_posix(),
    )


def _uniform_sample(frames: list[CasiaFrame], count: int) -> list[CasiaFrame]:
    frames = sorted(frames, key=lambda frame: frame.frame_index)
    if count <= 0 or len(frames) <= count:
        return frames
    indices = [round(index * (len(frames) - 1) / (count - 1)) for index in range(count)]
    return [frames[index] for index in indices]


def build_manifest(
    data_root: str | Path,
    frames_per_video: int = 20,
    val_subjects: frozenset[int] = frozenset({4, 9, 14, 19}),
) -> pd.DataFrame:
    root = Path(data_root)
    grouped: dict[tuple[str, int, str], list[CasiaFrame]] = defaultdict(list)
    for path in root.rglob("*.png"):
        parsed = parse_frame_path(path, root)
        if parsed is not None:
            grouped[(parsed.source_split, parsed.source_subject, parsed.video_token)].append(parsed)

    expected_subjects = {"train": set(range(1, 21)), "test": set(range(1, 31))}
    found_subjects = {
        split: {subject for source_split, subject, _ in grouped if source_split == split}
        for split in ("train", "test")
    }
    if found_subjects != expected_subjects:
        raise ValueError(f"unexpected source subjects: {found_subjects}")
    for split, subjects in expected_subjects.items():
        for subject in subjects:
            tokens = {token for source_split, source_subject, token in grouped if source_split == split and source_subject == subject}
            if tokens != EXPECTED_TOKENS:
                raise ValueError(f"missing/extra videos for {split} subject {subject}: {sorted(tokens)}")

    rows: list[dict[str, object]] = []
    for (source_split, source_subject, video_token), frames in sorted(grouped.items()):
        if source_split == "train":
            subject_number = source_subject
            split = "val" if source_subject in val_subjects else "train"
        else:
            subject_number = source_subject + 20
            split = "test"
        subject_id = f"casia_s{subject_number:02d}"
        video_id = f"{subject_id}_v{video_token}"
        label, attack_type, quality = VIDEO_METADATA[video_token]
        for frame in _uniform_sample(frames, frames_per_video):
            rows.append(
                {
                    "sample_id": f"{video_id}_f{frame.frame_index:06d}",
                    "split": split,
                    "subject_id": subject_id,
                    "video_id": video_id,
                    "frame_index": frame.frame_index,
                    "image_path": frame.image_path,
                    "depth_path": "",
                    "label": label,
                    "attack_type": attack_type,
                    "quality": quality,
                    "source_split": source_split,
                }
            )
    manifest = pd.DataFrame(rows)
    if manifest.empty:
        raise ValueError(f"no CASIA-FASD frames found under {root}")
    return manifest.sort_values(["split", "subject_id", "video_id", "frame_index"]).reset_index(drop=True)


def write_manifests(manifest: pd.DataFrame, output_dir: str | Path) -> None:
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    manifest.to_csv(destination / "casia_fasd_debug.csv", index=False)
    for split in ("train", "val", "test"):
        manifest[manifest["split"] == split].to_csv(destination / f"casia_fasd_{split}.csv", index=False)
