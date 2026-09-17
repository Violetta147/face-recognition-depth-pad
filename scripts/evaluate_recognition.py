from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from deepface_pad.evaluation.recognition_metrics import select_threshold  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Choose an UNKNOWN threshold from genuine/impostor validation scores"
    )
    parser.add_argument("scores_csv", help="CSV columns: score,is_genuine")
    parser.add_argument("--output", default="reports/tables/recognition_threshold.md")
    args = parser.parse_args()
    scores, labels = [], []
    with Path(args.scores_csv).open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            scores.append(float(row["score"]))
            labels.append(row["is_genuine"].strip().lower() in {"1", "true", "yes"})
    report = select_threshold(np.asarray(scores), np.asarray(labels))
    output = PROJECT_ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    content = (
        "# Recognition threshold (validation only)\n\n"
        "| Threshold | Genuine accept rate | Impostor reject rate | Balanced accuracy |\n"
        "|---:|---:|---:|---:|\n"
        f"| {report.threshold:.4f} | {report.true_accept_rate:.3f} | "
        f"{report.true_reject_rate:.3f} | {report.balanced_accuracy:.3f} |\n\n"
        "> Copy the selected threshold to `configs/demo.yaml` only after checking "
        "that enrollment and validation came from separate sessions.\n"
    )
    output.write_text(content, encoding="utf-8")
    print(content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

