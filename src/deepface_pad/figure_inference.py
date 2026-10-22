"""Bounded inference for report illustrations, depth MAE and forward timing."""
from __future__ import annotations

import copy
import gc
import json
import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader

from .data import PadDataset
from .depth_evaluation import depth_error_rows, summarize_depth_errors
from .figure_data import MODELS, DEPTH_MODELS, choose_cases, read_json, restore_selected_inputs
from .report_figures import COLORS, NOTE, _bars
from .train import build_model


def un_normalize_rgb(tensor, normalization):
    image = tensor.detach().cpu().numpy()
    if normalization == "cdcn_official":
        result = image * (128/255) + .5
    elif normalization == "imagenet":
        result = image * np.array([.229,.224,.225])[:,None,None] + np.array([.485,.456,.406])[:,None,None]
    else:
        raise ValueError(f"unknown normalization: {normalization}")
    return np.clip(result.transpose(1,2,0),0,1)


def load_model(run, device):
    cfg = copy.deepcopy(run["config"])
    # The complete frozen checkpoint supplies all weights; avoid a network download.
    if cfg["model"]["name"] == "mobilenet_v3_small":
        cfg["model"]["pretrained"] = False
    model = build_model(cfg).to(device)
    state = torch.load(run["folder"] / "best.ckpt",map_location="cpu",weights_only=True)
    model.load_state_dict(state["model"],strict=True)
    return model.eval()


def depth_figures(evidence, writer, data_root, dataset_zip, depth_tar, device):
    manifest, runs = evidence["manifest"], evidence["runs"]
    cases = choose_cases(evidence)
    selected = pd.concat([manifest[manifest.split == "val"],cases.drop(columns="role")],ignore_index=True).drop_duplicates("sample_id")
    snapshot = read_json(runs["E1"]["folder"] / "depth_input_snapshot.json")
    checksums = {row["sample_id"]:row["sha256"] for row in snapshot["depth_audit"]["artifact_checksums"]}
    provenance = restore_selected_inputs(selected,data_root,dataset_zip,depth_tar,checksums)
    (writer.root / "data/selected_input_hashes.json").write_text(json.dumps(provenance,indent=2)+"\n")
    selected_manifest = writer.root / "data/inference_manifest.csv"
    selected.to_csv(selected_manifest,index=False)
    val = PadDataset(selected_manifest,data_root,"val",256,augment=False,require_depth=True,normalization="cdcn_official")
    test = PadDataset(selected_manifest,data_root,"test",256,augment=False,require_depth=True,normalization="cdcn_official")
    loader = DataLoader(val,batch_size=8,shuffle=False,num_workers=0)
    case_samples = [test[index] for index in range(len(test))]
    case_images = torch.stack([row["image"] for row in case_samples]).to(device)
    samples = {str(row["sample_id"]):row for row in case_samples}
    outputs, reports, measures = {}, {}, []
    for name in DEPTH_MODELS:
        run = runs[name]
        if run["config"]["data"].get("normalization") != "cdcn_official" or run["config"]["data"].get("image_size") != 256:
            raise ValueError("depth figure inputs differ from the frozen preprocessing")
        model = load_model(run,device)
        errors, reproduced = [], []
        with torch.inference_mode():
            for batch in loader:
                output = model(batch["image"].to(device))
                errors.extend(depth_error_rows(output["depth"].cpu(),batch["depth"],batch["label"],batch["sample_id"],batch["video_id"]))
                scores = (torch.sigmoid(output["logit"]) if "logit" in output else output["score"]).cpu()
                reproduced.extend({"sample_id":sid,"reproduced_score":float(value)} for sid,value in zip(batch["sample_id"],scores))
            predicted = model(case_images)["depth"][:,0].cpu().numpy()
        frame = pd.DataFrame(errors)
        report = summarize_depth_errors(frame)
        score_check = pd.DataFrame(reproduced).merge(run["val_frame"][["sample_id","score"]],on="sample_id",validate="one_to_one")
        difference = float(np.max(np.abs(score_check.reproduced_score-score_check.score)))
        if difference > 1e-3:
            raise ValueError(f"{name}: reproduced validation score differs by {difference}; inspect inputs/runtime")
        report.update(model=name,split="val",checkpoint_sha256=run["checkpoint_sha256"],
                      max_abs_saved_frame_score_difference=difference,measurement="new bounded inference for figures")
        old_report_path = run["folder"] / "depth_val_metrics.json"
        if old_report_path.is_file():
            old = read_json(old_report_path)
            for label in ("attack","live"):
                if abs(old["by_class"][label]["frame_mean_mae_full"]-report["by_class"][label]["frame_mean_mae_full"]) > 1e-3:
                    raise ValueError(f"{name}: depth MAE differs from audited measurement")
        frame.to_csv(writer.root / "data" / f"depth_val_errors_{name}.csv",index=False)
        score_check.to_csv(writer.root / "data" / f"reproduced_val_scores_{name}.csv",index=False)
        (writer.root / "data" / f"depth_val_metrics_{name}.json").write_text(json.dumps(report,indent=2)+"\n")
        reports[name] = report
        measures.append({"model":name,"attack_full":report["by_class"]["attack"]["frame_mean_mae_full"],
                         "live_full":report["by_class"]["live"]["frame_mean_mae_full"],
                         "live_mask":report["by_class"]["live"]["pixel_weighted_mae_target_mask"]})
        outputs[name] = {str(row["sample_id"]):prediction for row,prediction in zip(case_samples,predicted)}
        del model
        gc.collect()
        if device.type == "cuda": torch.cuda.empty_cache()
        print("DEPTH INFERENCE",name,"960 val frames; saved-score max difference",difference,flush=True)
    if max(np.max(np.abs(outputs["E1"][sid]-outputs["E2"][sid])) for sid in samples) > 1e-5:
        raise ValueError("E1 and frozen E2 depth maps disagree")
    table = pd.DataFrame(measures)
    fig,axes = plt.subplots(1,3,figsize=(14,5),layout="constrained")
    shared_max = max(table[["attack_full","live_full","live_mask"]].max())*1.25
    for ax,column,title in zip(axes,("attack_full","live_full","live_mask"),("Attack: toàn ảnh","Live: toàn ảnh","Live: mask target > 1e-6")):
        _bars(ax,table.model.tolist(),table[column].tolist(),color=COLORS[1:],fmt=".4f")
        ax.set(ylim=(0,shared_max),ylabel="MAE pseudo-depth",title=title)
    writer.save(fig,"15_depth_MAE_all_models",NOTE+". New validation inference: 720 attack/240 live frames. Common targets, no prediction clipping; masked live MAE is pixel-weighted. Not true 3D error; E0 has no depth output.",table)

    fig,axes = plt.subplots(2,4,figsize=(14,8),layout="constrained")
    for ax in axes.flat: ax.axis("off")
    for ax,row in zip(axes.flat,cases.itertuples()):
        ax.imshow(un_normalize_rgb(samples[row.sample_id]["image"],"cdcn_official"))
        ax.set_title(f"{row.video_id}\n{row.attack_type} | quality={row.quality}",fontsize=10)
    writer.save(fig,"16_RGB_case_overview",NOTE+". Explicit outcome/attack-type examples, not a random sample. One middle temporal frame/video; RGB reverses actual CDCN normalization.",cases)

    limits = render_depth_cases(evidence,writer,cases,samples,outputs)
    return {"depth_inference_reports":reports, **limits,
            "selected_cases":cases[["sample_id","video_id","role"]].to_dict(orient="records")}


