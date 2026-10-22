"""Bounded illustrations for the predeclared Round 7 cases, never full scoring."""
from __future__ import annotations

import json
import io
import hashlib
from pathlib import Path
import shutil
import zipfile
import tarfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
import yaml

from .data import PadDataset
from .figure_data import safe_destination
from .figure_inference import load_model, un_normalize_rgb
from .round7 import csv, read, sha


def checked_copy(source, destination, expected):
    if sha(source) != expected:
        raise ValueError(f"changed source target: {source}")
    destination = Path(destination)
    if destination.exists():
        if sha(destination) != expected:
            raise ValueError(f"changed local target: {destination}")
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    with Path(source).open("rb") as src, destination.open("xb") as dst:
        shutil.copyfileobj(src, dst)


def restore_target(source, destination, expected, label, archive):
    """Restore live targets or serialized frozen attack zeros; require exact SHA."""
    if Path(source).is_file():
        checked_copy(source, destination, expected)
        return "existing snapshot-verified target"
    member_name = "depth/" + Path(destination).name
    try:
        member = archive.extractfile(member_name)
        payload = member.read() if member is not None else None
    except KeyError:
        payload = None
    if payload is None:
        if int(label) != 0:
            raise FileNotFoundError(f"missing live pseudo-depth: {member_name}")
        stream = io.BytesIO()
        np.save(stream, np.zeros((32,32), dtype=np.float32))
        payload = stream.getvalue()
        method = "deterministic serialization of frozen attack zero target; exact snapshot SHA verified"
    else:
        method = "original depth TAR member; exact snapshot SHA verified"
    if hashlib.sha256(payload).hexdigest() != expected:
        raise ValueError(f"restored target differs from snapshot: {member_name}")
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb") as stream:
        stream.write(payload)
    return method


def shared_limits(targets, predictions):
    values = list(targets) + list(predictions)
    if not all(np.isfinite(x).all() for x in values):
        raise ValueError("nonfinite depth")
    return [min(0., min(float(x.min()) for x in values)),
            max(1., max(float(x.max()) for x in values))]


def compare_frame_score(score, frozen_score, mode="strict"):
    if mode not in ("strict", "diagnostic"):
        raise ValueError("unknown score comparison mode")
    if not np.isfinite(score) or not np.isfinite(frozen_score):
        raise ValueError("nonfinite frame score")
    passed = bool(np.isclose(score, frozen_score, atol=1e-5, rtol=1e-4))
    if mode == "strict" and not passed:
        raise ValueError(f"bounded frame inference differs: {score} vs {frozen_score}")
    return {"score_reproduction_passed":passed, "comparison_atol":1e-5,
            "comparison_rtol":1e-4, "absolute_difference":abs(score-frozen_score)}


