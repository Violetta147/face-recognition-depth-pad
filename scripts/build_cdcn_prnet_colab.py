"""Build the self-contained CPU Colab notebook for the CDCN preprocessing smoke."""

from build_oulu_colab import ROOT, build_notebook
from cdcn_prnet_smoke import DEPTH_COMMIT, PRNET_COMMIT, SMOKE_PACKAGES, WEIGHT_SHA


CELLS = [
    ("markdown", """# CDCN CVPR 2020 · Kiểm tra MTCNN và PRNet trên OULU-NPU
Dùng runtime **CPU** và chạy các cell theo thứ tự. Mẫu nhỏ lấy 3 video và
9 khung ở mỗi tập Train và Dev của Protocol 1. Mỗi tập có video thật,
ảnh in và phát lại. Kết quả là ảnh scene, bbox, depth JPEG và JSON kiểm tra.
Notebook dành cho bước chuẩn bị dữ liệu trước huấn luyện."""),
    ("code", """#@title 1. Kết nối Drive và chọn thư mục OULU-NPU
from pathlib import Path
import os
import shutil
import sys
import time
from google.colab import drive

drive.mount("/content/drive")
DATA = Path("/content/drive/MyDrive/face-pad/datasets/OULU-NPU")
WORK = Path("/content/cdcn-prnet-smoke")
RUN = Path("/content/drive/MyDrive/face-pad/cdcn-prnet-smoke-p1") / str(time.time_ns())
for name, size in {"Protocols.tar": 417792, "Train_files.tar": 37753662976,
                   "Dev_files.tar": 28151992320}.items():
    source = DATA / name
    if not source.is_file() or source.stat().st_size != size:
        raise ValueError(f"Kiểm tra đường dẫn và dung lượng: {source}")
RUN.mkdir(parents=True)
print("Thư mục kết quả:", RUN)"""),
    ("code", """#@title 2. Nạp code và cài môi trường tách riêng
import base64
import hashlib
import io
import tarfile
bundle = base64.b64decode(BUNDLE)
if hashlib.sha256(bundle).hexdigest() != BUNDLE_SHA256:
    raise ValueError("Code đi kèm không khớp SHA-256")
WORK.mkdir(parents=True, exist_ok=True)
with tarfile.open(fileobj=io.BytesIO(bundle), mode="r:gz") as archive:
    for member in archive:
        dest = (WORK / member.name).resolve()
        if not member.isfile() or not dest.is_relative_to(WORK):
            raise ValueError(f"Invalid bundle member: {member.name}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(archive.extractfile(member).read())
(RUN / f"source-{BUNDLE_SHA256[:12]}.tar.gz").write_bytes(bundle)
sys.path.insert(0, str(WORK / "src"))
from deepface_pad.progress import Progress, run_logged

def run(label, *args):
    run_logged(args, label=label, log=RUN / f"{label}-{time.time_ns()}.log",
               env={**os.environ, "PYTHONPATH": str(WORK / "src"), "TF_ENABLE_ONEDNN_OPTS": "0"})

run("install-uv", sys.executable, "-m", "pip", "install", "uv")
VENV = WORK / "venv"
PY = VENV / "bin/python"
if not PY.is_file():
    run("create-venv", sys.executable, "-m", "uv", "venv", "--python", "3.12.10", VENV)
run("install-prnet", sys.executable, "-m", "uv", "pip", "install", "--python", PY,
    *PACKAGES)""".replace("PACKAGES", repr(SMOKE_PACKAGES))),
    ("code", f"""#@title 3. Tải code và trọng số PRNet công khai
PRNET = WORK / "PRNet"
RENDERER = WORK / "PRNet-Depth-Generation"
for path, repo, commit in [
    (PRNET, "https://github.com/yfeng95/PRNet.git", "{PRNET_COMMIT}"),
    (RENDERER, "https://github.com/clks-wzz/PRNet-Depth-Generation.git", "{DEPTH_COMMIT}"),
]:
    if not path.exists():
        run(f"clone-{{path.name}}", "git", "clone", repo, path)
    run(f"checkout-{{path.name}}", "git", "-C", path, "checkout", "--detach", commit)
WEIGHT = PRNET / "Data/net-data/256_256_resfcn256_weight.data-00000-of-00001"
def weight_matches(path):
    if not path.is_file():
        return False
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest() == "{WEIGHT_SHA}"

if not weight_matches(WEIGHT):
    partial = WEIGHT.with_suffix(".part")
    run("download-prnet", "curl", "-LfsS", "--retry", "2", "-o", partial,
        "https://drive.usercontent.google.com/download?id=1UoE-XuW1SDLUjZmJPkIZ1MLxvQFgmTFH&export=download&confirm=t")
    if not weight_matches(partial):
        raise ValueError("Tệp tải về không khớp SHA-256 của checkpoint PRNet")
    partial.replace(WEIGHT)
run("verify-prnet", PY, "-u", WORK / "scripts/cdcn_prnet_smoke.py",
    "--image", PRNET / "TestImages/0.jpg", "--prnet", PRNET, "--renderer", RENDERER,
    "--output", WORK / f"public-{{time.time_ns()}}")"""),
    ("code", """#@title 4. Dựng dữ liệu mẫu Train/Dev và lưu lên Drive
OUT = WORK / f"oulu-{time.time_ns()}"
WIDE_SAMPLE = False  # True để thêm phone 4/session 2, đọc sâu hơn trong TAR
run("oulu-prnet-smoke", PY, "-u", WORK / "scripts/cdcn_prnet_smoke.py",
    "--data", DATA, "--prnet", PRNET, "--renderer", RENDERER, "--output", OUT,
    *(["--wide-sample"] if WIDE_SAMPLE else []))
with Progress("Save smoke assets to Drive"):
    local_zip = Path(shutil.make_archive(str(OUT), "zip", OUT))
    temporary = RUN / (local_zip.name + ".part")
    shutil.copyfile(local_zip, temporary)
    temporary.replace(RUN / local_zip.name)
    shutil.copyfile(OUT / "smoke_summary.json", RUN / "smoke_summary.json")
print("CDCN_PRNET_SMOKE_READY", RUN)"""),
]


if __name__ == "__main__":
    build_notebook(
        CELLS,
        "Face_PAD_OULU_NPU_CDCN_PRNet_Smoke.ipynb",
        ["__init__", "progress"],
        {"scripts/cdcn_prnet_smoke.py": ROOT / "scripts/cdcn_prnet_smoke.py"},
    )
