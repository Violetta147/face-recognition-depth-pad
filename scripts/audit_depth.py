import argparse
import json
from pathlib import Path

from deepface_pad.depth_qa import audit_depth_targets

parser = argparse.ArgumentParser(description="Audit pseudo-depth targets referenced by a PAD manifest")
parser.add_argument("manifest")
parser.add_argument("--data-root", required=True)
parser.add_argument("--report", help="optional JSON report path")
parser.add_argument("--zero-tolerance", type=float, default=1e-6)
args = parser.parse_args()

report = audit_depth_targets(args.manifest, args.data_root, args.zero_tolerance)
rendered = json.dumps(report, indent=2, sort_keys=True)
if args.report:
    destination = Path(args.report)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(rendered + "\n", encoding="utf-8")
print(rendered)
if not report["valid"]:
    raise SystemExit(1)
