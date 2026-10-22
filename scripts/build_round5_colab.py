"""Build a clean, manually gated continuation of the existing CASIA protocol."""
from __future__ import annotations

import json
from pathlib import Path

from build_round4_colab import code, markdown


def build(root: Path) -> dict:
    prior = json.loads((root / "notebooks/Face_PAD_Round4_Official_Frozen_Head_Clean.ipynb").read_text(encoding="utf-8"))
    restore = {"".join(c["source"]).splitlines()[0].split()[1]: "".join(c["source"])
               for c in prior["cells"] if c["cell_type"] == "code"
               and "".join(c["source"]).startswith("#@title 1.")}
    cells = [markdown("""# Lượt 5 — E3, E3b và E4 trên cùng CASIA của E1/E2

Đọc `reports/ROUND_5_CASIA_RUNBOOK.md`. Chưa có kết quả E3/E3b/E4.
**Bắt đầu bằng cell 0.1–1.5, rồi dừng và gửi output PREFLIGHT cho Codex.**
Không dùng Run all qua các cổng `RUN_SMOKE`, `RUN_FULL`, `OPEN_TEST`.
Mọi cổng mặc định False. Không chạy lại E0/E1/E2, không đổi dataset hoặc split.
Test đã quan sát trước đây: đây là thí nghiệm phát triển trên CASIA.
"""), code('''#@title 0.1 Mount Drive, helper và đường dẫn
from google.colab import drive, files
drive.mount("/content/drive")
import copy, importlib, json, os, shutil, subprocess, sys, tarfile
from pathlib import Path
import numpy as np
import pandas as pd
import yaml
from IPython.display import display
REPO_ROOT = Path("/content/round5-source/DeepFace-PAD")
DRIVE_ROOT = Path("/content/drive/MyDrive/face-pad")
RUNS_DIR = DRIVE_ROOT / "runs"
REPORTS_DIR = DRIVE_ROOT / "reports"
DATA_ROOT = Path("/content/datasets/casia-fasd")
DEPTH_ROOT = DATA_ROOT / "depth"
DEPTH_LEDGER = DEPTH_ROOT / "depth_status.csv"
DEPTH_BACKUP = DRIVE_ROOT / "depth-checkpoints/casia-fasd"
MANIFEST = REPO_ROOT / "data/manifests/casia_fasd_debug.csv"
DEPTH_MANIFEST = REPO_ROOT / "data/manifests/casia_fasd_debug_with_depth.csv"
E1_RUN = RUNS_DIR / "CASIA_E1_CDCN_OFFICIAL_seed42_20260921T114029Z"
def run(command, cwd=None):
    subprocess.run([str(item) for item in command], cwd=str(cwd) if cwd else None, check=True)
'''), code('''#@title 0.2 Nạp source ZIP đã commit
archive = Path("/content/DeepFace-PAD-Round5-source.zip")
drive_archive = DRIVE_ROOT / "handoffs/round5-20261016/DeepFace-PAD-Round5-source.zip"
if not archive.is_file() and drive_archive.is_file():
    shutil.copy2(drive_archive, archive)
if not archive.is_file():
    print("Upload DeepFace-PAD-Round5-source.zip được cung cấp cùng notebook.")
    files.upload()
assert archive.is_file(), "Thiếu đúng source ZIP; dừng và gửi thông báo này"
shutil.unpack_archive(str(archive), "/content/round5-source")
SOURCE_COMMIT = (REPO_ROOT / "SOURCE_COMMIT.txt").read_text().strip()
assert len(SOURCE_COMMIT) == 40
run([sys.executable, "-m", "pip", "install", "-q", "-e", ".[dev]"], cwd=REPO_ROOT)
os.chdir(REPO_ROOT)
sys.path.insert(0, str(REPO_ROOT / "src"))
importlib.invalidate_caches()
OUTPUT_DIR = REPORTS_DIR / f"round5-{SOURCE_COMMIT[:12]}"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DEPTH_QA = OUTPUT_DIR / "depth-qa.json"
print("Source commit:", SOURCE_COMMIT)
'''), code('''#@title 1.1 Khôi phục đúng ZIP dataset cũ trên Drive
def looks_like_casia(path):
    return (path / "train/live").is_dir() and (path / "test/spoof").is_dir()
if not looks_like_casia(DATA_ROOT):
    dataset_zip = DRIVE_ROOT / "casia-fasd.zip"
    assert dataset_zip.is_file(), "Thiếu face-pad/casia-fasd.zip; dừng, không tải dataset khác"
    DATA_ROOT.parent.mkdir(parents=True, exist_ok=True)
    shutil.unpack_archive(str(dataset_zip), str(DATA_ROOT.parent))
    if not looks_like_casia(DATA_ROOT):
        roots = [p.parent for p in DATA_ROOT.parent.rglob("train") if looks_like_casia(p.parent)]
        assert len(roots) == 1, f"Không xác định duy nhất CASIA root: {roots}"
        shutil.copytree(roots[0], DATA_ROOT, dirs_exist_ok=True)
assert looks_like_casia(DATA_ROOT)
print("Dataset:", DATA_ROOT)
'''), code(restore["1.2"]), code('''#@title 1.3 Khôi phục cache đã kiểm toán, không chạy 3DDFA
from deepface_pad.data import manifest_checksum
cache_tar = DRIVE_ROOT / "depth-checkpoints/casia-fasd-depth-checkpoint.tar"
assert cache_tar.is_file(), "Thiếu TAR cache đã kiểm toán; dừng để kiểm tra"
assert manifest_checksum(cache_tar) == "26cfa7f26d61e3a71372404008f5dc9dd696af931172850986a8642e440b3d80"
local_tar = Path("/content/casia-fasd-depth-checkpoint.tar")
shutil.copy2(cache_tar, local_tar)
with tarfile.open(local_tar) as archive:
    for member in archive.getmembers():
        destination = (DATA_ROOT / member.name).resolve()
        assert destination.is_relative_to(DATA_ROOT.resolve())
        assert member.isfile() or member.isdir(), "Cache có entry không phải file/directory"
    archive.extractall(DATA_ROOT, filter="data")
# Tái tạo attack zero targets và ledger; live maps hợp lệ được tái sử dụng.
run([sys.executable, "scripts/generate_depth.py", MANIFEST,
     "--data-root", DATA_ROOT, "--output-root", DEPTH_ROOT], cwd=REPO_ROOT)
ledger = pd.read_csv(DEPTH_LEDGER, keep_default_na=False)
assert (ledger.status == "complete_bona_fide").sum() == 3000
assert (ledger.status == "complete_attack_zero").sum() == 9000
display(ledger.groupby("status").size().rename("samples").to_frame())
'''), code(restore["1.4"]), code('''#@title 1.5 Preflight: hash và depth phải khớp E1 — dừng tại đây
import torch
from deepface_pad.preflight import inspect_training_inputs
from deepface_pad.train import build_model, load_initial_weights
expected_source = "58fffcc2fb29649af1b8424d78b85067eefbd0321fde6b27fbd0803ef0fd7192"
expected_depth = "4c302c9039e48a8ea6baedf426b26e1b0a6663bc295c661bb71fefccdb9b37fd"
expected_e1 = "679810c001e526cafed8685fe731a7d5c539fd3fb9c5a9fb31725b7dbdf57024"
assert manifest_checksum(MANIFEST) == expected_source
assert manifest_checksum(DEPTH_MANIFEST) == expected_depth
assert manifest_checksum(E1_RUN / "best.ckpt") == expected_e1
CONFIG_FILES = {"E3": "casia_e3_joint_bce.yaml", "E3b": "casia_e3b_staged_bce.yaml", "E4": "casia_e4_staged_focal.yaml"}
CONFIGS = {}
for key, filename in CONFIG_FILES.items():
    cfg = yaml.safe_load((REPO_ROOT / "configs" / filename).read_text())
    cfg["source_commit"] = SOURCE_COMMIT
    cfg["data"].update(manifest=str(DEPTH_MANIFEST), source_manifest=str(MANIFEST),
                        depth_ledger=str(DEPTH_LEDGER), root=str(DATA_ROOT))
    cfg["training"]["init_checkpoint"] = str(E1_RUN / "best.ckpt")
    CONFIGS[key] = cfg
_, snapshot = inspect_training_inputs(CONFIGS["E3"])
old = json.loads((E1_RUN / "depth_input_snapshot.json").read_text())
assert snapshot["depth_audit"]["artifact_checksums"] == old["depth_audit"]["artifact_checksums"], "Cache khác E1"
model = build_model(CONFIGS["E3"])
load_initial_weights(model, E1_RUN / "best.ckpt", torch.device("cpu"))
del model
mf = pd.read_csv(DEPTH_MANIFEST)
summary = mf.groupby("split").agg(frames=("sample_id", "size"), videos=("video_id", "nunique"), subjects=("subject_id", "nunique"))
display(summary)
assert summary.frames.to_dict() == {"test":7200, "train":3840, "val":960}
assert summary.videos.to_dict() == {"test":360, "train":192, "val":48}
assert not (mf.groupby("subject_id").split.nunique() > 1).any()
preflight = {"source_commit": SOURCE_COMMIT, "source_manifest": expected_source,
             "depth_manifest": expected_depth, "initializer": expected_e1,
             "depth_samples": snapshot["depth_audit"]["samples"], "valid": True}
(OUTPUT_DIR / "preflight.json").write_text(json.dumps(preflight, indent=2))
print("PREFLIGHT PASS", json.dumps(preflight, indent=2))
print("DỪNG: gửi output cell này cho Codex trước khi bật cổng smoke.")
'''), markdown("## 2. Smoke từng nhánh — chỉ mở cổng sau khi preflight đã kiểm tra\n"), code('''#@title 2.0 Tests và GPU
run([sys.executable, "-m", "pytest", "-q"], cwd=REPO_ROOT)
assert torch.cuda.is_available(), "Chọn Runtime > Change runtime type > GPU; chạy lại setup nếu runtime bị xóa"
print(torch.__version__, torch.cuda.get_device_name(0))
'''), code('''#@title 2.1 Cổng smoke: một epoch mỗi stage, validation only
RUN_SMOKE = False
assert RUN_SMOKE, "Dừng: chỉ đổi True sau khi đã kiểm tra preflight"
REQUIRED = ["config.yaml", "best.ckpt", "checkpoint_selection.json", "metrics.json",
            "val_scores.csv", "val_frame_scores.csv", "threshold.json", "depth_input_snapshot.json"]
def train_or_reuse(key, smoke=False):
    cfg = copy.deepcopy(CONFIGS[key])
    if smoke:
        cfg["experiment_id"] += "_SMOKE"
        for stage in cfg["training"]["stages"]:
            stage["epochs"] = 1
    config_path = REPO_ROOT / "configs" / f"round5-{key}-{'smoke' if smoke else 'full'}.yaml"
    config_path.write_text(yaml.safe_dump(cfg, sort_keys=False))
    expected_config = manifest_checksum(config_path)
    registration = OUTPUT_DIR / f"{key}-{'smoke' if smoke else 'full'}-registration.json"
    record = {"config_sha256": expected_config, "source_commit": SOURCE_COMMIT, "config": cfg}
    if registration.is_file():
        assert json.loads(registration.read_text()) == record, "Đăng ký đã khác: dừng và hỏi Codex"
    else:
        registration.write_text(json.dumps(record, indent=2))
    candidates = sorted(RUNS_DIR.glob(f"{cfg['experiment_id']}_seed{cfg['seed']}_*"))
    complete = [p for p in candidates if all((p / f).is_file() for f in REQUIRED)]
    assert all(manifest_checksum(p / "config.yaml") == expected_config for p in complete), "Run đã có khác config"
    assert len(complete) <= 1, "Nhiều run hoàn tất: gửi danh sách để kiểm tra, không tự lấy best test"
    if not complete:
        assert not candidates, f"Có run chưa hoàn tất, giữ nguyên và gửi Codex: {candidates}"
        run([sys.executable, "scripts/run_experiment.py", config_path], cwd=REPO_ROOT)
        complete = [p for p in RUNS_DIR.glob(f"{cfg['experiment_id']}_seed{cfg['seed']}_*")
                    if all((p / f).is_file() for f in REQUIRED)]
    assert len(complete) == 1
    folder = complete[0]
    selected = json.loads((folder / "checkpoint_selection.json").read_text())
    assert selected["reported_stage"] == "joint"
    assert selected["stages"][-1]["selection_metric"] == "classification_bce"
    assert manifest_checksum(folder / "config.yaml") == expected_config
    return folder
SMOKES = {key: train_or_reuse(key, smoke=True) for key in CONFIGS}
'''), code('''#@title 2.2 Checklist smoke và ảnh depth validation
from IPython.display import Image as DisplayImage
for key, folder in SMOKES.items():
    print(key, folder)
    log = pd.read_csv(folder / "train_log.csv")
    assert np.isfinite(log[["train_loss", "val_loss", "val_selection_loss"]]).all().all()
    display(log)
    cases = OUTPUT_DIR / f"{key}-smoke-depth-cases"
    run([sys.executable, "scripts/visualize_depth_cases.py", "--run-dir", folder,
         "--split", "val", "--count", "4", "--output-dir", cases], cwd=REPO_ROOT)
    for picture in sorted(cases.glob("*.png")):
        display(DisplayImage(filename=str(picture)))
print("DỪNG: kiểm tra ảnh và gửi 3 smoke run ID/log trước full run.")
'''), markdown("## 3. Full validation — ngân sách 16 epoch/nhánh, không mở test\n"), code('''#@title 3.1 Cổng full run
RUN_FULL = False
assert RUN_FULL, "Dừng: chỉ đổi True sau khi smoke cả ba nhánh đạt"
assert len(SMOKES) == 3
FULL_RUNS = {key: train_or_reuse(key) for key in CONFIGS}
'''), code('''#@title 3.2 Bảng validation và depth MAE; gửi trước khi mở test
rows = []
for key, folder in FULL_RUNS.items():
    checkpoint = torch.load(folder / "best.ckpt", map_location="cpu", weights_only=False)
    metrics = json.loads((folder / "metrics.json").read_text())
    rows.append({"variant":key, "run":folder.name, **metrics,
                 "val_selection_bce":checkpoint["selection_value"], "selected_epoch":checkpoint["epoch"]})
    run([sys.executable, "scripts/evaluate_depth.py", "--run-dir", folder, "--split", "val"], cwd=REPO_ROOT)
validation = pd.DataFrame(rows)
validation.to_csv(OUTPUT_DIR / "validation.csv", index=False)
display(validation.style.format({"apcer":"{:.4%}", "bpcer":"{:.4%}", "acer":"{:.4%}",
                                 "eer":"{:.4%}", "auc":"{:.6f}", "val_selection_bce":"{:.6f}"}))
ranked = validation.sort_values(["acer", "eer", "auc", "val_selection_bce"],
                               ascending=[True,True,False,True], kind="stable")
SELECTED_VARIANT = ranked.iloc[0].variant
print("Validation-selected:", SELECTED_VARIANT)
print("DỪNG: gửi bảng này và depth_val_metrics.json của ba run; chưa mở test.")
'''), code('''#@title 4.1 Khóa ba run trước test
freeze = {"source_commit": SOURCE_COMMIT, "selection_source":"validation",
          "selected_variant":SELECTED_VARIANT, "runs":{}}
for key, folder in FULL_RUNS.items():
    freeze["runs"][key] = {"run":folder.name, "hashes":{
        name:manifest_checksum(folder / name) for name in ["config.yaml", "best.ckpt", "threshold.json", "metrics.json", "manifest_checksum.json"]}}
freeze_path = OUTPUT_DIR / "comparison_freeze.json"
if freeze_path.is_file():
    assert json.loads(freeze_path.read_text()) == freeze, "Freeze khác: dừng"
else:
    assert all(not (folder / "test_metrics.json").exists() for folder in FULL_RUNS.values()), "Đã có test trước freeze"
    freeze_path.write_text(json.dumps(freeze, indent=2))
print(freeze_path)
'''), code('''#@title 4.2 Cổng test phát triển — không chọn lại model bằng test
OPEN_TEST = False
assert OPEN_TEST, "Dừng: chỉ đổi True sau khi validation và freeze được kiểm tra"
assert json.loads(freeze_path.read_text()) == freeze
for key, folder in FULL_RUNS.items():
    assert all(manifest_checksum(folder / name) == value for name, value in freeze["runs"][key]["hashes"].items())
    names = ["test_metrics.json", "test_scores.csv", "test_frame_scores.csv"]
    existing = [(folder / name).is_file() for name in names]
    assert all(existing) or not any(existing), "Test artifact dở dang: dừng, không tự score lại"
    if not any(existing):
        run([sys.executable, "scripts/score_checkpoint.py", "--run-dir", folder, "--split", "test"], cwd=REPO_ROOT)
test = pd.DataFrame([{"variant":key, "run":folder.name, **json.loads((folder / "test_metrics.json").read_text())}
                     for key, folder in FULL_RUNS.items()])
test.to_csv(OUTPUT_DIR / "development-test.csv", index=False)
display(test.style.format({"apcer":"{:.4%}", "bpcer":"{:.4%}", "acer":"{:.4%}", "eer":"{:.4%}", "auc":"{:.6f}"}))
print("Giữ lựa chọn từ validation:", SELECTED_VARIANT, "| one seed, CASIA development protocol")
print("Gửi notebook đã lưu và đường dẫn:", OUTPUT_DIR)
''')]
    for index, cell in enumerate(cells):
        cell["id"] = f"round5-{index:02d}"
    return {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name":"python"}, "colab":{"name":"Face_PAD_Round5_CASIA_E3_E4.ipynb"}}, "nbformat":4, "nbformat_minor":5}


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    destination = root / "notebooks/Face_PAD_Round5_CASIA_E3_E4.ipynb"
    destination.write_text(json.dumps(build(root), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(destination)
