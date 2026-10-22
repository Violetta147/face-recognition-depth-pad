"""Truthful static figures from the frozen single-seed CASIA experiments."""
from __future__ import annotations

import html
import json
from pathlib import Path
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import numpy as np
import pandas as pd

from .figure_data import MODELS, choose_cases, read_json, sha256

COLORS = ["#0072B2", "#333333", "#009E73", "#D55E00", "#7B4AB0", "#8A6500"]
NOTE = "CASIA development protocol · seed 42 · video mean of 20 frames · 270 attack / 90 live test videos"


class FigureWriter:
    def __init__(self, output_dir, dpi=300):
        self.root = Path(output_dir)
        self.dpi = dpi
        self.items = []
        for name in ("png", "pdf", "svg", "data"):
            (self.root / name).mkdir(parents=True, exist_ok=True)
        plt.rcParams.update({"font.family":"DejaVu Sans", "font.size":11,
            "axes.spines.top":False, "axes.spines.right":False,
            "pdf.fonttype":42, "svg.fonttype":"none", "savefig.facecolor":"white"})

    def save(self, fig, stem, caption, data=None):
        fig.supxlabel("\n".join(textwrap.wrap(caption, 135)), fontsize=9)
        paths = []
        for extension in ("png", "pdf", "svg"):
            path = self.root / extension / f"{stem}.{extension}"
            if path.exists():
                raise FileExistsError(f"Use a new output folder: {path}")
            fig.savefig(path, dpi=self.dpi, facecolor="white")
            paths.append(str(path.relative_to(self.root)))
        if data is not None:
            data.to_csv(self.root / "data" / f"{stem}.csv", index=False)
        self.items.append({"name":stem, "caption":caption, "files":paths,
                           "width_inches":float(fig.get_figwidth()), "height_inches":float(fig.get_figheight()), "png_dpi":self.dpi})
        plt.close(fig)
        print("FIGURE", stem, flush=True)

    def finish(self, provenance):
        table = pd.DataFrame([{"figure":row["name"],"caption":row["caption"]} for row in self.items])
        table.to_csv(self.root / "CAPTIONS.csv", index=False)
        entries = []
        for row in self.items:
            label = html.escape(row["name"])
            caption = html.escape(row["caption"])
            entries.append(f'<article><h2>{label}</h2><a href="png/{label}.png"><img src="png/{label}.png" alt="{caption}"></a><p>{caption}</p><p><a href="pdf/{label}.pdf">PDF</a> · <a href="svg/{label}.svg">SVG</a></p></article>')
        (self.root / "INDEX.html").write_text('<!doctype html><meta charset="utf-8"><title>DeepFace PAD figures</title><style>body{font-family:Arial;max-width:1200px;margin:auto;padding:24px;color:#222}img{width:100%}article{margin-bottom:48px}</style><h1>DeepFace PAD — frozen E0–E4</h1><p>One seed, CASIA development protocol. Captions and source CSV accompany every figure.</p>'+"\n".join(entries),encoding="utf-8")
        provenance.update(figures=self.items, exported_files={str(p.relative_to(self.root)):sha256(p)
                           for p in sorted(self.root.rglob("*")) if p.is_file() and p.name != "figure_manifest.json"})
        (self.root / "figure_manifest.json").write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")


def metric_table(evidence, split):
    rows = []
    for name in MODELS:
        run = evidence["runs"][name]
        log = run["log"]
        stage = log.iloc[-1].stage
        final_stage = log[log.stage == stage]
        criterion = "val_selection_loss" if "val_selection_loss" in log else "val_loss"
        selected = final_stage.loc[final_stage[criterion].idxmin()]
        rows.append({"model":name, **run[f"{split}_metrics"], "epochs_trained":len(log),
                     "selected_stage":stage, "selected_stage_epoch":int(selected.epoch),
                     "selected_global_epoch":int(selected.global_epoch)})
    return pd.DataFrame(rows)


