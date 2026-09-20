"""Create a resumable 3DDFA work list and protocol-correct attack targets."""
import argparse

from deepface_pad.depth_jobs import prepare_depth_jobs

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("manifest")
parser.add_argument("--data-root", required=True)
parser.add_argument("--output-root", required=True)
parser.add_argument("--ledger", help="status CSV (default: OUTPUT_ROOT/depth_status.csv)")
parser.add_argument(
    "--failure-report",
    help="optional 3DDFA failure CSV with sample_id,error columns",
)
parser.add_argument(
    "--retry-failed",
    action="store_true",
    help="explicitly move previously failed bona fide rows back to the pending list",
)
args = parser.parse_args()

counts = prepare_depth_jobs(
    args.manifest,
    args.data_root,
    args.output_root,
    ledger_path=args.ledger,
    failure_report=args.failure_report,
    retry_failed=args.retry_failed,
)
summary = ", ".join(f"{status}={count}" for status, count in counts.items() if count)
print(summary or "manifest is empty")
