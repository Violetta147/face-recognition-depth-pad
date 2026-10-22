"""Registered forward-only cost measurement. Never trains or evaluates accuracy."""
from __future__ import annotations

import io
import itertools
import json
import random
import time
import traceback
import zipfile
from pathlib import Path, PurePosixPath

import numpy as np
import pandas as pd
from PIL import Image
import torch
import yaml

from .data import PadDataset, manifest_checksum
from .round6 import digest, environment, immutable_json, read, verify_source
from .train import build_model

MODELS = ("E1", "E3", "E4")


def orders(seed):
    result = list(itertools.permutations(MODELS))
    random.Random(seed).shuffle(result)
    return result


def quantiles(values):
    values = np.asarray(values, dtype=float)
    if values.ndim != 1 or len(values) < 2 or not np.isfinite(values).all() or (values <= 0).any():
        raise ValueError("timings must contain at least two finite positive samples")
    return {"n": len(values), "mean": float(values.mean()),
            "p50": float(np.quantile(values, .5, method="linear")),
            "p95": float(np.quantile(values, .95, method="linear")),
            "min": float(values.min()), "max": float(values.max())}


def summarize(raw, timing):
    expected = [(r, p, m, i, i % 2) for r, sequence in enumerate(orders(timing["order_seed"]))
                for p, m in enumerate(sequence) for i in range(timing["iterations_per_block"])]
    identity = ["round", "position", "model", "iteration", "input_index"]
    if list(raw[identity].itertuples(index=False, name=None)) != expected:
        raise ValueError("raw timings are incomplete, reordered or from a different schedule")
    scopes = ("cuda_event_forward_ms", "synchronized_host_forward_ms")
    pooled = {m: {scope: quantiles(raw.loc[raw.model == m, scope]) for scope in scopes} for m in MODELS}
    blocks = [{"round": int(r), "model": m, **{scope: quantiles(group[scope]) for scope in scopes}}
              for (r, m), group in raw.groupby(["round", "model"], sort=True)]
    return {"pooled": pooled, "blocks": blocks, "quantile_method": "linear"}


def select_rows(manifest):
    selected = []
    for label in (0, 1):
        rows = manifest.loc[(manifest.split == "val") & (manifest.label == label)].sort_values("sample_id")
        if rows.empty:
            raise ValueError("need one validation frame per class")
        selected.append(rows.iloc[0].to_dict())
    return selected


def validation_inputs(manifest_path, dataset_zip):
    """Read two real validation images, never extract the full dataset/depth cache."""
    frame = pd.read_csv(manifest_path, keep_default_na=False)
    selected = select_rows(frame)
    dataset = PadDataset(manifest_path, ".", "val", 256, augment=False, normalization="cdcn_official")
    tensors, metadata = [], []
    with zipfile.ZipFile(dataset_zip) as archive:
        members = archive.infolist()
        for row in selected:
            relative = str(row["image_path"]).replace("\\", "/")
            parts = PurePosixPath(relative)
            if parts.is_absolute() or ".." in parts.parts:
                raise ValueError("image path must be relative to CASIA root")
            candidates = [m for m in members if not m.is_dir() and
                          (m.filename.replace("\\", "/") == relative or
                           m.filename.replace("\\", "/").endswith("/" + relative))]
            if len(candidates) != 1:
                raise ValueError(f"expected exactly one ZIP member for {relative}, got {len(candidates)}")
            payload = archive.read(candidates[0])
            with Image.open(io.BytesIO(payload)) as image:
                image_size = list(image.size)
                tensor = dataset.transform(image.convert("RGB")).as_subclass(torch.Tensor).unsqueeze(0).contiguous()
            if list(tensor.shape) != [1,3,256,256] or tensor.dtype != torch.float32 or not torch.isfinite(tensor).all():
                raise ValueError("invalid preprocessed input")
            tensors.append(tensor)
            import hashlib
            metadata.append({"sample_id":row["sample_id"], "label":int(row["label"]),
                "split":"val", "image_path":relative,"original_size":image_size,
                "image_sha256":hashlib.sha256(payload).hexdigest(),
                "tensor_sha256":hashlib.sha256(tensor.numpy().tobytes()).hexdigest(),
                "shape":list(tensor.shape),"dtype":str(tensor.dtype)})
    return tensors, metadata


def load_models(plan, drive_root):
    models, profiles = {}, {}
    for key in MODELS:
        spec = plan["models"][key]
        folder = Path(drive_root) / "runs" / spec["run_id"]
        checkpoint, config = folder / "best.ckpt", folder / "config.yaml"
        if (manifest_checksum(checkpoint) != spec["checkpoint_sha256"] or
                manifest_checksum(config) != spec["config_sha256"]):
            raise ValueError(f"{key}: checkpoint/config hash differs from cost registration")
        cfg = yaml.safe_load(config.read_text(encoding="utf-8"))
        if (cfg["model"]["name"] != spec["model_name"] or cfg["seed"] != spec["seed"] or
                cfg.get("source_commit") != spec["training_source_commit"]):
            raise ValueError(f"{key}: checkpoint identity differs")
        state = torch.load(checkpoint, map_location="cpu", weights_only=True)
        if state["config"] != cfg:
            raise ValueError(f"{key}: checkpoint embedded config differs")
        model = build_model(cfg).float().eval()
        model.load_state_dict(state["model"], strict=True)
        models[key] = model
        profiles[key] = {**spec, "params":sum(p.numel() for p in model.parameters()),
            "parameter_bytes":sum(p.numel()*p.element_size() for p in model.parameters()),
            "state_bytes_including_buffers":sum(p.numel()*p.element_size() for p in model.state_dict().values()),
            "checkpoint_file_bytes":checkpoint.stat().st_size,
            "reported_stage":state["stage"],"selected_epoch":state["epoch"]}
    if profiles["E3"]["params"] != profiles["E4"]["params"]:
        raise ValueError("E3/E4 must use the same inference architecture")
    return models, profiles