def render_depth_cases(evidence,writer,cases,samples,outputs):
    runs = evidence["runs"]
    map_max = max(1.,max(float(values.max()) for model in outputs.values() for values in model.values()))
    error_max = max(float(np.abs(outputs[name][sid]-samples[sid]["depth"][0].numpy()).max()) for name in DEPTH_MODELS for sid in samples)
    error_max = max(error_max,1e-6)
    raw_arrays = {}
    for position,row in enumerate(cases.itertuples(),1):
        sample = samples[row.sample_id]
        target = sample["depth"][0].numpy()
        fig,axes = plt.subplots(3,5,figsize=(15,9),layout="constrained")
        for ax in axes.flat: ax.set_xticks([]); ax.set_yticks([])
        axes[0,0].imshow(un_normalize_rgb(sample["image"],"cdcn_official")); axes[0,0].set_title("RGB model input")
        target_artist = axes[0,1].imshow(target,cmap="viridis",vmin=0,vmax=map_max,interpolation="nearest"); axes[0,1].set_title("Pseudo-depth target")
        axes[0,2].imshow(target>1e-6,cmap="gray",vmin=0,vmax=1,interpolation="nearest"); axes[0,2].set_title("Target mask")
        for ax in axes[0,3:]: ax.axis("off")
        axes[0,3].text(0,.8,f"Label: {'Live' if row.label else 'Attack'}\nQuality: {row.quality}\nFrame: {row.frame_index}\nDepth shown at 32×32",va="top",fontsize=11)
        axes[0,4].text(0,.8,"Decisions below use\nVIDEO mean of 20 frames.\nColor limits shared\nacross all cases/models.",va="top",fontsize=10)
        for column,name in enumerate(DEPTH_MODELS):
            prediction = outputs[name][row.sample_id]
            run = runs[name]; video = run["test_video"].set_index("video_id").loc[row.video_id]
            decision = "Live" if video.prediction else "Attack"
            status = "CORRECT" if video.prediction == row.label else "ERROR"
            axes[1,column].imshow(prediction,cmap="viridis",vmin=0,vmax=map_max,interpolation="nearest")
            axes[1,column].set_title(f"{name}: {decision} / {status}\nvideo={video.score:.4f}; t={run['threshold']:.4f}",fontsize=10)
            error_artist = axes[2,column].imshow(np.abs(prediction-target),cmap="magma",vmin=0,vmax=error_max,interpolation="nearest")
            axes[2,column].set_title(f"{name}: |prediction − target|",fontsize=10)
            raw_arrays[f"{row.sample_id}_{name}_prediction"] = prediction
        raw_arrays[f"{row.sample_id}_target"] = target
        fig.colorbar(target_artist,ax=list(axes[1,:])+[axes[0,1]],shrink=.65,label="Normalized pseudo-depth units")
        fig.colorbar(error_artist,ax=list(axes[2,:]),shrink=.8,label="Absolute error")
        fig.suptitle(f"{row.video_id} | {row.role}",fontsize=15)
        writer.save(fig,f"17_case_{position:02d}_{row.video_id}","Selected illustration, not aggregate performance. Middle frame; displayed decisions/scores are frozen VIDEO-level results. Shared color scales, no per-image normalization or prediction clipping. Native depth resolution 32×32.")
    np.savez_compressed(writer.root / "data/qualitative_depth_arrays.npz",**raw_arrays)
    return {"depth_color_limits":[0,map_max],"absolute_error_color_limits":[0,error_max]}


