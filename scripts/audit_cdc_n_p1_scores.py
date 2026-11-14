"""Recalculate saved video scores at the public CDCN evaluator's Dev threshold."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_curve


def load_scores(path):
    frame = pd.read_csv(path)
    if (frame.video_id.isna().any() or frame.video_id.duplicated().any()
            or set(frame.label) != {0, 1} or not np.isfinite(frame.score).all()):
        raise ValueError(f"{path} requires one finite score per video and both labels")
    return frame


def score(dev, test):
    # The public code picks the first ROC point nearest to FPR = FNR.
    fpr, tpr, thresholds = roc_curve(dev.label, dev.score, pos_label=1)
    threshold = float(thresholds[np.argmin(np.abs(tpr + fpr - 1.0))])
    if not np.isfinite(threshold):
        raise ValueError("Dev did not yield a finite threshold")

    def rates(frame):
        # The public evaluator uses strict >, even though sklearn's ROC uses >=.
        live = frame.loc[frame.label.eq(1), "score"]
        attack = frame.loc[frame.label.eq(0), "score"]
        rejected = int(live.le(threshold).sum())
        accepted = int(attack.gt(threshold).sum())
        bpcer, apcer = rejected / len(live), accepted / len(attack)
        return {"apcer_pooled": apcer, "bpcer": bpcer, "acer_pooled": (apcer + bpcer) / 2,
                "live_rejected": rejected, "live_total": len(live),
                "attack_accepted": accepted, "attack_total": len(attack)}

    return {"threshold_from_dev": threshold, "dev": rates(dev), "test": rates(test)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dev", type=Path, required=True)
    parser.add_argument("--test", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(score(load_scores(args.dev), load_scores(args.test)), indent=2))


if __name__ == "__main__":
    main()