def prepare(root, drive_root, output):
    root, drive_root, output = map(Path, (root, drive_root, output))
    source = verify_source(root)
    plan = read(root / "configs/round6_cost.json")
    manifest = drive_root / "reports/casia_fasd_debug_with_depth.csv"
    if manifest_checksum(manifest) != plan["input"]["manifest_sha256"]:
        raise ValueError("validation manifest differs from locked CASIA split")
    tensors, inputs = validation_inputs(manifest, drive_root / "casia-fasd.zip")
    models, profiles = load_models(plan, drive_root)
    # A separate cost runtime: these settings never alter training registration.
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = False
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    env = environment()  # Requires actual A100; records GPU UUID/driver/dependencies.
    env.update(matmul_allow_tf32=torch.backends.cuda.matmul.allow_tf32,
               cudnn_allow_tf32=torch.backends.cudnn.allow_tf32)
    record = {"schema_version":1,"source":source,"plan":plan,"environment":env,
              "inputs":inputs,"models":profiles,"model_orders":[list(sequence) for sequence in orders(plan["timing"]["order_seed"])]}
    immutable_json(output / "registration.json", record)
    return record, models, tensors


@torch.inference_mode()
def timed_block(model, inputs, warmup, iterations):
    for i in range(warmup):
        result = model(inputs[i % 2])
    if not all(torch.isfinite(value).all() for value in result.values()):
        raise ValueError("nonfinite model output during warm-up")
    torch.cuda.synchronize()
    start, end = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
    rows = []
    for i in range(iterations):
        torch.cuda.synchronize()
        wall_started = time.perf_counter()
        start.record()
        result = model(inputs[i % 2])
        end.record()
        end.synchronize()
        wall_ms = (time.perf_counter() - wall_started)*1000
        rows.append({"iteration":i,"input_index":i % 2,
                     "cuda_event_forward_ms":float(start.elapsed_time(end)),
                     "synchronized_host_forward_ms":wall_ms})
    return rows


def run_cost(root, drive_root, output, *, allow_benchmark=False):
    if not allow_benchmark:
        raise ValueError("RUN_BENCHMARK is closed; review cost preflight first")
    output = Path(output)
    record, models, inputs = prepare(root, drive_root, output)
    registration_sha = manifest_checksum(output / "registration.json")
    complete, raw_path = output / "results.json", output / "timings.csv"
    if complete.exists():
        saved = read(complete)
        if (saved["registration_sha256"] != registration_sha or saved["raw_sha256"] != manifest_checksum(raw_path)
                or saved["summary"] != summarize(pd.read_csv(raw_path), record["plan"]["timing"])):
            raise ValueError("completed cost result changed; preserve and inspect")
        return saved
    if raw_path.exists() or (output / "failure.json").exists():
        raise ValueError("partial/failed cost block exists; no overwrite or automatic resume")
    raw = []
    try:
        device_inputs = [t.to("cuda") for t in inputs]
        models = {key:model.to("cuda").eval() for key,model in models.items()}
        cfg = record["plan"]["timing"]
        print("Measuring real validation inputs; forward only, not webcam FPS or accuracy.", flush=True)
        for round_id, sequence in enumerate(record["model_orders"]):
            for position, key in enumerate(sequence):
                rows = timed_block(models[key], device_inputs, cfg["warmup_per_block"], cfg["iterations_per_block"])
                raw.extend({"round":round_id,"position":position,"model":key,**row} for row in rows)
                temporary = output / "timings.csv.tmp"
                pd.DataFrame(raw).to_csv(temporary,index=False)
                temporary.replace(raw_path)
                print(f"round {round_id+1}/6 position {position+1}/3 {key}: {len(rows)} samples",flush=True)
        torch.cuda.synchronize()
        env_after = environment()
        env_after.update(matmul_allow_tf32=torch.backends.cuda.matmul.allow_tf32,
                         cudnn_allow_tf32=torch.backends.cudnn.allow_tf32)
        if env_after != record["environment"] or verify_source(Path(root)) != record["source"]:
            raise ValueError("environment/source changed during cost block")
        result = {"registration_sha256":registration_sha,"raw_sha256":manifest_checksum(raw_path),
                  "summary":summarize(pd.read_csv(raw_path),cfg),"models":record["models"],
                  "scope":record["plan"]["limits"]}
        immutable_json(complete,result)
        return result
    except BaseException as exc:
        immutable_json(output / "failure.json", {"exception":type(exc).__name__,"message":str(exc),
            "traceback":traceback.format_exc(),"completed_samples":len(raw),"registration_sha256":registration_sha})
        raise
