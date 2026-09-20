"""Verify the exact source, ledger, and derived manifest bytes used for materialization."""
import argparse

from deepface_pad.depth_jobs import verify_depth_manifest_provenance

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--source", required=True, help="official-protocol source manifest")
parser.add_argument("--ledger", required=True, help="completed depth_status.csv")
parser.add_argument("--derived", required=True, help="materialized depth manifest")
parser.add_argument("--provenance", help="provenance JSON path (default: <derived>.provenance.json)")
args = parser.parse_args()

payload = verify_depth_manifest_provenance(
    args.source,
    args.ledger,
    args.derived,
    provenance_path=args.provenance,
)
print(
    f"verified sha256 provenance for {payload['rows']} rows "
    f"(bona_fide={payload['bona_fide']}, attack={payload['attack']})"
)
