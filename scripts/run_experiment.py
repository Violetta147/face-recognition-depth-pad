import argparse

from deepface_pad.train import run

parser = argparse.ArgumentParser()
parser.add_argument("config")
args = parser.parse_args()
print(run(args.config))