def roc_points(labels, scores):
    labels, scores = np.asarray(labels), np.asarray(scores)
    if set(np.unique(labels)) != {0,1} or not np.isfinite(scores).all():
        raise ValueError("ROC requires two classes and finite scores")
    thresholds = np.r_[np.inf, np.unique(scores)[::-1], -np.inf]
    return np.array([np.mean(scores[labels == 0] >= t) for t in thresholds]), np.array([np.mean(scores[labels == 1] >= t) for t in thresholds])


def _bars(ax, names, values, color=None, fmt=".2f"):
    bars = ax.bar(names, values, color=color or COLORS[:len(names)], edgecolor="#222", linewidth=.5)
    maximum = max(values) if len(values) else 0
    ax.set_ylim(0, max(maximum*1.25, 1.0))
    ax.bar_label(bars, labels=[format(v,fmt) for v in values],padding=4,fontsize=10)
    ax.grid(axis="y", alpha=.2)
    ax.set_axisbelow(True)


def _box(ax, x, y, w, h, label, color="#EAF3FA"):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=.015",facecolor=color,edgecolor="#333",linewidth=1.2))
    ax.text(x+w/2,y+h/2,label,ha="center",va="center",fontsize=11)


def _arrow(ax, start, end, dashed=False):
    ax.add_patch(FancyArrowPatch(start,end,arrowstyle="-|>",mutation_scale=14,color="#333",linestyle="--" if dashed else "-"))


