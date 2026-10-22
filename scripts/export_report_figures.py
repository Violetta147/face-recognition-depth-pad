"""Export frozen E0–E4 report figures. No training and no test retuning."""
from __future__ import annotations

import argparse
import platform
from pathlib import Path

import matplotlib
import torch

from deepface_pad.figure_data import load_evidence, sha256
from deepface_pad.report_figures import FigureWriter, numeric_figures
from deepface_pad.figure_inference import depth_figures, benchmark_figures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-dir",required=True)
    parser.add_argument("--manifest",required=True)
    parser.add_argument("--freeze",required=True)
    parser.add_argument("--output-dir",required=True)
    parser.add_argument("--data-root",default="/content/datasets/casia-fasd")
    parser.add_argument("--dataset-zip",default="/content/drive/MyDrive/face-pad/casia-fasd.zip")
    parser.add_argument("--depth-tar",default="/content/drive/MyDrive/face-pad/depth-checkpoints/casia-fasd-depth-checkpoint.tar")
    parser.add_argument("--phase",choices=["numeric","all"],default="all")
    args = parser.parse_args()
    if args.phase == "all" and not torch.cuda.is_available():
        raise SystemExit("Full export needs a Colab GPU for bounded inference/timing. Use --phase numeric for CPU-only figures.")
    root = Path(__file__).resolve().parents[1]
    output = Path(args.output_dir).resolve()
    if output.is_relative_to(Path(args.runs_dir).resolve()):
        raise ValueError("output must be outside the frozen run directories")
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("Use a new output folder for each export")
    print("VERIFYING FROZEN INPUTS",flush=True)
    evidence = load_evidence(root,args.runs_dir,args.manifest,args.freeze)
    writer = FigureWriter(output,dpi=300)
    provenance = {"scope":"single-seed CASIA development; frozen scores, read-only checkpoints",
        "phase":args.phase,"python":platform.python_version(),"torch":str(torch.__version__),"matplotlib":matplotlib.__version__,
        "experiment_source_commit":evidence["freeze"]["source_commit"],"selected_variant":"E3",
        "manifest_sha256":evidence["manifest_sha256"],"source_files":evidence["source_files"],
        "figure_code_sha256":{str(p.relative_to(root)):sha256(p) for p in (
            root/"src/deepface_pad/figure_data.py",root/"src/deepface_pad/report_figures.py",root/"src/deepface_pad/figure_inference.py",Path(__file__))}}
    source_commit = root / "SOURCE_COMMIT.txt"
    if source_commit.is_file(): provenance["figure_source_commit"] = source_commit.read_text().strip()
    numeric_figures(evidence,writer)
    if args.phase == "all":
        device = torch.device("cuda")
        provenance.update(depth_figures(evidence,writer,args.data_root,args.dataset_zip,args.depth_tar,device))
        provenance.update(benchmark_figures(evidence,writer,device))
    writer.finish(provenance)
    print("FIGURES_COMPLETE",len(writer.items),"figures in",output,flush=True)


if __name__ == "__main__":
    main()
