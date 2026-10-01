from __future__ import annotations

import json
import subprocess
from pathlib import Path


def markdown(source: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": source.splitlines(keepends=True)}


def code(source: str) -> dict:
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": source.splitlines(keepends=True)}


def build(root: Path) -> dict:
    original = json.loads(subprocess.check_output(
        ["git", "show", "HEAD:notebooks/Face_PAD_Official_CDCN_E1_Rerun.ipynb"],
        cwd=root, encoding="utf-8",
    ))
    restore = [cell for cell in original["cells"] if cell["cell_type"] == "code" and
               any("".join(cell["source"]).startswith(f"#@title 1.{index} ") for index in range(1, 5))]
    if len(restore) != 4:
        raise ValueError("Committed official E1 notebook must contain all four restore cells")
    restore = [code("".join(cell["source"])) for cell in restore]
    cells = [markdown("""# Lượt 4 — Frozen learned depth head trên Official CDCN

**Câu hỏi:** đọc cùng predicted depth map bằng head 1.265 tham số có tốt hơn lấy mean không?

E1: `CASIA_E1_CDCN_OFFICIAL_seed42_20260921T114029Z`. E2 nạp checkpoint E1,
khóa cả weights và BatchNorm, train riêng head với BCE 10 epoch. Mọi lựa chọn
checkpoint và threshold dùng validation. Notebook không train lại E1 hoặc sinh lại
3DDFA. CASIA test đã được xem ở Lượt 3: bảng mới là **so sánh phát triển**, chưa phải
xác nhận độc lập, nhiều seed hay SOTA. UCDCN 2024 là tiền lệ của learned depth classifier.

Chọn GPU runtime. Mở notebook này và chạy tuần tự. Chuẩn bị file
`DeepFace-PAD-Round4-source.zip` nếu runtime chưa có source mới.
Không dùng kết quả test để chọn phiên bản, epoch, threshold hay sửa config.
"""), code('''#@title 0.1 Drive, helper và đường dẫn
from google.colab import drive, files
drive.mount("/content/drive")
import importlib, json, shutil, subprocess, sys, time
from pathlib import Path
import numpy as np
import pandas as pd
import yaml
from IPython.display import display

REPO_ROOT = Path("/content/round4-source/DeepFace-PAD")
DRIVE_ROOT = Path("/content/drive/MyDrive/face-pad")
RUNS_DIR = DRIVE_ROOT / "runs"
REPORTS_DIR = DRIVE_ROOT / "reports"
DATA_ROOT = Path("/content/datasets/casia-fasd")
DEPTH_BACKUP = DRIVE_ROOT / "depth-checkpoints/casia-fasd"
DEPTH_ROOT = DATA_ROOT / "depth"
DEPTH_LEDGER = DEPTH_ROOT / "depth_status.csv"
DEPTH_QA = REPORTS_DIR / "casia-depth-qa-round4.json"
MANIFEST = REPO_ROOT / "data/manifests/casia_fasd_debug.csv"
DEPTH_MANIFEST = REPO_ROOT / "data/manifests/casia_fasd_debug_with_depth.csv"
E1_RUN = RUNS_DIR / "CASIA_E1_CDCN_OFFICIAL_seed42_20260921T114029Z"
for directory in (RUNS_DIR, REPORTS_DIR):
    directory.mkdir(parents=True, exist_ok=True)

def run(command, cwd=None):
    subprocess.run([str(item) for item in command], cwd=str(cwd) if cwd else None, check=True)
'''), code('''#@title 0.2 Nạp source đã commit từ ZIP và chạy tests
archive = Path("/content/DeepFace-PAD-Round4-source.zip")
if not archive.is_file():
    print("Upload DeepFace-PAD-Round4-source.zip vừa được cung cấp cùng notebook.")
    uploaded = files.upload()
    assert archive.is_file(), "Thiếu đúng file DeepFace-PAD-Round4-source.zip"
shutil.unpack_archive(str(archive), "/content/round4-source")
assert (REPO_ROOT / "src/deepface_pad/models/cdcn_depth_head.py").is_file()
run([sys.executable, "-m", "pip", "install", "-q", "-e", ".[dev]"], cwd=REPO_ROOT)
sys.path.insert(0, str(REPO_ROOT / "src"))
importlib.invalidate_caches()
run([sys.executable, "-m", "pytest", "-q"], cwd=REPO_ROOT)
import torch
assert torch.cuda.is_available(), "Chọn Runtime > Change runtime type > GPU"
print("GPU:", torch.cuda.get_device_name(0))
'''), markdown("## 1. Khôi phục cùng dataset và pseudo-depth E1\nCác cell này được sao chép từ notebook E1 đã commit; output notebook E1 đang mở không bị thay đổi.\n")]
    cells.extend(restore)
    cells.extend([markdown("## 2. Xác nhận đối chứng và đăng ký E2 trước khi train\n"), code('''#@title 2.1 Kiểm tra đúng E1, manifest và preprocessing
from deepface_pad.data import manifest_checksum
required = ["best.ckpt", "config.yaml", "model_provenance.json", "manifest_checksum.json", "val_frame_scores.csv", "val_scores.csv", "threshold.json"]
assert all((E1_RUN / name).is_file() for name in required), "Thiếu frozen E1 artifact trên Drive"
e1_config = yaml.safe_load((E1_RUN / "config.yaml").read_text())
assert e1_config["model"]["name"] == "cdcn_official"
assert e1_config["data"]["normalization"] == "cdcn_official"
assert e1_config["data"]["image_size"] == 256
assert e1_config["evaluation"]["aggregation"] == "mean"
expected_manifest = json.loads((E1_RUN / "manifest_checksum.json").read_text())["sha256"]
assert manifest_checksum(DEPTH_MANIFEST) == expected_manifest, "Manifest khác E1; dừng để kiểm tra, không đổi split"
e1_state = torch.load(E1_RUN / "best.ckpt", map_location="cpu", weights_only=False)
assert e1_state["config"]["model"]["name"] == "cdcn_official"

config = yaml.safe_load((REPO_ROOT / "configs/casia_e2_official_head_frozen.yaml").read_text())
assert config["model"]["theta"] == e1_config["model"].get("theta", .7)
config["data"]["manifest"] = str(DEPTH_MANIFEST)
config["data"]["root"] = str(DATA_ROOT)
config["training"]["init_checkpoint"] = str(E1_RUN / "best.ckpt")
CONFIG_PATH = REPO_ROOT / "configs/round4_full_runtime.yaml"
CONFIG_PATH.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
print(yaml.safe_dump(config, sort_keys=False))
print("E1 checkpoint SHA256:", manifest_checksum(E1_RUN / "best.ckpt"))
'''), code('''#@title 2.2 Smoke nạp checkpoint, khóa backbone và so lại validation E1
from deepface_pad.data import PadDataset
from deepface_pad.train import build_model, load_initial_weights, _set_stage, score_loader
from torch.utils.data import DataLoader
device = torch.device("cuda")
e1 = build_model(e1_config).to(device)
e1.load_state_dict(e1_state["model"])
e1.eval()
e2 = build_model(config).to(device)
load_initial_weights(e2, E1_RUN / "best.ckpt", device)
_set_stage(e2, "head")
e2.train()
assert not e2.backbone.training
assert all(torch.equal(value.cpu(), e2.backbone.state_dict()[key].cpu()) for key, value in e1_state["model"].items())
val_data = PadDataset(DEPTH_MANIFEST, DATA_ROOT, "val", 256, augment=False, normalization="cdcn_official")
val_loader = DataLoader(val_data, batch_size=8, shuffle=False, num_workers=2)
images = next(iter(val_loader))["image"].to(device)
with torch.no_grad():
    assert torch.equal(e1(images)["depth"], e2(images)["depth"])
replayed = score_loader(e1, val_loader, device)
saved = pd.read_csv(E1_RUN / "val_frame_scores.csv", dtype={"sample_id": str})
paired = saved.merge(replayed, on=["sample_id", "video_id", "label"], suffixes=("_saved", "_replayed"), validate="one_to_one")
assert len(paired) == len(saved) == len(replayed)
assert np.allclose(paired.score_saved, paired.score_replayed, atol=1e-6, rtol=1e-5), "Không tái lập được validation score E1; kiểm tra dataset/crop/version trước train"
print("PASS: same manifest, exact backbone tensors, identical depth, reproduced E1 validation")
del e1, e2, images
torch.cuda.empty_cache()
'''), code('''#@title 2.3 Train smoke 1 epoch, rồi full 10 epoch (validation chọn best)
def registered_run(payload, path):
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    candidates = []
    for folder in RUNS_DIR.glob(payload["experiment_id"] + "_seed42_*"):
        if all((folder / name).is_file() for name in ("best.ckpt", "metrics.json", "config.yaml", "manifest_checksum.json")):
            existing = yaml.safe_load((folder / "config.yaml").read_text())
            if existing == payload and json.loads((folder / "manifest_checksum.json").read_text())["sha256"] == expected_manifest:
                candidates.append(folder)
    if not candidates:
        run([sys.executable, "scripts/run_experiment.py", path], cwd=REPO_ROOT)
        return registered_run(payload, path)
    return sorted(candidates)[-1]

def assert_frozen_backbone(folder):
    result = torch.load(folder / "best.ckpt", map_location="cpu", weights_only=False)
    assert all(torch.equal(value, result["model"]["backbone." + key]) for key, value in e1_state["model"].items()), "Backbone hoặc BatchNorm thay đổi"
    assert json.loads((folder / "initial_checkpoint.json").read_text())["sha256"] == manifest_checksum(E1_RUN / "best.ckpt")

import copy
smoke_config = copy.deepcopy(config)
smoke_config["experiment_id"] += "_SMOKE"
smoke_config["training"]["stages"][0]["epochs"] = 1
SMOKE_RUN = registered_run(smoke_config, REPO_ROOT / "configs/round4_smoke_runtime.yaml")
assert_frozen_backbone(SMOKE_RUN)
smoke_log = pd.read_csv(SMOKE_RUN / "train_log.csv")
assert np.isfinite(smoke_log[["train_loss", "val_loss"]].to_numpy()).all()
E2_RUN = registered_run(config, CONFIG_PATH)
assert_frozen_backbone(E2_RUN)
print("Full E2:", E2_RUN)
'''), code('''#@title 2.4 Bảng validation và BCE curve
from deepface_pad.metrics import evaluate_scores
import matplotlib.pyplot as plt
e1_val = pd.read_csv(E1_RUN / "val_scores.csv")
e1_threshold = json.loads((E1_RUN / "threshold.json").read_text())
assert e1_threshold["source"] == "validation"
e2_threshold = json.loads((E2_RUN / "threshold.json").read_text())
assert e2_threshold["source"] == "validation"
val_metrics = pd.DataFrame([
    {"model": "E1 fixed mean", **evaluate_scores(e1_val.label.to_numpy(), e1_val.score.to_numpy(), e1_threshold["threshold"]).to_dict()},
    {"model": "E2 frozen head", **json.loads((E2_RUN / "metrics.json").read_text())},
]).set_index("model")
display(val_metrics.style.format({"apcer":"{:.4%}", "bpcer":"{:.4%}", "acer":"{:.4%}", "eer":"{:.4%}", "auc":"{:.6f}", "threshold":"{:.8f}"}))
log = pd.read_csv(E2_RUN / "train_log.csv")
best = log.loc[log.val_loss.idxmin()]
fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(log.epoch, log.train_loss, label="train BCE")
ax.plot(log.epoch, log.val_loss, label="validation BCE")
ax.scatter([best.epoch], [best.val_loss], color="red", label="best validation epoch")
ax.set(xlabel="Epoch", ylabel="BCE loss", title="E2: head-only training")
ax.grid(alpha=.25); ax.legend(); fig.tight_layout()
FIGURE_DIR = REPORTS_DIR / E2_RUN.name
FIGURE_DIR.mkdir(exist_ok=True)
fig.savefig(FIGURE_DIR / "e2-bce-curve.png", dpi=180)
plt.show()
print("Best epoch:", int(best.epoch), "— chosen by validation BCE, not test")
'''), markdown("## 3. Đóng băng rồi so sánh trên CASIA test đã mở\nBảng này không phải xác nhận độc lập mới. Không chọn thêm biến thể bằng kết quả test.\n"), code('''#@title 3.1 Khóa artifact rồi score E2 một lần; tái dùng E1 đã có
freeze = {
    "config_sha256": manifest_checksum(E2_RUN / "config.yaml"),
    "checkpoint_sha256": manifest_checksum(E2_RUN / "best.ckpt"),
    "threshold_sha256": manifest_checksum(E2_RUN / "threshold.json"),
    "manifest_sha256": manifest_checksum(DEPTH_MANIFEST),
    "evaluation_status": "CASIA development test already observed in round 3",
}
freeze_path = E2_RUN / "comparison_freeze.json"
if freeze_path.is_file():
    assert json.loads(freeze_path.read_text()) == freeze, "Frozen E2 artifact changed"
else:
    freeze_path.write_text(json.dumps(freeze, indent=2), encoding="utf-8")
assert (E1_RUN / "test_metrics.json").is_file() and (E1_RUN / "test_scores.csv").is_file()
if not (E2_RUN / "test_metrics.json").is_file():
    run([sys.executable, "scripts/score_checkpoint.py", "--run-dir", E2_RUN, "--split", "test"], cwd=REPO_ROOT)
comparison = pd.DataFrame([
    {"model": "E1 fixed mean", **json.loads((E1_RUN / "test_metrics.json").read_text())},
    {"model": "E2 frozen head", **json.loads((E2_RUN / "test_metrics.json").read_text())},
]).set_index("model")
comparison["delta_acer_vs_E1"] = comparison.acer - comparison.loc["E1 fixed mean", "acer"]
comparison.to_csv(FIGURE_DIR / "e1-e2-development-test.csv")
display(comparison.style.format({"apcer":"{:.4%}", "bpcer":"{:.4%}", "acer":"{:.4%}", "eer":"{:.4%}", "auc":"{:.6f}", "threshold":"{:.8f}", "delta_acer_vs_E1":"{:+.4%}"}))
print("One seed, CASIA development protocol, test previously observed; not SOTA evidence.")
'''), code('''#@title 3.2 E2 sửa được gì và làm sai thêm gì? So sánh theo cùng video
def paired_errors(split):
    first = pd.read_csv(E1_RUN / f"{split}_scores.csv", dtype={"video_id": str}).rename(columns={"score":"score_e1"})
    second = pd.read_csv(E2_RUN / f"{split}_scores.csv", dtype={"video_id": str}).rename(columns={"score":"score_e2"})
    result = first.merge(second, on=["video_id", "label"], validate="one_to_one")
    assert len(result) == len(first) == len(second)
    result["pred_e1"] = (result.score_e1 >= e1_threshold["threshold"]).astype(int)
    result["pred_e2"] = (result.score_e2 >= e2_threshold["threshold"]).astype(int)
    result["correct_e1"] = result.pred_e1 == result.label
    result["correct_e2"] = result.pred_e2 == result.label
    result["change"] = np.select([
        ~result.correct_e1 & result.correct_e2,
        result.correct_e1 & ~result.correct_e2,
        ~result.correct_e1 & ~result.correct_e2,
    ], ["fixed_by_E2", "new_error_E2", "both_wrong"], default="both_correct")
    metadata = pd.read_csv(MANIFEST, dtype={"video_id": str})
    columns = ["video_id", "label", "attack_type", "quality"]
    metadata = metadata.loc[metadata.split == split, columns].drop_duplicates()
    return result.merge(metadata, on=["video_id", "label"], validate="one_to_one")

errors = paired_errors("test")
errors.to_csv(FIGURE_DIR / "e1-e2-paired-errors.csv", index=False)
display(errors.groupby(["label", "attack_type", "change"]).size().rename("videos").to_frame())
display(errors[errors.change != "both_correct"])
val_errors = paired_errors("val")
val_errors.to_csv(FIGURE_DIR / "e1-e2-validation-paired-errors.csv", index=False)
fig, axes = plt.subplots(1, 2, figsize=(10, 4))
for ax, column, title, threshold in zip(axes, ["score_e1", "score_e2"], ["E1 mean depth", "E2 head sigmoid"], [e1_threshold["threshold"], e2_threshold["threshold"]]):
    for label, name in [(0, "attack"), (1, "live")]:
        ax.hist(errors.loc[errors.label == label, column], bins=25, alpha=.55, label=name)
    ax.axvline(threshold, color="black", linestyle="--", label="validation threshold")
    ax.set(xlabel="Score (different scales)", ylabel="Videos", title=title)
    ax.legend()
fig.tight_layout(); fig.savefig(FIGURE_DIR / "e1-e2-score-distributions.png", dpi=180); plt.show()
'''), code('''#@title 3.3 Params và latency — RGB→score, batch 1, cùng GPU
e1 = build_model(e1_config).to(device).eval()
e1.load_state_dict(e1_state["model"])
e2 = build_model(config).to(device).eval()
trained = torch.load(E2_RUN / "best.ckpt", map_location=device, weights_only=False)
e2.load_state_dict(trained["model"])
sample = torch.randn(1, 3, 256, 256, device=device)

@torch.no_grad()
def latency(model, tensor, warmup=10, repeats=50):
    for _ in range(warmup):
        model(tensor)
    torch.cuda.synchronize()
    measurements = []
    for _ in range(repeats):
        torch.cuda.synchronize()
        start = time.perf_counter()
        model(tensor)
        torch.cuda.synchronize()
        measurements.append((time.perf_counter() - start) * 1000)
    return {"latency_p50_ms": float(np.median(measurements)), "latency_p95_ms": float(np.percentile(measurements, 95))}

efficiency = pd.DataFrame([
    {"model":"E1 fixed mean", "parameters":sum(p.numel() for p in e1.parameters()), **latency(e1, sample)},
    {"model":"E2 frozen head", "parameters":sum(p.numel() for p in e2.parameters()), **latency(e2, sample)},
]).set_index("model")
efficiency["fps_from_p50"] = 1000 / efficiency.latency_p50_ms
efficiency.to_csv(FIGURE_DIR / "e1-e2-efficiency.csv")
display(efficiency)
print("Head parameters:", sum(p.numel() for p in e2.head.parameters()))
print("Added params (%):", 100 * (efficiency.parameters.iloc[1] / efficiency.parameters.iloc[0] - 1))
print("Latency includes model forward only; no crop, disk load, CPU-to-GPU transfer or webcam.")
print("GPU:", torch.cuda.get_device_name(0), "torch:", torch.__version__)
'''), markdown("""## 4. Chuẩn bị báo cáo

Lấy bảng test phát triển, BCE curve, paired error CSV và efficiency CSV trong
`/content/drive/MyDrive/face-pad/reports/<E2_RUN_ID>`.

- Nêu rõ E1 và E2 có cùng backbone/checkpoint/depth map; thay cách đọc map.
- ACER/APCER/BPCER và threshold đánh giá tại operating point; AUC/EER xét khả năng phân tách.
- Báo cả video được sửa và lỗi mới; improvement có thể âm hoặc bằng 0.
- Một seed và CASIA test đã mở chỉ cho kết luận phát triển. UCDCN là tiền lệ;
  chưa so với mô hình hiện đại, nhiều seed hay benchmark độc lập.
- Không so BCE của E2 với depth loss của E1 như thể hai loss có cùng ý nghĩa.
- Nếu run chưa xong, báo trạng thái thật; không điền số giả.

Notebook sạch này chưa chứa output train. File E1 đã chạy vẫn được giữ riêng.
""")])
    return {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python"}, "colab": {"name": "Face_PAD_Round4_Official_Frozen_Head.ipynb"}, "accelerator": "GPU"}, "nbformat": 4, "nbformat_minor": 5}


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    notebook = build(root)
    for index, cell in enumerate(notebook["cells"]):
        cell["id"] = f"round4-{index:02d}"
    destination = root / "notebooks/Face_PAD_Round4_Official_Frozen_Head.ipynb"
    destination.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(destination)