def numeric_figures(evidence, writer):
    runs, manifest = evidence["runs"], evidence["manifest"]
    fig, ax = plt.subplots(figsize=(14,7),layout="constrained")
    ax.set(xlim=(-.03,1.04),ylim=(0,1)); ax.axis("off")
    _box(ax,.01,.66,.17,.15,"RGB 256×256\nCDCN normalization")
    _box(ax,.24,.66,.18,.15,"Official CDCN\nθ = 0.7")
    _box(ax,.48,.66,.16,.15,"Predicted depth\n1×32×32")
    _box(ax,.73,.78,.25,.13,"E1: spatial mean → score")
    _box(ax,.73,.52,.25,.19,"E2 / E3 / E3b / E4\nConv 1→8→16 → GAP\nLinear 16→1 → sigmoid")
    for first, second in [((.18,.735),(.24,.735)),((.42,.735),(.48,.735)),((.64,.77),(.73,.84)),((.64,.69),(.73,.62))]:
        _arrow(ax,first,second)
    _box(ax,.03,.30,.28,.13,"Frozen pseudo-depth cache\n3DDFA V2 live / zero attack", "#F8F1DF")
    _box(ax,.40,.30,.29,.13,"Train: depth MSE + contrast MSE\nHead: BCE or Focal", "#F8F1DF")
    _arrow(ax,(.31,.365),(.40,.365),True); _arrow(ax,(.55,.66),(.55,.43),True)
    _box(ax,.03,.07,.57,.12,"E0: RGB 224×224 → MobileNetV3 Small → sigmoid", "#F0F0F0")
    ax.text(.74,.19,"20 frame scores → video mean\nThreshold selected on validation\nNo 3DDFA at PAD inference",ha="center",va="center",fontsize=11)
    fig.suptitle("Luồng nghiên cứu và cách đọc bản đồ depth",fontsize=18)
    writer.save(fig,"01_pipeline","Implemented-code schematic. Solid: inference; dashed: supervision. Depth loss applies to E1 and depth/joint stages; E2 trains only the BCE head. E0 and CDCN use different input sizes/preprocessing.")

    schedule = []
    fig, ax = plt.subplots(figsize=(12,5),layout="constrained")
    stage_colors = {"depth":"#0072B2","head":"#009E73","joint":"#D55E00"}
    for y,name in enumerate(MODELS):
        cfg = runs[name]["config"]["training"]
        stages = cfg.get("stages",[{"name":"depth" if name == "E1" else "joint", "epochs":cfg.get("epochs",0)}])
        start = 0
        for stage in stages:
            duration, label = stage["epochs"], stage["name"]
            ax.barh(y,duration,left=start,height=.65,color=stage_colors[label],edgecolor="white")
            ax.text(start+duration/2,y,f"{label}\n{duration}",ha="center",va="center",color="white",fontsize=10)
            schedule.append({"model":name,"stage":label,"start":start,"epochs":duration})
            start += duration
    ax.set(yticks=range(6),yticklabels=MODELS,xlabel="Epoch",xlim=(0,32)); ax.invert_yaxis()
    ax.set_title("Ngân sách và lịch train thực tế")
    writer.save(fig,"02_training_schedule",NOTE+". E0 joint means binary BCE training; E1 depth-only. E0/E1/E2 budgets differ from the 16-epoch E3/E3b/E4 ablation.",pd.DataFrame(schedule))

    split = manifest.groupby("split").agg(frames=("sample_id","size"),videos=("video_id","nunique"),subjects=("subject_id","nunique")).loc[["train","val","test"]]
    fig, axes = plt.subplots(1,3,figsize=(12,4.5),layout="constrained")
    for ax,(column,label) in zip(axes,[("subjects","Người"),("videos","Video"),("frames","Frame")]):
        _bars(ax,["Train","Validation","Test"],split[column].tolist(),fmt=".0f"); ax.set_title(label)
    fig.suptitle("CASIA-FASD: split cố định, tách người giữa các tập",fontsize=16)
    writer.save(fig,"03_dataset_split","50 people, 600 videos, 12,000 sampled frames. Validation subjects 4, 9, 14, 19. No detected subject/video overlap; 20 frames/video.",split.reset_index())

    snapshot = read_json(runs["E1"]["folder"] / "depth_input_snapshot.json")["depth_audit"]
    fig, ax = plt.subplots(figsize=(9,4.5),layout="constrained")
    target_counts = [int((manifest.label == label).sum()) for label in (0,1)]
    _bars(ax,["Attack zero targets","Live 3DDFA targets"],target_counts,fmt=".0f")
    ax.set(ylabel="Depth maps",title="Pseudo-depth cache và kiểm tra đầu vào")
    writer.save(fig,"04_depth_QA",f"Recorded E1 preflight: {snapshot['samples']:,} targets; {len(snapshot['issues'])} QA issues. QA verifies readable finite nonzero live / zero attack maps, not true 3D accuracy.",pd.DataFrame({"target":["attack_zero","live_3ddfa"],"count":target_counts}))

    for split_name in ("val","test"):
        table = metric_table(evidence,split_name)
        display = table[["model","threshold","apcer","bpcer","acer","eer","auc","epochs_trained","selected_global_epoch"]].copy()
        for column in ("apcer","bpcer","acer","eer"):
            display[column] = display[column].map(lambda value:f"{100*value:.4f}")
        display.threshold = display.threshold.map(lambda value:f"{value:.6f}")
        display.auc = display.auc.map(lambda value:f"{value:.6f}")
        fig, ax = plt.subplots(figsize=(14,4.2),layout="constrained"); ax.axis("off")
        tab = ax.table(cellText=display.values,colLabels=["Model","Threshold","APCER %","BPCER %","ACER %","EER %","AUC","Epochs","Best global"],loc="center",cellLoc="center")
        tab.auto_set_font_size(False); tab.set_fontsize(11); tab.scale(1,2.05)
        for (row,col),cell in tab.get_celld().items():
            cell.set_edgecolor("#DDDDDD")
            if row == 0: cell.set_facecolor("#EAF3FA"); cell.set_text_props(weight="bold")
        ax.set_title("Kết quả "+("validation (48 video)" if split_name == "val" else "test phát triển (360 video)"),fontsize=16)
        writer.save(fig,f"05_{split_name}_metrics",NOTE+". Fixed validation thresholds. No multi-seed uncertainty; E3 was selected before test.",table)

    test_table = metric_table(evidence,"test")
    fig, axes = plt.subplots(1,3,figsize=(14,5),layout="constrained")
    for ax,key in zip(axes,("apcer","bpcer","acer")):
        _bars(ax,list(MODELS),(100*test_table[key]).tolist(),fmt=".4f")
        ax.set_ylim(0,14); ax.set_title(key.upper()); ax.set_ylabel("% video")
    fig.suptitle("Sai số tại ngưỡng validation đã khóa",fontsize=17)
    writer.save(fig,"06_test_error_rates",NOTE+". All APCER values are zero in this sample. E1/E2 ACER 2.7778%; E3/E3b 5%; E4 4.4444%.",test_table)

    fig, axes = plt.subplots(1,2,figsize=(13,5.5),layout="constrained")
    roc_data = []
    for index,name in enumerate(MODELS):
        video = runs[name]["test_video"]
        fpr,tpr = roc_points(video.label.to_numpy(),video.score.to_numpy())
        area = float(np.sum(np.diff(fpr)*(tpr[1:]+tpr[:-1])/2))
        if abs(area-runs[name]["test_metrics"]["auc"]) > 1e-12: raise ValueError("ROC area disagrees with saved AUC")
        for ax in axes:
            ax.plot(fpr,tpr,color=COLORS[index],linestyle=["-","--",":","-.","--","-"][index],marker=["o","s","^","D","v","x"][index],markevery=max(1,len(fpr)//10),markersize=3,label=f"{name}: {area:.6f}",linewidth=1.7)
        roc_data.extend({"model":name,"false_attack_accept_rate":x,"true_live_accept_rate":y} for x,y in zip(fpr,tpr))
    axes[0].plot([0,1],[0,1],color="#999",linestyle=":")
    axes[0].set(xlim=(0,1),ylim=(0,1.01),title="Toàn khoảng ROC")
    axes[1].set(xlim=(0,.08),ylim=(.85,1.005),title="Phóng vùng góc trên trái")
    for ax in axes:
        ax.set(xlabel="False attack accept rate",ylabel="True live accept rate"); ax.grid(alpha=.2)
    axes[0].legend(fontsize=9,loc="lower right")
    writer.save(fig,"07_ROC",NOTE+". ROC/AUC uses video ranking across thresholds; ACER uses each model's fixed validation threshold. Right panel is an explicitly labelled zoom.",pd.DataFrame(roc_data))

    bins = np.linspace(0,max(1,max(runs[n]["test_video"].score.max() for n in MODELS)),26)
    fig, axes = plt.subplots(2,3,figsize=(14,8),layout="constrained")
    score_rows = []
    for ax,name in zip(axes.flat,MODELS):
        video = runs[name]["test_video"]
        for label,text,color,style in [(0,"Attack","#0072B2","-"),(1,"Live","#D55E00","--")]:
            values = video.loc[video.label == label,"score"]
            ax.hist(values,bins=bins,weights=np.ones(len(values))*100/len(values),histtype="step",linewidth=2,color=color,linestyle=style,label=text)
        ax.axvline(runs[name]["threshold"],color="#222",linestyle=":",label="Val threshold")
        ax.set(title=name,xlabel="Score",ylabel="% video trong lớp"); ax.legend(fontsize=8)
        score_rows.append(video.assign(model=name))
    writer.save(fig,"08_score_distributions",NOTE+". Common 25 bins, normalized within each class. E1 mean depth and head sigmoid are different score scales; thresholds are model-specific.",pd.concat(score_rows,ignore_index=True))
    pd.DataFrame({"left":bins[:-1],"right":bins[1:]}).to_csv(writer.root / "data/histogram_bins.csv",index=False)

    fig, axes = plt.subplots(2,3,figsize=(13,8),layout="constrained")
    confusion_rows = []
    for ax,name in zip(axes.flat,MODELS):
        video = runs[name]["test_video"]
        matrix = np.array([[int(((video.label == truth)&(video.prediction == pred)).sum()) for pred in (0,1)] for truth in (0,1)])
        ax.imshow(matrix,cmap="Blues",vmin=0,vmax=270)
        for row in range(2):
            for col in range(2):
                ax.text(col,row,f"{matrix[row,col]}\n{100*matrix[row,col]/matrix[row].sum():.2f}%",ha="center",va="center",color="white" if matrix[row,col]>135 else "black",fontsize=13)
                confusion_rows.append({"model":name,"true_label":row,"pred_label":col,"videos":matrix[row,col]})
        ax.set(title=name,xticks=[0,1],yticks=[0,1],xticklabels=["Attack","Live"],yticklabels=["Attack","Live"],xlabel="Dự đoán",ylabel="Nhãn thật")
    writer.save(fig,"09_confusion_matrices",NOTE+". Counts and row percentages; common color scale 0–270 videos. A live predicted as attack is a false rejection.",pd.DataFrame(confusion_rows))

    for name in MODELS:
        log = runs[name]["log"]
        stage_names = list(log.stage.drop_duplicates())
        fig, axes = plt.subplots(1,len(stage_names),figsize=(max(8,4.6*len(stage_names)),4.8),layout="constrained",squeeze=False)
        for ax,stage in zip(axes.flat,stage_names):
            part = log[log.stage == stage]
            ax.plot(part.epoch,part.train_loss,"o-",color="#0072B2",label="Train objective",markersize=3)
            ax.plot(part.epoch,part.val_loss,"s--",color="#D55E00",label="Val objective",markersize=3)
            classification = runs[name]["config"].get("loss",{}).get("classification","none")
            semantic_stage = "depth-only (runner: joint)" if name == "E1" else stage
            ax.set(title=f"{semantic_stage} | cls={classification}",xlabel="Epoch trong stage",ylabel="Objective loss"); ax.legend(fontsize=9); ax.grid(alpha=.2)
        fig.suptitle(f"{name}: đường học thực tế",fontsize=16)
        writer.save(fig,f"10_learning_{name}",NOTE+". Raw unsmoothed logs. Stage objectives differ: panels are separate and their losses are not comparable across stages/models.",log)
    fig, axes = plt.subplots(1,3,figsize=(13,4.8),layout="constrained")
    selection_rows = []
    for ax,name in zip(axes,("E3","E3b","E4")):
        log = runs[name]["log"]; part = log[log.stage == "joint"]
        best = part.loc[part.val_selection_loss.idxmin()]
        ax.plot(part.epoch,part.val_selection_loss,"o-",color=COLORS[MODELS.index(name)],markersize=4)
        ax.scatter([best.epoch],[best.val_selection_loss],marker="*",s=160,color="black",label=f"Chọn epoch {int(best.epoch)}")
        ax.set(title=name,xlabel="Epoch trong joint",ylabel="Validation classification BCE"); ax.grid(alpha=.2); ax.legend(fontsize=9)
        selection_rows.append(part.assign(model=name))
    writer.save(fig,"11_checkpoint_selection",NOTE+". Common validation BCE criterion, including Focal training. Selection is within the final joint stage; E3 trained 16 joint epochs, staged models 8.",pd.concat(selection_rows,ignore_index=True))

    paired_rows = []
    for name in MODELS[2:]:
        pair = runs["E1"]["test_video"][["video_id","label","prediction"]].merge(runs[name]["test_video"][["video_id","prediction"]],on="video_id",validate="one_to_one",suffixes=("_base","_new"))
        first,second = pair.prediction_base == pair.label, pair.prediction_new == pair.label
        paired_rows.append({"model":name,"fixed":int((~first&second).sum()),"new_error":int((first&~second).sum()),"both_wrong":int((~first&~second).sum())})
    pairs = pd.DataFrame(paired_rows)
    fig, ax = plt.subplots(figsize=(10,4.8),layout="constrained")
    positions = np.arange(len(pairs))
    for delta,key,label,color in [(-.23,"fixed","Sửa lỗi E1","#0072B2"),(0,"new_error","Tạo lỗi mới","#D55E00"),(.23,"both_wrong","Cùng sai","#777777")]:
        bars = ax.bar(positions+delta,pairs[key],width=.23,label=label,color=color,edgecolor="#222",linewidth=.4); ax.bar_label(bars,padding=3)
    ax.set(xticks=positions,xticklabels=pairs.model,ylabel="Video",ylim=(0,6.5),title="Thay đổi lỗi so với Official E1"); ax.legend()
    writer.save(fig,"12_paired_errors",NOTE+". Same 360 videos paired by ID; improved and newly wrong videos are both shown.",pairs)

    metadata = manifest.loc[manifest.split == "test",["video_id","label","quality"]].drop_duplicates()
    rows = []
    for name in MODELS:
        live = runs[name]["test_video"].merge(metadata,on=["video_id","label"],validate="one_to_one").query("label == 1")
        for quality in ("high","normal","low"):
            group = live[live.quality == quality]
            rows.append({"model":name,"quality":quality,"live_videos":len(group),"errors":int((group.prediction != 1).sum()),"bpcer_percent":100*float((group.prediction != 1).mean())})
    quality_data = pd.DataFrame(rows)
    fig, ax = plt.subplots(figsize=(12,5),layout="constrained")
    for i,name in enumerate(MODELS):
        part = quality_data[quality_data.model == name]
        x = np.arange(3)+(i-2.5)*.13
        bars = ax.bar(x,part.bpcer_percent,width=.13,color=COLORS[i],hatch=["","//","..","xx","\\\\","++"][i],label=name,edgecolor="#222",linewidth=.3)
        ax.bar_label(bars,labels=[str(v) for v in part.errors],padding=3,fontsize=8)
    ax.set(xticks=[0,1,2],xticklabels=["high","normal","low"],ylabel="BPCER (%)",ylim=(0,30),title="Lỗi mặt thật theo quality trong manifest"); ax.legend(ncol=6,fontsize=9)
    writer.save(fig,"13_quality_errors",NOTE+". Each quality group has 30 live videos. Bar labels are error counts. Quality is manifest metadata, not a new measured blur/lighting cause.",quality_data)

    union = sorted(set().union(*(set(runs[name]["test_video"].loc[lambda d:d.prediction != d.label,"video_id"]) for name in MODELS)))
    matrix = np.array([[int(runs[name]["test_video"].set_index("video_id").loc[video,"prediction"] != runs[name]["test_video"].set_index("video_id").loc[video,"label"]) for video in union] for name in MODELS])
    fig, ax = plt.subplots(figsize=(max(12,len(union)*.7),5.2),layout="constrained")
    ax.imshow(matrix,cmap=matplotlib.colors.ListedColormap(["#F2F2F2","#D55E00"]),vmin=0,vmax=1,aspect="auto")
    for y in range(len(MODELS)):
        for x in range(len(union)): ax.text(x,y,"×" if matrix[y,x] else "·",ha="center",va="center",fontsize=15)
    ax.set(yticks=range(6),yticklabels=MODELS,xticks=range(len(union)),xticklabels=union,title="Những video có lỗi ở ít nhất một model")
    plt.setp(ax.get_xticklabels(),rotation=55,ha="right",fontsize=8)
    writer.save(fig,"14_error_video_matrix",NOTE+". Filtered to the union of error videos, all live in these runs; not the complete test set. × = false rejection, dot = correct.",pd.DataFrame(matrix,index=MODELS,columns=union).reset_index(names="model"))
    cases = choose_cases(evidence)
    cases.to_csv(writer.root / "data/case_selection.csv",index=False)
    return cases
