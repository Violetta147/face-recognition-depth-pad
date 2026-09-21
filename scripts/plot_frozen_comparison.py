"""Plot frozen E0 versus official-E1 curves and video-score distributions."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--e0-run", required=True)
    parser.add_argument("--e1-run", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    e0_run = Path(args.e0_run)
    e1_run = Path(args.e1_run)
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)

    runs = [
        ("E0 MobileNetV3", e0_run, "#2878B5"),
        ("E1 Official CDCN", e1_run, "#D95319"),
    ]
    for _, run_dir, _ in runs:
        required = ("train_log.csv", "test_scores.csv", "threshold.json")
        missing = [name for name in required if not (run_dir / name).is_file()]
        if missing:
            raise SystemExit(f"{run_dir} is missing: {missing}")

    figure, axes = plt.subplots(1, 2, figsize=(13, 4.5))
    for axis, (name, run_dir, color) in zip(axes, runs):
        log = pd.read_csv(run_dir / "train_log.csv")
        axis.plot(log["epoch"], log["train_loss"], label="train", color=color)
        axis.plot(log["epoch"], log["val_loss"], label="validation", color="black", linestyle="--")
        best_index = log["val_loss"].idxmin()
        best_epoch = int(log.loc[best_index, "epoch"])
        best_loss = float(log.loc[best_index, "val_loss"])
        axis.scatter([best_epoch], [best_loss], color="red", zorder=3, label=f"best epoch {best_epoch}")
        axis.set_title(name)
        axis.set_xlabel("Epoch")
        axis.set_ylabel("Loss")
        axis.grid(alpha=0.25)
        axis.legend()
    figure.tight_layout()
    curves = output / "e0-official-e1-training-curves.png"
    figure.savefig(curves, dpi=200, bbox_inches="tight")
    plt.close(figure)

    figure, axes = plt.subplots(1, 2, figsize=(13, 4.5))
    for axis, (name, run_dir, _) in zip(axes, runs):
        threshold = float(json.loads((run_dir / "threshold.json").read_text(encoding="utf-8"))["threshold"])
        scores = pd.read_csv(run_dir / "test_scores.csv")
        attack = scores.loc[scores["label"] == 0, "score"]
        live = scores.loc[scores["label"] == 1, "score"]
        axis.hist(attack, bins=30, alpha=0.65, label=f"attack (n={len(attack)})", color="#D95319")
        axis.hist(live, bins=30, alpha=0.65, label=f"bona fide (n={len(live)})", color="#2878B5")
        axis.axvline(threshold, color="black", linestyle="--", label=f"threshold={threshold:.4f}")
        axis.set_title(name)
        axis.set_xlabel("Video-level live score")
        axis.set_ylabel("Number of videos")
        axis.grid(alpha=0.20)
        axis.legend()
    figure.tight_layout()
    distributions = output / "e0-official-e1-test-score-distributions.png"
    figure.savefig(distributions, dpi=200, bbox_inches="tight")
    plt.close(figure)

    print(f"training_curves={curves}")
    print(f"score_distributions={distributions}")


if __name__ == "__main__":
    main()
