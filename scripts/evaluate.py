import argparse

from deepface_pad.evaluate import evaluate_file

parser = argparse.ArgumentParser()
parser.add_argument("scores")
parser.add_argument("--output", default="metrics.json")
parser.add_argument("--threshold", type=float)
parser.add_argument("--aggregation", choices=["mean", "median"], default="mean")
args = parser.parse_args()
print(evaluate_file(args.scores, args.output, args.threshold, args.aggregation))
