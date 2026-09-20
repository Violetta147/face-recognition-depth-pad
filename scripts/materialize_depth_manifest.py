"""Create a derived manifest from a completed, verified pseudo-depth ledger."""
import argparse

from deepface_pad.depth_jobs import materialize_depth_manifest

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("manifest", help="source official-protocol manifest (never modified)")
parser.add_argument("--ledger", required=True, help="completed depth_status.csv")
parser.add_argument("--data-root", required=True, help="root containing images and generated depth maps")
parser.add_argument("--output", required=True, help="new derived manifest path")
parser.add_argument("--provenance", help="provenance JSON path (default: <output>.provenance.json)")
parser.add_argument("--zero-tolerance", type=float, default=1e-6)
args = parser.parse_args()

counts = materialize_depth_manifest(
    args.manifest,
    args.ledger,
    args.data_root,
    args.output,
    provenance_path=args.provenance,
    zero_tolerance=args.zero_tolerance,
)
provenance = args.provenance or f"{args.output}.provenance.json"
print(
    f"wrote {counts['rows']} rows to {args.output} "
    f"(bona_fide={counts['bona_fide']}, attack={counts['attack']}); "
    f"provenance={provenance}"
)
