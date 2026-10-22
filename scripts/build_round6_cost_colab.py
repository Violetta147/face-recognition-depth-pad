"""Clean cost-only Colab notebook; no dependency on the finished train runtime."""
from __future__ import annotations

import json
from pathlib import Path

CPU_TESTS = ["tests/test_cost.py", "tests/test_cost_notebook.py", "tests/test_official_depth_head.py"]


def cell(kind, text):
    result={"cell_type":kind,"metadata":{},"source":text.splitlines(keepends=True)}
    if kind=="code": result.update(execution_count=None,outputs=[])
    return result


def build():
    cells=[cell("markdown",'''# Lượt 6 — đo chi phí E1/E3/E4, không train/test lại

Mở một phiên **A100 GPU**, chạy **0.1–1.1**, rồi gửi output `COST PREFLIGHT PASS`.
Cell đo mặc định đóng. Không Run all. Chỉ đọc hai ảnh validation từ ZIP dataset
đã có; không giải nén lại cả dataset, sinh depth hoặc sửa sáu run đã khóa.
Đọc `reports/ROUND_6_COST_PLAN.md`. Latency dưới đây chỉ thuộc forward batch 1,
không phải FPS webcam hoặc thời gian của toàn pipeline.
'''),cell("code",'''#@title 0.1 Mount Drive và nạp ZIP source đo chi phí
from google.colab import drive, files
drive.mount("/content/drive")
import hashlib, importlib, json, os, shutil, subprocess, sys, zipfile
from pathlib import Path
DRIVE_ROOT = Path("/content/drive/MyDrive/face-pad")
REPO_ROOT = Path("/content/round6-cost-source/DeepFace-PAD")
archive = Path("/content/DeepFace-PAD-Round6-cost-source.zip")
drive_archive = DRIVE_ROOT / "handoffs/round6-cost-20261022" / archive.name
if not archive.exists() and drive_archive.is_file():
    shutil.copy2(drive_archive, archive)
if not archive.exists():
    print("Upload DeepFace-PAD-Round6-cost-source.zip được giao cùng notebook này.")
    files.upload()
assert archive.is_file(), "Thiếu ZIP source đo chi phí"
with zipfile.ZipFile(archive) as z:
    if REPO_ROOT.exists():
        assert z.read("DeepFace-PAD/SOURCE_LOCK.json") == (REPO_ROOT / "SOURCE_LOCK.json").read_bytes(), "Thư mục source đang có khác ZIP; dừng kiểm tra"
    else:
        parent = REPO_ROOT.parent.resolve()
        for entry in z.infolist():
            assert (parent / entry.filename).resolve().is_relative_to(parent)
            assert (entry.external_attr >> 16) & 0o170000 != 0o120000
        z.extractall(parent)
lock = json.loads((REPO_ROOT / "SOURCE_LOCK.json").read_text())
assert all(hashlib.sha256((REPO_ROOT / p).read_bytes()).hexdigest()==h for p,h in lock["files"].items())
SOURCE_COMMIT = (REPO_ROOT / "SOURCE_COMMIT.txt").read_text().strip()
assert SOURCE_COMMIT == lock["commit"] and len(SOURCE_COMMIT)==40
subprocess.run([sys.executable,"-m","pip","install","-q","-e",".[dev]"],cwd=REPO_ROOT,check=True)
os.chdir(REPO_ROOT)
sys.path.insert(0,str(REPO_ROOT / "src"))
importlib.invalidate_caches()
print("Cost source:", SOURCE_COMMIT)
'''),cell("code",'''#@title 0.2 Tests CPU và GPU thực tế
CPU_TESTS = '''+repr(CPU_TESTS)+'''
subprocess.run([sys.executable,"-m","pytest","-q",*CPU_TESTS],cwd=REPO_ROOT,
    env=dict(os.environ,CUDA_VISIBLE_DEVICES="",OMP_NUM_THREADS="2",MKL_NUM_THREADS="2"),check=True)
import torch
assert torch.cuda.is_available() and "A100" in torch.cuda.get_device_name(0), "Chọn A100 GPU rồi chạy lại setup"
print("GPU:",torch.cuda.get_device_name(0),"torch:",torch.__version__,"CUDA:",torch.version.cuda)
'''),cell("code",'''#@title 1.1 COST PREFLIGHT: kiểm hash ba checkpoint, hai ảnh validation và môi trường
import pandas as pd
from IPython.display import display
from deepface_pad.cost import prepare, run_cost
BLOCK_ID = "a100-01"
OUTPUT_DIR = DRIVE_ROOT / "reports" / f"round6-cost-{SOURCE_COMMIT[:12]}" / BLOCK_ID
registration, cpu_models, cpu_inputs = prepare(REPO_ROOT, DRIVE_ROOT, OUTPUT_DIR)
display(pd.DataFrame([{"model":key,"seed":value["seed"],"params":value["params"],
    "state_bytes":value["state_bytes_including_buffers"],"checkpoint_bytes":value["checkpoint_file_bytes"]}
    for key,value in registration["models"].items()]))
print("COST PREFLIGHT PASS",json.dumps({"source_commit":SOURCE_COMMIT,
    "gpu":registration["environment"]["gpu"],"driver":registration["environment"]["driver_inventory"],
    "torch":registration["environment"]["torch"],"cuda":registration["environment"]["cuda"],
    "input_samples":[x["sample_id"] for x in registration["inputs"]],
    "orders":registration["model_orders"],"output_dir":str(OUTPUT_DIR)},indent=2))
del cpu_models, cpu_inputs
print("DỪNG: gửi output này cho Codex; chưa mở cổng đo. Giữ nguyên BLOCK_ID.")
'''),cell("code",'''#@title 2.1 Cổng đo forward — chỉ mở sau khi preflight đã được kiểm
RUN_BENCHMARK = False
results = run_cost(REPO_ROOT, DRIVE_ROOT, OUTPUT_DIR, allow_benchmark=RUN_BENCHMARK)
rows=[]
for key, stats in results["summary"]["pooled"].items():
    rows.append({"model":key,"params":results["models"][key]["params"],
        "checkpoint_bytes":results["models"][key]["checkpoint_file_bytes"],
        "samples":stats["cuda_event_forward_ms"]["n"],
        "CUDA p50 ms":stats["cuda_event_forward_ms"]["p50"],
        "CUDA p95 ms":stats["cuda_event_forward_ms"]["p95"],
        "host p50 ms":stats["synchronized_host_forward_ms"]["p50"],
        "host p95 ms":stats["synchronized_host_forward_ms"]["p95"]})
display(pd.DataFrame(rows).style.format({name:"{:.4f}" for name in
    ("CUDA p50 ms","CUDA p95 ms","host p50 ms","host p95 ms")}).set_caption(
    "Forward batch 1, float32; preprocessing/transfer/Drive I/O nằm ngoài timing"))
print("COST COMPLETE:",OUTPUT_DIR)
print("Lưu notebook đã chạy rồi gửi đường dẫn này. Không train, test hoặc đo lại để chọn số nhanh.")
''')]
    for i,c in enumerate(cells): c["id"]=f"round6-cost-{i:02d}"
    return {"cells":cells,"metadata":{"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},
        "language_info":{"name":"python"},"colab":{"name":"Face_PAD_Round6_Cost_E1_E3_E4.ipynb"}},"nbformat":4,"nbformat_minor":5}


if __name__=="__main__":
    p=Path(__file__).resolve().parents[1]/"notebooks/Face_PAD_Round6_Cost_E1_E3_E4.ipynb"
    p.write_text(json.dumps(build(),ensure_ascii=False,indent=1)+"\n",encoding="utf-8")
    print(p)
