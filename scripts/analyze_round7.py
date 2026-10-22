"""Analyze frozen E1/E3 scores; never run or modify a checkpoint."""
import argparse
from deepface_pad.round7 import analyze

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", default=".")
    parser.add_argument("--evidence", default="artifacts/round6-test-audit-20261022")
    parser.add_argument("--output", default="reports/round7/analysis")
    args = parser.parse_args()
    result = analyze(args.project, args.evidence, args.output)
    print(result["paired_counts"], "selected cases:", result["selected_cases"])
