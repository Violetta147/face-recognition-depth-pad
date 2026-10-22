"""Build a clean, manually gated Round 6 notebook without running its cells."""
from __future__ import annotations

import json
from pathlib import Path

CPU_TESTS = ["test_round6.py", "test_round6_notebook.py", "test_preflight.py",
             "test_training_stages.py", "test_official_depth_head.py", "test_metrics.py",
             "test_manifest.py", "test_depth_jobs.py", "test_depth_qa.py"]


def cell(kind, source):
    result = {"cell_type": kind, "metadata": {}, "source": source.splitlines(keepends=True)}
    if kind == "code":
        result.update(execution_count=None, outputs=[])
    return result


def build(root=None):
    cells = [cell("markdown", """# Lượt 6 — ba cặp E1/E3, seed 43/44/45

Đọc `reports/ROUND_6_CASIA_RUNBOOK.md`. Chọn **A100 GPU** và chạy từng cell.
**Chỉ chạy 0.1–1.4, dừng tại PREFLIGHT PASS rồi gửi output để kiểm tra.**
Không Run all. Train và test mặc định đóng. Ngân sách 2–3 giờ là ước lượng,
chưa đo. Không trộn seed 42 vào đợt mới. CASIA đã quan sát là development evidence.
E3 giữ nguyên lựa chọn từ validation Lượt 5, kể cả khi kết quả mới âm tính.
"""), cell("code", '''#@title 0.1 Mount Drive và đường dẫn
from google.colab import drive, files
drive.mount("/content/drive")
import hashlib, importlib, json, os, shutil, subprocess, sys, tarfile, zipfile
from pathlib import Path
REPO_ROOT = Path("/content/round6-source/DeepFace-PAD")
DRIVE_ROOT = Path("/content/drive/MyDrive/face-pad")
DATA_ROOT = Path("/content/datasets/casia-fasd")
RUNS_DIR = DRIVE_ROOT / "runs"
MANIFEST = REPO_ROOT / "data/manifests/casia_fasd_debug.csv"
DEPTH_MANIFEST = REPO_ROOT / "data/manifests/casia_fasd_debug_with_depth.csv"
DEPTH_ROOT = DATA_ROOT / "depth"
DEPTH_LEDGER = DEPTH_ROOT / "depth_status.csv"
def run(command, cwd=REPO_ROOT, env=None):
    subprocess.run([str(x) for x in command], cwd=cwd, env=env, check=True)
def checksum(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()
def safe_zip(path, target):
    target = Path(target).resolve()
    with zipfile.ZipFile(path) as archive:
        for entry in archive.infolist():
            destination = (target / entry.filename).resolve()
            assert destination.is_relative_to(target), "ZIP path outside destination"
            assert (entry.external_attr >> 16) & 0o170000 != 0o120000, "ZIP symlink"
        archive.extractall(target)
'''), cell("code", '''#@title 0.2 Nạp ZIP đúng commit và cài package
archive = Path("/content/DeepFace-PAD-Round6-source.zip")
drive_archive = DRIVE_ROOT / "handoffs/round6-20261022/DeepFace-PAD-Round6-source.zip"
if not archive.is_file() and drive_archive.is_file():
    shutil.copy2(drive_archive, archive)
if not archive.is_file():
    print("Upload DeepFace-PAD-Round6-source.zip được giao cùng notebook.")
    files.upload()
assert archive.is_file(), "Thiếu source ZIP Lượt 6"
if not REPO_ROOT.exists():
    safe_zip(archive, REPO_ROOT.parent)
else:
    with zipfile.ZipFile(archive) as source_zip:
        assert source_zip.read("DeepFace-PAD/SOURCE_LOCK.json") == (REPO_ROOT / "SOURCE_LOCK.json").read_bytes(), "Source cũ khác ZIP; dừng kiểm tra"
lock = json.loads((REPO_ROOT / "SOURCE_LOCK.json").read_text())
assert all(checksum(REPO_ROOT / name) == value for name, value in lock["files"].items())
SOURCE_COMMIT = (REPO_ROOT / "SOURCE_COMMIT.txt").read_text().strip()
assert SOURCE_COMMIT == lock["commit"] and len(SOURCE_COMMIT) == 40
run([sys.executable, "-m", "pip", "install", "-q", "-e", ".[dev]"])
os.chdir(REPO_ROOT)
sys.path.insert(0, str(REPO_ROOT / "src"))
importlib.invalidate_caches()
import numpy as np
import pandas as pd
import torch
from IPython.display import display
from deepface_pad.round6 import Batch, summarize
OUTPUT_DIR = DRIVE_ROOT / "reports" / f"round6-{SOURCE_COMMIT[:12]}"
batch = Batch(REPO_ROOT, OUTPUT_DIR)
print("Source commit:", SOURCE_COMMIT, "ZIP SHA256:", checksum(archive))
'''), cell("code", '''#@title 0.3 Tests CPU, chưa train; kiểm đúng A100
cpu_env = dict(os.environ, CUDA_VISIBLE_DEVICES="")
TESTS = ''' + repr(["tests/" + name for name in CPU_TESTS]) + '''
run([sys.executable, "-m", "pytest", "-q", *TESTS], env=cpu_env)
assert torch.cuda.is_available(), "Chọn A100 GPU, không chạy train bằng CPU"
assert "A100" in torch.cuda.get_device_name(0), torch.cuda.get_device_name(0)
print("GPU:", torch.cuda.get_device_name(0), "torch:", torch.__version__, "CUDA:", torch.version.cuda)
'''), cell("code", '''#@title 1.1 Khôi phục ZIP dataset cũ trên Drive
def looks_like_casia(path):
    return (path / "train/live").is_dir() and (path / "test/spoof").is_dir()
if not looks_like_casia(DATA_ROOT):
    dataset_zip = DRIVE_ROOT / "casia-fasd.zip"
    assert dataset_zip.is_file(), "Thiếu face-pad/casia-fasd.zip; dừng, không tải bộ dữ liệu khác"
    DATA_ROOT.parent.mkdir(parents=True, exist_ok=True)
    safe_zip(dataset_zip, DATA_ROOT.parent)
    if not looks_like_casia(DATA_ROOT):
        roots = [p.parent for p in DATA_ROOT.parent.rglob("train") if looks_like_casia(p.parent)]
        assert len(roots) == 1, f"CASIA root không duy nhất: {roots}"
        shutil.copytree(roots[0], DATA_ROOT, dirs_exist_ok=True)
assert looks_like_casia(DATA_ROOT)
print("Dataset:", DATA_ROOT)
'''), cell("code", '''#@title 1.2 Manifest cùng split và sampling đã khóa
run([sys.executable, "scripts/prepare_casia_fasd.py", "--data-root", DATA_ROOT,
     "--output-dir", REPO_ROOT / "data/manifests", "--frames-per-video", "20",
     "--val-subjects", "4,9,14,19"])
from deepface_pad.round6 import SOURCE_MANIFEST, DEPTH_MANIFEST as EXPECTED_DEPTH
assert checksum(MANIFEST) == SOURCE_MANIFEST, "Manifest khác; không tự đổi split"
'''), cell("code", '''#@title 1.3 Khôi phục cache cũ; không chạy worker 3DDFA
cache_tar = DRIVE_ROOT / "depth-checkpoints/casia-fasd-depth-checkpoint.tar"
assert cache_tar.is_file(), "Thiếu TAR cache đã kiểm toán; dừng"
assert checksum(cache_tar) == "26cfa7f26d61e3a71372404008f5dc9dd696af931172850986a8642e440b3d80"
local_tar = Path("/content/casia-fasd-depth-checkpoint.tar")
if not local_tar.exists():
    shutil.copy2(cache_tar, local_tar)
assert checksum(local_tar) == checksum(cache_tar)
with tarfile.open(local_tar) as archive:
    for member in archive.getmembers():
        destination = (DATA_ROOT / member.name).resolve()
        assert destination.is_relative_to(DATA_ROOT.resolve())
        assert member.isfile() or member.isdir(), "Cache entry không phải file/directory"
        if member.isdir():
            destination.mkdir(parents=True, exist_ok=True)
        else:
            payload = archive.extractfile(member).read()
            if destination.exists():
                assert hashlib.sha256(payload).hexdigest() == checksum(destination), f"Cache cục bộ khác: {destination}"
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(payload)
worker = DRIVE_ROOT / "depth-checkpoints/casia-fasd/depth_status.csv.worker.json"
if worker.is_file() and not (DEPTH_ROOT / worker.name).exists():
    shutil.copy2(worker, DEPTH_ROOT / worker.name)
# Helper tái sử dụng live maps; chỉ khôi phục attack zero cố định/ledger.
run([sys.executable, "scripts/generate_depth.py", MANIFEST,
     "--data-root", DATA_ROOT, "--output-root", DEPTH_ROOT])
ledger = pd.read_csv(DEPTH_LEDGER, keep_default_na=False)
assert ledger.status.value_counts().to_dict() == {"complete_attack_zero":9000, "complete_bona_fide":3000}, "Cache chưa đủ; không sinh lại live depth"
run([sys.executable, "scripts/materialize_depth_manifest.py", MANIFEST,
     "--ledger", DEPTH_LEDGER, "--data-root", DATA_ROOT, "--output", DEPTH_MANIFEST])
assert checksum(DEPTH_MANIFEST) == EXPECTED_DEPTH
'''), cell("code", '''#@title 1.4 PREFLIGHT: đăng ký sáu config/source/data/environment — DỪNG
registration = batch.register(DATA_ROOT, RUNS_DIR)
identity = registration["environment"]
display(pd.DataFrame([{"key":key, "seed":cfg["seed"], "model":cfg["model"]["name"],
                      "initializer":cfg.get("round6_initializer", "random, đúng seed")}
                     for key,cfg in registration["configs"].items()]))
print("PREFLIGHT PASS", json.dumps({"source_commit":SOURCE_COMMIT,
    "gpu":identity["gpu"], "driver":identity["driver_inventory"], "torch":identity["torch"],
    "cuda":identity["cuda"], "cudnn":identity["cudnn"], "seeds":registration["seeds"],
    "depth_targets":len(registration["depth"]["artifacts"]), "epoch_budget":138,
    "registration":str(batch.registration_path)}, indent=2))
print("DỪNG: gửi output cell này và CPU tests; kiểm budget A100 trước train. Không Run all.")
'''), cell("markdown", """## 2. Train từng cặp — chỉ mở sau khi preflight đã được kiểm tra

Mỗi cặp E1 → E3 phải dùng cùng seed. Giữ partial log khi bị ngắt; không full resume.
Sau mỗi cặp, kiểm output và thời gian còn lại trước seed tiếp theo.
""")]
    for seed in (43, 44, 45):
        cells.append(cell("code", f'''#@title 2.{seed-42} Cặp seed {seed} — cổng mặc định đóng
RUN_SEED{seed} = False
pair{seed} = batch.train_pair({seed}, allow_train=RUN_SEED{seed})
for key, folder in pair{seed}.items():
    print(key, folder)
    display(pd.read_csv(folder / "train_log.csv"))
print("DỪNG: gửi run ID/log/initializer, kiểm thời gian trước cặp tiếp theo.")
'''))
    cells.extend([cell("code", '''#@title 3.1 Freeze validation đủ sáu run, chưa mở test
freeze = batch.freeze()
rows = []
for key, record in freeze["runs"].items():
    folder = Path(record["run"])
    selected = json.loads((folder / "checkpoint_selection.json").read_text())["stages"][-1]
    rows.append({"key":key, "split":"validation", "unit":"video", "run":folder.name,
                 "selected_epoch":selected["epoch"], "selection_loss":selected["selection_value"],
                 **json.loads((folder / "metrics.json").read_text())})
validation = pd.DataFrame(rows)
validation.to_csv(OUTPUT_DIR / "validation.csv", index=False)
formats = {m:"{:.4%}" for m in ("apcer","bpcer","acer","eer")}
formats.update(auc="{:.6f}", threshold="{:.8f}", selection_loss="{:.6f}")
display(validation.style.format(formats).set_caption("Validation — video; APCER/BPCER/ACER/EER %, AUC không đơn vị"))
print("DỪNG: gửi bảng validation và freeze:", batch.freeze_path)
'''), cell("code", '''#@title 4.1 Test phát triển — chỉ sau khi kiểm freeze cả sáu run
OPEN_TEST = False
test = batch.test(allow_test=OPEN_TEST)
test.to_csv(OUTPUT_DIR / "development-test.csv", index=False)
summary, paired = summarize(test)
summary.to_csv(OUTPUT_DIR / "summary-mean-sample-sd.csv")
paired.to_csv(OUTPUT_DIR / "paired-video-acer.csv")
(OUTPUT_DIR / "paired-summary.json").write_text(json.dumps(paired.attrs, indent=2))
display(test.style.format({"apcer":"{:.4%}","bpcer":"{:.4%}","acer":"{:.4%}","eer":"{:.4%}","auc":"{:.6f}"}).set_caption("CASIA development test — video"))
display(summary.style.format({(m,s):("{:.6f}" if m=="auc" else "{:.4%}") for m in ("apcer","bpcer","acer","eer","auc") for s in ("mean","std")}).set_caption("Ba seed mới — mean và sample SD, ddof=1"))
display(paired.style.format("{:.4%}").set_caption("Video ACER; delta = E3 − E1, hiển thị theo điểm phần trăm"))
print("Paired delta mean/sample SD, điểm phần trăm:", {k:100*v for k,v in paired.attrs.items()})
print("Giữ mọi kết quả, gồm delta dương. Không chọn E4 từ test; không gộp seed 42.")
print("Lưu notebook đã chạy và gửi output:", OUTPUT_DIR)
''')])
    for i, item in enumerate(cells):
        item["id"] = f"round6-{i:02d}"
    return {"cells": cells, "metadata": {"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},
        "language_info":{"name":"python"}, "colab":{"name":"Face_PAD_Round6_CASIA_E1_E3.ipynb"}},
        "nbformat":4, "nbformat_minor":5}


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    path = root / "notebooks/Face_PAD_Round6_CASIA_E1_E3.ipynb"
    path.write_text(json.dumps(build(root), ensure_ascii=False, indent=1)+"\n", encoding="utf-8")
    print(path)
