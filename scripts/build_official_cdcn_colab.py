"""Build the clean Colab runbook for the official-CDCN E1 correction run."""
from __future__ import annotations

import json
from pathlib import Path


def markdown(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": text.splitlines(keepends=True)}


def code(text: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": text.splitlines(keepends=True),
    }


cells = [
    markdown(
        """# Official CDCN E1 correction — CASIA-FASD

Notebook sạch để đóng lại Lượt 3 bằng **kiến trúc và depth loss CDCN CVPR 2020 của tác giả**.

- Giữ nguyên manifest CASIA subject-disjoint, pseudo-depth 3DDFA V2, E0 và evaluator.
- Giữ preprocessing face-centric frame của E0; 3DDFA depth đã được render trong cùng toạ độ frame.
- Run compact cũ được giữ với nhãn `E1-Lite Pilot`; không ghi đè.
- Không dùng test để chọn epoch, hyperparameter hoặc quyết định extension.
- Không dùng **Run all** qua hai cổng thủ công.

Bạn chỉ cần chọn GPU runtime, chạy tuần tự, duyệt smoke cases, rồi mở locked test đúng một lần sau khi full run đã khóa.
"""
    ),
    code(
        '''#@title 0.1 Mount Drive, đường dẫn và helper
from google.colab import drive
drive.mount("/content/drive")

import importlib, json, shutil, subprocess, sys, time
from pathlib import Path
import numpy as np
import pandas as pd
from IPython.display import Image as DisplayImage, display

REPO_URL = "https://github.com/Violetta147/face-recognition-depth-pad.git"
REPO_ROOT = Path("/content/face-recognition-depth-pad")
OFFICIAL_ROOT = Path("/content/CDCN-official")
OFFICIAL_URL = "https://github.com/ZitongYu/CDCN.git"
OFFICIAL_COMMIT = "fd8370e8f32bdd090a3552f5a1fe4c301fa99f2b"
DATA_ROOT = Path("/content/datasets/casia-fasd")
DRIVE_ROOT = Path("/content/drive/MyDrive/face-pad")
RUNS_DIR = DRIVE_ROOT / "runs"
REPORTS_DIR = DRIVE_ROOT / "reports"
DEPTH_BACKUP = DRIVE_ROOT / "depth-checkpoints" / "casia-fasd"
MANIFEST = REPO_ROOT / "data/manifests/casia_fasd_debug.csv"
DEPTH_MANIFEST = REPO_ROOT / "data/manifests/casia_fasd_debug_with_depth.csv"
DEPTH_ROOT = DATA_ROOT / "depth"
DEPTH_LEDGER = DEPTH_ROOT / "depth_status.csv"
DEPTH_QA = REPORTS_DIR / "casia-depth-qa-official-e1.json"

for directory in (RUNS_DIR, REPORTS_DIR):
    directory.mkdir(parents=True, exist_ok=True)

def run(command, cwd=None):
    command = [str(item) for item in command]
    print("$", " ".join(command))
    subprocess.run(command, cwd=str(cwd) if cwd else None, check=True)

def latest_complete(pattern, required=("best.ckpt", "metrics.json")):
    candidates = [p for p in RUNS_DIR.glob(pattern) if all((p / f).is_file() for f in required)]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)
'''
    ),
    code(
        '''#@title 0.2 Clone project, install và xác nhận revision
if (REPO_ROOT / ".git").is_dir():
    run(["git", "-C", REPO_ROOT, "pull", "--ff-only"])
else:
    run(["git", "clone", REPO_URL, REPO_ROOT])

run([sys.executable, "-m", "pip", "install", "-q", "-e", ".[dev]"], cwd=REPO_ROOT)
source_root = REPO_ROOT / "src"
if str(source_root) not in sys.path:
    sys.path.insert(0, str(source_root))
importlib.invalidate_caches()

required = [
    REPO_ROOT / "src/deepface_pad/models/cdcn_official.py",
    REPO_ROOT / "scripts/verify_official_cdcn_port.py",
    REPO_ROOT / "configs/casia_e1_cdcn_official_smoke.yaml",
    REPO_ROOT / "configs/casia_e1_cdcn_official.yaml",
]
missing = [str(path) for path in required if not path.is_file()]
assert not missing, f"GitHub chưa có correction code: {missing}"
print("Project commit:", subprocess.check_output(["git", "-C", REPO_ROOT, "rev-parse", "HEAD"], text=True).strip())
'''
    ),
    code(
        '''#@title 0.3 Unit tests và GPU
import torch
run([sys.executable, "-m", "pytest", "-q"], cwd=REPO_ROOT)
assert torch.cuda.is_available(), "Hãy chọn Runtime > Change runtime type > GPU"
print("PyTorch:", torch.__version__)
print("GPU:", torch.cuda.get_device_name(0))
'''
    ),
    code(
        '''#@title 0.4 Clone upstream CDCN đúng commit và kiểm chứng port số học
if not (OFFICIAL_ROOT / ".git").is_dir():
    run(["git", "clone", OFFICIAL_URL, OFFICIAL_ROOT])
run(["git", "-C", OFFICIAL_ROOT, "fetch", "origin", OFFICIAL_COMMIT])
run(["git", "-C", OFFICIAL_ROOT, "checkout", "--detach", OFFICIAL_COMMIT])
actual = subprocess.check_output(["git", "-C", OFFICIAL_ROOT, "rev-parse", "HEAD"], text=True).strip()
assert actual == OFFICIAL_COMMIT
run([sys.executable, "scripts/verify_official_cdcn_port.py", "--official-root", OFFICIAL_ROOT], cwd=REPO_ROOT)
'''
    ),
    markdown("## 1. Khôi phục dataset và pseudo-depth đã khóa\n"),
    code(
        '''#@title 1.1 Chuẩn bị CASIA-FASD ở đường dẫn chuẩn
def looks_like_casia(path):
    return (path / "train" / "live").is_dir() and (path / "test" / "spoof").is_dir()

def find_casia_root(base):
    if looks_like_casia(base):
        return base
    if base.exists():
        for train_dir in base.rglob("train"):
            if looks_like_casia(train_dir.parent):
                return train_dir.parent
    return None

if not looks_like_casia(DATA_ROOT):
    drive_dataset = DRIVE_ROOT / "datasets" / "casia-fasd"
    dataset_zip = DRIVE_ROOT / "casia-fasd.zip"
    DATA_ROOT.parent.mkdir(parents=True, exist_ok=True)
    if looks_like_casia(drive_dataset):
        shutil.copytree(drive_dataset, DATA_ROOT, dirs_exist_ok=True)
    elif dataset_zip.is_file():
        shutil.unpack_archive(str(dataset_zip), str(DATA_ROOT.parent))
        discovered = find_casia_root(DATA_ROOT.parent)
        assert discovered is not None, "Không tìm thấy CASIA root sau khi giải nén"
        if discovered.resolve() != DATA_ROOT.resolve():
            shutil.copytree(discovered, DATA_ROOT, dirs_exist_ok=True)
    else:
        run([sys.executable, "-m", "pip", "install", "-q", "kagglehub"])
        import kagglehub
        downloaded = Path(kagglehub.dataset_download("immada/casia-fasd"))
        roots = [p.parent for p in downloaded.rglob("train") if looks_like_casia(p.parent)]
        assert roots, "Không tìm thấy CASIA root trong Kaggle download"
        shutil.copytree(roots[0], DATA_ROOT, dirs_exist_ok=True)

assert looks_like_casia(DATA_ROOT), f"CASIA chưa đúng cấu trúc: {DATA_ROOT}"
print("Dataset:", DATA_ROOT)
'''
    ),
    code(
        '''#@title 1.2 Tạo lại manifest xác định và kiểm tra protocol
run([
    sys.executable, "scripts/prepare_casia_fasd.py",
    "--data-root", DATA_ROOT,
    "--output-dir", REPO_ROOT / "data/manifests",
    "--frames-per-video", "20",
    "--val-subjects", "4,9,14,19",
], cwd=REPO_ROOT)
run([sys.executable, "scripts/validate_manifest.py", MANIFEST, "--data-root", DATA_ROOT, "--subject-disjoint"], cwd=REPO_ROOT)
'''
    ),
    code(
        '''#@title 1.3 Khôi phục cache depth từ Drive; không tái sinh map hợp lệ
assert DEPTH_BACKUP.is_dir(), f"Thiếu depth checkpoint trên Drive: {DEPTH_BACKUP}"
DEPTH_ROOT.mkdir(parents=True, exist_ok=True)

# Google Drive có độ trễ cao với hàng nghìn file nhỏ. Copy từng file, bỏ qua file
# đã đủ byte và in tiến độ để cell có thể resume sau khi runtime bị ngắt.
backup_files = [path for path in DEPTH_BACKUP.iterdir() if path.is_file()]
copied = skipped = 0
for index, source in enumerate(backup_files, start=1):
    destination = DEPTH_ROOT / source.name
    if destination.is_file() and destination.stat().st_size == source.stat().st_size:
        skipped += 1
    else:
        shutil.copy2(source, destination)
        copied += 1
    if index % 250 == 0 or index == len(backup_files):
        print(f"Depth restore {index}/{len(backup_files)} — copied={copied}, reused={skipped}", flush=True)

# Checkpoint Drive chỉ giữ 3.000 live maps để tránh 9.000 file zero dư thừa.
# Lệnh này tạo lại attack zero-maps ở local, tái sử dụng toàn bộ live maps hợp lệ
# và làm mới ledger; nó không chạy 3DDFA.
run([
    sys.executable, "scripts/generate_depth.py", MANIFEST,
    "--data-root", DATA_ROOT,
    "--output-root", DEPTH_ROOT,
], cwd=REPO_ROOT)

assert DEPTH_LEDGER.is_file(), f"Thiếu ledger: {DEPTH_LEDGER}"

ledger = pd.read_csv(DEPTH_LEDGER, keep_default_na=False, dtype={"sample_id": str})
display(ledger.groupby("status").size().rename("samples").to_frame())
pending = int((ledger.status == "pending_3ddfa").sum())
failed = int((ledger.status == "failed_bona_fide").sum())
complete_live = int((ledger.status == "complete_bona_fide").sum())
assert pending == 0 and failed == 0 and complete_live == 3000, (pending, failed, complete_live)
'''
    ),
    code(
        '''#@title 1.4 Materialize manifest, provenance và full depth QA
run([
    sys.executable, "scripts/materialize_depth_manifest.py", MANIFEST,
    "--ledger", DEPTH_LEDGER,
    "--data-root", DATA_ROOT,
    "--output", DEPTH_MANIFEST,
], cwd=REPO_ROOT)
run([
    sys.executable, "scripts/verify_depth_provenance.py",
    "--source", MANIFEST,
    "--ledger", DEPTH_LEDGER,
    "--derived", DEPTH_MANIFEST,
], cwd=REPO_ROOT)
run([
    sys.executable, "scripts/validate_manifest.py", DEPTH_MANIFEST,
    "--data-root", DATA_ROOT, "--require-depth",
], cwd=REPO_ROOT)
run([
    sys.executable, "scripts/audit_depth.py", DEPTH_MANIFEST,
    "--data-root", DATA_ROOT, "--report", DEPTH_QA,
], cwd=REPO_ROOT)
print("Depth QA:", DEPTH_QA)
'''
    ),
    markdown("## 2. Official CDCN smoke gate\n"),
    code(
        '''#@title 2.1 Chạy hoặc tái sử dụng official-CDCN smoke
OFFICIAL_SMOKE = latest_complete("CASIA_E1_CDCN_OFFICIAL_SMOKE_seed42_*")
if OFFICIAL_SMOKE is None:
    run([sys.executable, "scripts/run_experiment.py", "configs/casia_e1_cdcn_official_smoke.yaml"], cwd=REPO_ROOT)
    OFFICIAL_SMOKE = latest_complete("CASIA_E1_CDCN_OFFICIAL_SMOKE_seed42_*")
assert OFFICIAL_SMOKE is not None
print("Official smoke:", OFFICIAL_SMOKE)
display(pd.read_csv(OFFICIAL_SMOKE / "train_log.csv"))
print(json.loads((OFFICIAL_SMOKE / "metrics.json").read_text()))
print(json.loads((OFFICIAL_SMOKE / "model_provenance.json").read_text()))
'''
    ),
    code(
        '''#@title 2.2 Xuất predicted-depth smoke cases
SMOKE_CASES = REPORTS_DIR / f"{OFFICIAL_SMOKE.name}-depth-cases"
run([
    sys.executable, "scripts/visualize_depth_cases.py",
    "--run-dir", OFFICIAL_SMOKE,
    "--split", "val", "--count", "12",
    "--output-dir", SMOKE_CASES,
], cwd=REPO_ROOT)
case_files = sorted(SMOKE_CASES.glob("*.png"))
assert len(case_files) >= 12
for path in case_files[:12]:
    display(DisplayImage(filename=str(path)))
'''
    ),
    code(
        '''#@title 2.3 CỔNG THỦ CÔNG — chỉ đổi sau khi đã xem 12 ảnh
SMOKE_APPROVED = False  # đổi thành True sau khi map hữu hạn, không hằng và bám cấu trúc mặt
assert SMOKE_APPROVED, "Dừng tại đây và gửi 12 smoke cases cho nhóm review"
print("✓ Official CDCN smoke gate approved")
'''
    ),
    markdown("## 3. Full run và lựa chọn hoàn toàn bằng validation\n"),
    code(
        '''#@title 3.1 Chạy hoặc tái sử dụng official-CDCN full 30 epoch
OFFICIAL_E1 = latest_complete("CASIA_E1_CDCN_OFFICIAL_seed42_*")
if OFFICIAL_E1 is None:
    run([sys.executable, "scripts/run_experiment.py", "configs/casia_e1_cdcn_official.yaml"], cwd=REPO_ROOT)
    OFFICIAL_E1 = latest_complete("CASIA_E1_CDCN_OFFICIAL_seed42_*")
assert OFFICIAL_E1 is not None
print("Official E1:", OFFICIAL_E1)
'''
    ),
    code(
        '''#@title 3.2 Kiểm tra curve và validation metrics (chưa mở test)
import matplotlib.pyplot as plt
log = pd.read_csv(OFFICIAL_E1 / "train_log.csv")
metrics_val = json.loads((OFFICIAL_E1 / "metrics.json").read_text())
threshold_record = json.loads((OFFICIAL_E1 / "threshold.json").read_text())
best_row = log.loc[log.val_loss.idxmin()]
tail_slope = float(np.polyfit(log.epoch.tail(min(5, len(log))), log.val_loss.tail(min(5, len(log))), 1)[0])
display(log.tail(10))
display(pd.DataFrame([metrics_val], index=["official E1 validation"]))
print("Best epoch:", int(best_row.epoch), "best val_loss:", float(best_row.val_loss))
print("Last-5 validation slope:", tail_slope)
print("Threshold record:", threshold_record)

plt.figure(figsize=(8, 4.5))
plt.plot(log.epoch, log.train_loss, label="train")
plt.plot(log.epoch, log.val_loss, label="validation")
plt.scatter([best_row.epoch], [best_row.val_loss], color="red", label=f"best epoch {int(best_row.epoch)}")
plt.xlabel("Epoch"); plt.ylabel("Official CDCN loss"); plt.grid(alpha=.25); plt.legend(); plt.show()
'''
    ),
    code(
        '''#@title 3.3 Xuất 12 validation depth cases
OFFICIAL_CASES = REPORTS_DIR / f"{OFFICIAL_E1.name}-depth-cases"
run([
    sys.executable, "scripts/visualize_depth_cases.py",
    "--run-dir", OFFICIAL_E1,
    "--split", "val", "--count", "12",
    "--output-dir", OFFICIAL_CASES,
], cwd=REPO_ROOT)
case_files = sorted(OFFICIAL_CASES.glob("*.png"))
assert len(case_files) >= 12
for path in case_files[:12]:
    display(DisplayImage(filename=str(path)))
'''
    ),
    code(
        '''#@title 3.4 CỔNG ĐÓNG BĂNG VALIDATION
FREEZE_AT_30 = False  # chỉ True nếu nhóm quyết định giữ run 30 epoch dựa trên validation
assert FREEZE_AT_30, (
    "Nếu best epoch=30 và val_loss còn giảm rõ, chưa mở test; đăng ký extension config mới. "
    "Nếu curve đã phẳng/dao động và cases hợp lý, đổi FREEZE_AT_30=True."
)
assert threshold_record.get("source") == "validation"
print("✓ Config, checkpoint và validation threshold đã khóa")
'''
    ),
    markdown("## 4. Locked test — chạy đúng một lần sau khi khóa\n"),
    code(
        '''#@title 4.1 MỞ LOCKED TEST ĐÚNG MỘT LẦN
RUN_LOCKED_TEST = False  # đổi thành True duy nhất sau cell 3.4
assert RUN_LOCKED_TEST, "Locked test vẫn đóng"
if (OFFICIAL_E1 / "test_metrics.json").is_file():
    print("Tái sử dụng locked-test artifact đã có; không score lại.")
else:
    run([
        sys.executable, "scripts/score_checkpoint.py",
        "--run-dir", OFFICIAL_E1, "--split", "test",
    ], cwd=REPO_ROOT)
test_metrics = json.loads((OFFICIAL_E1 / "test_metrics.json").read_text())
display(pd.DataFrame([test_metrics], index=["official E1 locked test"]))
'''
    ),
    code(
        '''#@title 4.2 Error analysis theo attack type và quality
scores = pd.read_csv(OFFICIAL_E1 / "test_scores.csv").reset_index(drop=True)
source = pd.read_csv(MANIFEST, dtype={"sample_id": str})
metadata = source[source.split == "test"][["video_id", "label", "subject_id", "attack_type", "quality"]].drop_duplicates()
analysis = scores.merge(metadata, on=["video_id", "label"], how="left", validate="one_to_one")
threshold = float(test_metrics["threshold"])
analysis["prediction"] = (analysis.score >= threshold).astype(int)
analysis["correct"] = analysis.prediction == analysis.label
summary = analysis.groupby(["label", "attack_type", "quality"], dropna=False).agg(
    videos=("video_id", "size"), errors=("correct", lambda value: int((~value).sum())),
    mean_score=("score", "mean"), min_score=("score", "min"), max_score=("score", "max"),
)
display(summary)
display(analysis[(analysis.label == 1) & ~analysis.correct].sort_values("score").head(20))
display(analysis[(analysis.label == 0) & ~analysis.correct].sort_values("score", ascending=False).head(20))
analysis.to_csv(REPORTS_DIR / f"{OFFICIAL_E1.name}-error-analysis.csv", index=False)
'''
    ),
    code(
        '''#@title 4.3 So sánh E0, E1-Lite pilot và official E1
E0_RUN = Path("/content/drive/MyDrive/face-pad/runs/CASIA_E0_BCE_5E_seed42_20260920T082941Z")
PILOT_RUN = Path("/content/drive/MyDrive/face-pad/runs/CASIA_E1_CDCN_seed42_20260921T024300Z")
rows = {"E0_MobileNetV3": json.loads((E0_RUN / "test_metrics.json").read_text())}
if (PILOT_RUN / "test_metrics.json").is_file():
    rows["E1_Lite_Pilot"] = json.loads((PILOT_RUN / "test_metrics.json").read_text())
rows["E1_Official_CDCN"] = test_metrics
comparison = pd.DataFrame(rows).T[["threshold", "apcer", "bpcer", "acer", "eer", "auc"]]
comparison["acer_delta_vs_E0"] = comparison.acer - comparison.loc["E0_MobileNetV3", "acer"]
display(comparison.style.format({"threshold":"{:.8f}", "apcer":"{:.4%}", "bpcer":"{:.4%}", "acer":"{:.4%}", "eer":"{:.4%}", "auc":"{:.6f}", "acer_delta_vs_E0":"{:+.4%}"}))
COMPARISON = REPORTS_DIR / f"E0-vs-{OFFICIAL_E1.name}.csv"
comparison.to_csv(COMPARISON)
print("Saved:", COMPARISON)
'''
    ),
    code(
        '''#@title 4.4 Kiểm tra artifact đóng Lượt 3
required = [
    "config.yaml", "environment.txt", "manifest_checksum.json", "model_provenance.json",
    "depth_input_snapshot.json", "train_log.csv", "best.ckpt", "val_frame_scores.csv",
    "val_scores.csv", "threshold.json", "metrics.json", "test_frame_scores.csv",
    "test_scores.csv", "test_metrics.json",
]
artifact_table = pd.DataFrame([{"artifact": name, "exists": (OFFICIAL_E1 / name).is_file(), "path": str(OFFICIAL_E1 / name)} for name in required])
display(artifact_table)
assert artifact_table.exists.all()
assert DEPTH_QA.is_file() and OFFICIAL_CASES.is_dir() and COMPARISON.is_file()
print("✓ Official-CDCN E1 correction hoàn tất")
print("Run:", OFFICIAL_E1)
print("Cases:", OFFICIAL_CASES)
print("Comparison:", COMPARISON)
'''
    ),
    markdown(
        """## Hoàn tất

Khi cell 4.4 pass, gửi lại các output sau để đồng bộ tài liệu báo cáo:

1. bảng validation và best epoch ở cell 3.2;
2. bảng locked-test ở cell 4.1;
3. bảng error analysis ở cell 4.2;
4. bảng so sánh ở cell 4.3;
5. đường dẫn run chính thức in ở cell 4.4.

Không đưa notebook đã chạy có ảnh khuôn mặt, checkpoint, dataset hoặc pseudo-depth lên GitHub.
"""
    ),
]

notebook = {
    "cells": cells,
    "metadata": {
        "accelerator": "GPU",
        "colab": {"provenance": [], "toc_visible": True},
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.x"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

destination = Path(__file__).resolve().parents[1] / "notebooks" / "Face_PAD_Official_CDCN_E1_Rerun.ipynb"
destination.write_text(json.dumps(notebook, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
print(destination)
