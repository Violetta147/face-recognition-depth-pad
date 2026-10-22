"""Evaluate a frozen depth model against its recorded pseudo-depth cache."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
import torch
import yaml
from torch.utils.data import DataLoader

from deepface_pad.data import PadDataset, manifest_checksum
from deepface_pad.depth_evaluation import depth_error_rows, summarize_depth_errors
from deepface_pad.preflight import inspect_training_inputs
from deepface_pad.train import build_model


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--split", choices=["val", "test"], default="val")
    args = parser.parse_args()
    folder = Path(args.run_dir)
    cfg = yaml.safe_load((folder / "config.yaml").read_text(encoding="utf-8"))
    saved = json.loads((folder / "depth_input_snapshot.json").read_text())
    _, current = inspect_training_inputs(cfg)
    if current is None or saved["files"] != current["files"] or saved["depth_audit"]["artifact_checksums"] != current["depth_audit"]["artifact_checksums"]:
        raise ValueError("depth targets/provenance changed since training")
    dataset = PadDataset(cfg["data"]["manifest"], cfg["data"]["root"], args.split,
                         cfg["data"].get("image_size", 256), augment=False, require_depth=True,
                         normalization=cfg["data"].get("normalization", "imagenet"))
    loader = DataLoader(dataset, batch_size=cfg["training"].get("batch_size", 8),
                        shuffle=False, num_workers=cfg["training"].get("workers", 0))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = build_model(cfg).to(device)
    model.load_state_dict(torch.load(folder / "best.ckpt", map_location=device, weights_only=False)["model"])
    model.eval()
    rows = []
    with torch.no_grad():
        for batch in loader:
            output = model(batch["image"].to(device))
            rows.extend(depth_error_rows(output["depth"].cpu(), batch["depth"], batch["label"],
                                         batch["sample_id"], batch["video_id"]))
    frame = pd.DataFrame(rows)
    report = summarize_depth_errors(frame)
    report.update(split=args.split, checkpoint_sha256=manifest_checksum(folder / "best.ckpt"),
                  manifest_sha256=manifest_checksum(cfg["data"]["manifest"]))
    frame.to_csv(folder / f"depth_{args.split}_errors.csv", index=False)
    (folder / f"depth_{args.split}_metrics.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
