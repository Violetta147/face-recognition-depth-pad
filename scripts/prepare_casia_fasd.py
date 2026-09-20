import argparse

from deepface_pad.casia_fasd import build_manifest, write_manifests
from deepface_pad.data import validate_manifest


parser = argparse.ArgumentParser(description="Build a protocol-aware debug manifest from the immada/casia-fasd Kaggle copy.")
parser.add_argument("--data-root", required=True)
parser.add_argument("--output-dir", default="data/manifests")
parser.add_argument("--frames-per-video", type=int, default=20)
parser.add_argument("--val-subjects", default="4,9,14,19")
args = parser.parse_args()

validation_subjects = frozenset(int(value) for value in args.val_subjects.split(",") if value)
if not validation_subjects or not validation_subjects.issubset(set(range(1, 21))):
    raise SystemExit("--val-subjects must select at least one source training subject from 1 through 20")

manifest = build_manifest(args.data_root, args.frames_per_video, validation_subjects)
write_manifests(manifest, args.output_dir)
errors = validate_manifest(
    f"{args.output_dir}/casia_fasd_debug.csv",
    args.data_root,
    require_subject_disjoint=True,
    check_files=True,
)
if errors:
    raise SystemExit("Generated manifest is invalid:\n- " + "\n- ".join(errors))
print(manifest.groupby(["split", "label"])[["sample_id", "video_id"]].nunique())
print(f"wrote {len(manifest)} sampled frames from {manifest.video_id.nunique()} videos")
