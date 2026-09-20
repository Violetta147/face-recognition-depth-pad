import argparse

from deepface_pad.data import validate_manifest

parser = argparse.ArgumentParser()
parser.add_argument("manifest")
parser.add_argument("--data-root", required=True)
parser.add_argument("--subject-disjoint", action="store_true")
parser.add_argument("--skip-files", action="store_true")
parser.add_argument("--require-depth", action="store_true", help="require a pseudo-depth path for every bona fide sample")
args = parser.parse_args()
errors = validate_manifest(args.manifest, args.data_root, args.subject_disjoint, not args.skip_files, args.require_depth)
if errors:
    raise SystemExit("Manifest invalid:\n- " + "\n- ".join(errors))
print("Manifest valid")