def benchmark_figures(evidence, writer, device, rounds=5, warmup=20, repeats=50):
    if device.type != "cuda": raise ValueError("GPU required for the common-session forward benchmark")
    torch.manual_seed(42)
    models = {name:load_model(evidence["runs"][name],device) for name in MODELS}
    samples = {side:torch.randn(1,3,side,side,device=device) for side in (224,256)}
    generator = np.random.default_rng(20261016)
    rows = []
    with torch.inference_mode():
        for profile in ("native","common256"):
            for round_index in range(rounds):
                for order,name in enumerate(generator.permutation(MODELS)):
                    side = evidence["runs"][name]["config"]["data"]["image_size"] if profile == "native" else 256
                    tensor = samples[side]
                    for _ in range(warmup): models[name](tensor)
                    torch.cuda.synchronize()
                    for repetition in range(repeats):
                        torch.cuda.synchronize(); started = time.perf_counter()
                        models[name](tensor); torch.cuda.synchronize()
                        rows.append({"profile":profile,"round":round_index+1,"order":order+1,"model":str(name),"input_side":side,
                                     "repeat":repetition+1,"latency_ms":1000*(time.perf_counter()-started)})
                print("BENCHMARK",profile,"round",round_index+1,"/",rounds,flush=True)
    raw = pd.DataFrame(rows)
    raw.to_csv(writer.root / "data/latency_raw.csv",index=False)
    summary = []
    for (profile,name),group in raw.groupby(["profile","model"],sort=False):
        model = models[name]
        summary.append({"profile":profile,"model":name,"input_side":int(group.input_side.iloc[0]),"samples":len(group),
                        "p50_ms":float(group.latency_ms.median()),"p95_ms":float(group.latency_ms.quantile(.95)),
                        "parameters":sum(p.numel() for p in model.parameters()),
                        "checkpoint_MiB":evidence["runs"][name]["folder"].joinpath("best.ckpt").stat().st_size/1024**2})
    table = pd.DataFrame(summary)
    for profile in ("native","common256"):
        part = table[table.profile == profile].set_index("model").loc[list(MODELS)].reset_index()
        fig,axes = plt.subplots(1,3,figsize=(14,5),layout="constrained")
        _bars(axes[0],list(MODELS),(part.parameters/1e6).tolist(),fmt=".3f"); axes[0].set(ylabel="Million parameters",title="Số tham số")
        _bars(axes[1],list(MODELS),part.checkpoint_MiB.tolist(),fmt=".2f"); axes[1].set(ylabel="MiB",title="File checkpoint thực tế")
        _bars(axes[2],list(MODELS),part.p50_ms.tolist(),fmt=".2f")
        axes[2].scatter(np.arange(6),part.p95_ms,marker="D",color="black",label="p95")
        axes[2].set(ylim=(0,float(part.p95_ms.max())*1.25),ylabel="ms / frame",title="Forward: bar p50, diamond p95"); axes[2].legend(fontsize=9)
        native_note = "Native: E0 224×224; CDCN 256×256." if profile == "native" else "Common synthetic 256×256 for all; E0 was trained at 224×224."
        writer.save(fig,f"18_efficiency_{profile}",f"{native_note} Same GPU/session, FP32 batch 1; {rounds} randomized-order rounds, {warmup} warm-up and {repeats} timed forwards/model/round. Includes dispatch+synchronized forward, excludes loading/crop/transfer/webcam; percentiles are not CI.",part)
    del models
    torch.cuda.empty_cache()
    return {"latency_device":torch.cuda.get_device_name(device),"latency_rounds":rounds,"warmup":warmup,"repeats":repeats,
            "order_seed":20261016,"precision":"float32", "timing":"perf_counter with CUDA synchronize; forward only",
            "cuda_matmul_allow_tf32":torch.backends.cuda.matmul.allow_tf32,"cudnn_allow_tf32":torch.backends.cudnn.allow_tf32}
