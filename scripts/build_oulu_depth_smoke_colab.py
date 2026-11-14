"""Build the standalone Colab notebook for the OULU Protocol 1 depth smoke."""
from build_oulu_colab import ROOT, build_notebook

SOURCES = ["__init__", "colab_cache", "data", "depth_jobs", "depth_qa", "oulu_depth_smoke", "progress"]

CELLS = [
    ("markdown", """# OULU-NPU Protocol 1 · Thử tạo bản đồ giả độ sâu
Chọn **CPU** trong Colab. Chạy cell 1–4 rồi kiểm ảnh ở cell cuối. Notebook đọc 32 ảnh trong hai ZIP RGB đã lưu, gồm 24 ảnh thật và 8 ảnh tấn công. 3DDFA V2 dựng map cho ảnh thật trên CPU qua ONNX. Ảnh tấn công có target bằng 0. Lượt thử dùng Train và Dev."""),
    ("code", '''#@title 1. Mount Drive và chọn thư mục kết quả riêng
from pathlib import Path
from google.colab import drive
drive.mount("/content/drive")
BASE = Path("/content/drive/MyDrive/face-pad/oulu-fast-p1")
RGB = BASE / "prepared-cache"
RESULTS = BASE / "depth-smoke" / "p1-32-v1"
WORK = Path("/content/deepface-pad-oulu-depth")
ROOT = WORK / "p1-32-v1"
RESULTS.mkdir(parents=True, exist_ok=True)
assert RGB.is_dir(), f"Missing RGB cache directory: {RGB}"
'''),
    ("code", '''#@title 2. Nạp code và chuẩn bị 32 ảnh có kiểm hash
import base64
import hashlib
import io
import os
import sys
import tarfile
import time

bundle = base64.b64decode(BUNDLE)
assert hashlib.sha256(bundle).hexdigest() == BUNDLE_SHA256
with tarfile.open(fileobj=io.BytesIO(bundle), mode="r:gz") as archive:
    for entry in archive:
        path = (WORK / entry.name).resolve()
        assert entry.isfile() and path.is_relative_to(WORK)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(archive.extractfile(entry).read())
sys.path.insert(0, str(WORK / "src"))

from deepface_pad.oulu_depth_smoke import prepare_smoke, verify_smoke
from deepface_pad.progress import run_logged
from deepface_pad.colab_cache import copy_progress, depth_identity, save_cache
from shutil import copy2

ENV = {**os.environ, "PYTHONPATH": str(WORK / "src"), "PYTHONUNBUFFERED": "1",
       "OMP_NUM_THREADS": "2", "MKL_NUM_THREADS": "2", "CUDA_VISIBLE_DEVICES": ""}
def run(label, *args, cwd=None):
    run_logged(args, label=label, log=RESULTS / f"{label}-{time.time_ns()}.log", cwd=cwd, env=ENV)

MANIFEST, counts = prepare_smoke(RGB, ROOT)
copy2(MANIFEST, RESULTS / "rgb_smoke.csv")
print("RGB_SMOKE_READY", counts, "| source", BUNDLE_SHA256, flush=True)
'''),
    ("code", '''#@title 3. Cài ONNX và build renderer từ 3DDFA V2
import subprocess
THREE_DDFA = WORK / "3DDFA_V2"
COMMIT = "1b6c67601abffc1e9f248b291708aef0e43b55ae"
if not THREE_DDFA.exists():
    run("clone-3ddfa", "git", "clone", "https://github.com/cleardusk/3DDFA_V2.git", THREE_DDFA)
run("checkout-3ddfa", "git", "checkout", "--detach", COMMIT, cwd=THREE_DDFA)
assert subprocess.check_output(["git", "-C", str(THREE_DDFA), "rev-parse", "HEAD"], text=True).strip() == COMMIT
run("install-onnx", sys.executable, "-m", "pip", "install", "onnx", "onnxruntime", "Cython", "setuptools")
run("build-sim3dr", sys.executable, "setup.py", "build_ext", "--inplace", cwd=THREE_DDFA / "Sim3DR")
print("3DDFA_SETUP_READY", COMMIT, flush=True)
'''),
    ("code", '''#@title 4. Dựng map, lưu log và kiểm tra đủ 32 target
import json
from importlib.metadata import version
DEPTH = ROOT / "depth"
LEDGER = DEPTH / "depth_status.csv"
WORKER_META = DEPTH / "depth_status.csv.worker.json"
CONFIG = THREE_DDFA / "configs/mb1_120x120.yml"
ASSETS = [CONFIG, *(THREE_DDFA / path for path in (
    "configs/bfm_noneck_v3.pkl", "configs/tri.pkl", "configs/param_mean_std_62d_120x120.pkl",
    "weights/mb1_120x120.pth", "FaceBoxes/weights/FaceBoxesProd.pth", "configs/bfm_noneck_v3.onnx",
    "weights/mb1_120x120.onnx", "FaceBoxes/weights/FaceBoxesProd.onnx",
))]
started = time.monotonic()
try:
    run("3ddfa-smoke", sys.executable, WORK / "scripts/run_3ddfa_worker.py",
        "--3ddfa-root", THREE_DDFA, "--config", CONFIG, "--pending", DEPTH / "3ddfa_pending.csv",
        "--ledger", LEDGER, "--onnx", "--mode", "cpu", "--failure-report", DEPTH / "failures.csv")
finally:
    for path in (LEDGER, WORKER_META, DEPTH / "failures.csv"):
        if path.is_file():
            copy2(path, RESULTS / path.name)
report = verify_smoke(MANIFEST, ROOT)
assert report["counts"] == {"rows": 32, "bona_fide": 24, "attack": 8}
metadata = depth_identity(ROOT, MANIFEST, WORKER_META, ASSETS)
metadata.update(source_bundle=BUNDLE_SHA256, data_root=str(ROOT),
                versions={name: version(name) for name in ("torch", "numpy", "onnx", "onnxruntime", "Cython")})
report["worker_seconds"] = time.monotonic() - started
report["environment"] = metadata
report_path = RESULTS / "smoke_summary.json"
report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

# Preserve machine-readable evidence without duplicating any RGB images.
archive = WORK / "depth-smoke.zip"
paths = [MANIFEST, *ROOT.glob("rgb_smoke_with_depth.csv*"),
         *(path for path in DEPTH.iterdir() if path.suffix in {".npy", ".csv", ".json"})]
save_cache(ROOT, archive, paths, metadata)
copy_progress(archive, RESULTS / "depth-smoke.zip", "Save depth smoke to Drive")
print("DEPTH_SMOKE_PASS", report["counts"], "|", report_path, flush=True)
'''),
    ("code", '''#@title 5. Duyệt trực quan RGB và map
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
rows = pd.read_csv(ROOT / "rgb_smoke_with_depth.csv")
examples = rows.groupby(["split", "label"], sort=True).head(1)
fig, axes = plt.subplots(len(examples), 2, figsize=(6, 10), squeeze=False)
for row, (rgb_axis, depth_axis) in zip(examples.itertuples(index=False), axes):
    with Image.open(ROOT / row.image_path) as image:
        rgb_axis.imshow(image)
    rgb_axis.set_title(f"{row.split} | {row.attack_type}")
    depth_axis.imshow(np.load(ROOT / row.depth_path, allow_pickle=False), cmap="viridis", vmin=0, vmax=1)
    depth_axis.set_title(row.sample_id)
    rgb_axis.axis("off")
    depth_axis.axis("off")
plt.tight_layout()
plt.show()
'''),
]

if __name__ == "__main__":
    build_notebook(CELLS, "Face_PAD_OULU_NPU_Depth_Smoke.ipynb", SOURCES,
                   {"scripts/run_3ddfa_worker.py": ROOT / "scripts/run_3ddfa_worker.py"})
