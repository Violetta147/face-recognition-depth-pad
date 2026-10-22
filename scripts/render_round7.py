"""Render only the predeclared Round 7 cases on CPU."""
import argparse
import json
from pathlib import Path
from deepface_pad.round7_figures import figures

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project", default=".")
    p.add_argument("--drive", default="G:/My Drive/face-pad")
    p.add_argument("--analysis", default="reports/round7/analysis")
    p.add_argument("--output", default="reports/round7/figures")
    p.add_argument("--artifacts", default="artifacts/round7/figures")
    p.add_argument("--score-mode",choices=["strict","diagnostic"],default="strict")
    a = p.parse_args()
    try:
        print(figures(a.project, a.drive, a.analysis, a.output, a.artifacts, a.score_mode)["scope"])
    except Exception as exc:
        folder = Path(a.artifacts)
        folder.mkdir(parents=True,exist_ok=True)
        receipt = folder / "failure.json"
        if not receipt.exists():
            receipt.write_text(json.dumps({"status":"failed; partial files preserved", "error":str(exc)},indent=2)+"\n",encoding="utf-8")
        raise