def figures(project, drive, analysis, output, artifacts, score_mode="strict"):
    project, drive, analysis, output, artifacts = map(Path, (project, drive, analysis, output, artifacts))
    if output.exists() or artifacts.exists():
        raise FileExistsError("use fresh output/artifacts directories")
    audit = read(project / "reports/ROUND_6_RESULTS_2026-10-22.json")
    cases = csv(analysis / "case_index.csv")
    # Selection is fixed by the prior committed CSV analysis, before image decoding.
    source_hashes = {str(analysis / "case_index.csv"): sha(analysis / "case_index.csv")}
    runs, snapshots = {}, {}
    for key, record in audit["runs"].items():
        folder = drive / "runs" / record["run_id"]
        for name in ("best.ckpt", "config.yaml", "depth_input_snapshot.json"):
            digest = sha(folder / name)
            if digest != record["hashes"][name]:
                raise ValueError(f"changed {key}/{name}")
            source_hashes[str(folder / name)] = digest
        cfg = yaml.safe_load((folder / "config.yaml").read_text(encoding="utf-8"))
        model, seed = key.split("_")
        if cfg["seed"] != int(seed) or cfg["data"]["normalization"] != "cdcn_official" or cfg["data"]["image_size"] != 256:
            raise ValueError("preprocessing/seed differs")
        if cfg["model"]["name"] != {"E1":"cdcn_official", "E3":"cdcn_official_head"}[model]:
            raise ValueError("wrong architecture")
        snapshot = read(folder / "depth_input_snapshot.json")
        if snapshot["files"]["derived_manifest"]["sha256"] != audit["manifest_sha256"]:
            raise ValueError("snapshot manifest differs")
        snapshots[key] = {x["sample_id"]: x["sha256"] for x in snapshot["depth_audit"]["artifact_checksums"]}
        runs[key] = {"folder": folder, "config": cfg}
    output.mkdir(parents=True)
    artifacts.mkdir(parents=True)
    inputs = artifacts / "inputs"
    provenance = {}
    archive_path = drive / "casia-fasd.zip"
    # New archive digest is provenance, not a claim of a registered original RGB hash.
    source_hashes[str(archive_path)] = sha(archive_path)
    depth_tar = drive / "depth-checkpoints/casia-fasd-depth-checkpoint.tar"
    source_hashes[str(depth_tar)] = sha(depth_tar)
    from .figure_data import DEPTH_TAR_SHA
    if source_hashes[str(depth_tar)] != DEPTH_TAR_SHA:
        raise ValueError("changed depth archive")
    with zipfile.ZipFile(archive_path) as archive, tarfile.open(depth_tar) as targets:
        for row in cases.drop_duplicates("sample_id").itertuples():
            sid = row.sample_id
            relevant = cases[cases.sample_id == sid]
            checksums = {snapshots[f"{model}_{int(seed)}"][sid] for seed in relevant.seed for model in ("E1", "E3")}
            if len(checksums) != 1:
                raise ValueError("target differs across runs")
            depth_path = safe_destination(inputs, row.depth_path)
            source = drive / "depth-checkpoints/casia-fasd" / Path(row.depth_path).name
            target_method = restore_target(source, depth_path, checksums.pop(), row.label, targets)
            rgb_path = safe_destination(inputs, row.image_path)
            rgb_path.parent.mkdir(parents=True, exist_ok=True)
            with rgb_path.open("xb") as stream:
                stream.write(archive.read(f"casia-fasd/{row.image_path}"))
            provenance[sid] = {"rgb_sha256": sha(rgb_path), "target_sha256": sha(depth_path),
                               "target_restoration":target_method,
                               "rgb_member": f"casia-fasd/{row.image_path}",
                               "rgb_identity": "ZIP member + CRC + newly recorded SHA; no preregistered per-RGB hash claimed"}
    manifest_path = output / "selected_manifest.csv"
    cases.drop_duplicates("sample_id").to_csv(manifest_path, index=False)
    dataset = PadDataset(manifest_path, inputs, "test", 256, augment=False,
                         require_depth=True, normalization="cdcn_official")
    samples = {str(dataset.rows.iloc[i].sample_id): dataset[i] for i in range(len(dataset))}
    for sid, sample in samples.items():
        provenance[sid]["input_tensor_sha256"] = hashlib.sha256(sample["image"].numpy().tobytes()).hexdigest()
        provenance[sid]["target_tensor_sha256"] = hashlib.sha256(sample["depth"].numpy().tobytes()).hexdigest()
    arrays, measures, predictions = {}, [], {}
    device = torch.device("cpu")
    torch.set_num_threads(2)
    for key, run in runs.items():
        model_name, seed = key.split("_")
        selected = cases[cases.seed == int(seed)]
        model = load_model(run, device)
        saved = csv(drive / "runs" / audit["runs"][key]["run_id"] / "test_frame_scores.csv").set_index("sample_id")
        # Saved frame score identity is checked separately from fresh bounded inference.
        saved_path = run["folder"] / "test_frame_scores.csv"
        if sha(saved_path) != audit["runs"][key]["hashes"]["test_frame_scores.csv"]:
            raise ValueError("saved frame scores changed")
        with torch.inference_mode():
            for row in selected.itertuples():
                sample = samples[row.sample_id]
                result = model(sample["image"][None])
                depth = result["depth"][0, 0].cpu().numpy().copy()
                score = float(result["score"].reshape(-1)[0])
                old_score = float(saved.loc[row.sample_id, "score"])
                comparison = compare_frame_score(score, old_score, score_mode)
                target = sample["depth"][0].numpy()
                prefix = f"{key}_{row.sample_id}"
                arrays[prefix + "_prediction"] = depth
                arrays[prefix + "_absolute_error"] = np.abs(depth - target)
                arrays[prefix + "_target"] = target
                predictions[(int(seed), row.sample_id, model_name)] = depth
                measures.append({"run_key":key, "sample_id":row.sample_id, "frame_score_new":score,
                                 "frame_score_frozen":old_score, **comparison,
                                 "selected_frame_pseudo_depth_mae":float(np.abs(depth-target).mean())})
        del model
        print("BOUNDED", key, len(selected), flush=True)
    limits = shared_limits([s["depth"][0].numpy() for s in samples.values()], predictions.values())
    error_max = max(float(x.max()) for k,x in arrays.items() if k.endswith("_absolute_error"))
    error_limits = [0, max(error_max, 1e-6)]
    raw_path = artifacts / "qualitative_arrays.npz"
    np.savez_compressed(raw_path, **arrays)
    pd.DataFrame(measures).to_csv(output / "bounded_inference.csv", index=False)
    for index, row in enumerate(cases.itertuples(), 1):
        sample = samples[row.sample_id]
        fig, axes = plt.subplots(2, 4, figsize=(13, 7), layout="constrained")
        for ax in axes.flat: ax.set_xticks([]); ax.set_yticks([])
        axes[0,0].imshow(un_normalize_rgb(sample["image"], "cdcn_official"))
        axes[0,0].set_title("RGB model input (256 x 256)")
        axes[0,1].imshow(sample["depth"][0], cmap="viridis", vmin=limits[0], vmax=limits[1], interpolation="nearest")
        axes[0,1].set_title("Pseudo-depth target (32 x 32)")
        for col, name in ((2,"E1"), (3,"E3")):
            pred = predictions[(row.seed, row.sample_id, name)]
            artist = axes[0,col].imshow(pred, cmap="viridis", vmin=limits[0], vmax=limits[1], interpolation="nearest")
            score, threshold = getattr(row,name+"_score"), getattr(row,name+"_threshold")
            decision = "Live" if score >= threshold else "Attack"
            axes[0,col].set_title(f"{name} predicted depth\nVIDEO: {decision}; s={score:.4f}, t={threshold:.4f}")
            error_artist = axes[1,col].imshow(np.abs(pred-sample["depth"][0].numpy()), cmap="magma", vmin=0, vmax=error_limits[1], interpolation="nearest")
            axes[1,col].set_title(name+" absolute pseudo-depth error")
        for ax in axes[1,:2]: ax.axis("off")
        axes[1,0].text(0, .9, f"Label: {'live' if row.label else 'attack'}\nType: {row.attack_type}\nQuality metadata: {row.quality}\nFrame index: {row.frame_index}\nRole: {row.role}", va="top", fontsize=11)
        axes[1,1].text(0, .9, "Illustration selected before RGB inspection.\nVideo decisions: frozen mean of 20 frames.\nNew CPU inference: one middle frame only.\nCPU frame scores may differ from CUDA.\nShared scales; no prediction clipping.\nPseudo-depth is not measured 3D truth.", va="top", fontsize=9)
        fig.colorbar(artist, ax=list(axes[0,1:]), shrink=.7, label="Normalized pseudo-depth units")
        fig.colorbar(error_artist, ax=list(axes[1,2:]), shrink=.7, label="Absolute error (pseudo-depth units)")
        fig.suptitle(f"Seed {row.seed} | {row.video_id} | {row.role}", fontsize=15)
        fig.savefig(output / f"case_{index:02d}_seed{row.seed}_{row.video_id}.png", dpi=160, facecolor="white")
        plt.close(fig)
    metadata = {"scope":"bounded CPU illustrations; frozen benchmark unchanged", "selected_cases":len(cases),
                "score_comparison_mode":score_mode,
                "frame_score_reproduction_mismatches":sum(not row["score_reproduction_passed"] for row in measures),
                "numeric_scope":"Diagnostic mode records failed original tolerances without widening them or claiming CUDA score reproduction. Cause unresolved; no original CUDA TF32 state captured.",
                "forward_count":len(measures), "device":"cpu", "torch":torch.__version__,
                "normalization":"RGB -> torchvision Resize(256,256), float /255, (x-.5)/(128/255)",
                "depth_limits":limits, "absolute_error_limits":error_limits, "sources":source_hashes,
                "inputs":provenance, "raw_arrays":str(raw_path), "raw_arrays_sha256":sha(raw_path),
                "target_semantics":"Snapshot-verified pseudo-depth; missing attack constants serialized as zero float32 maps and required to match exact frozen SHA. No new 3DDFA.",
                "mae_scope":"Selected illustrative frames only, not full-test depth performance"}
    (output / "provenance.json").write_text(json.dumps(metadata, indent=2)+"\n", encoding="utf-8")
    return metadata
