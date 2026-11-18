"""Build the standalone Colab notebook for the frozen OULU-NPU P1 Test run."""
from build_cdcn_prnet_full_colab import LOAD_CODE
from build_cdcn_prnet_train_colab import include_setup
from build_oulu_colab import ROOT, build_notebook
from cdcn_prnet_locked_test import RUN_NAME


CELLS = [
    ("markdown", """# CDCN và PRNet · Chấm Test OULU-NPU Protocol 1

1. Mở notebook trên Colab và chạy cell 1–3 trên **CPU**, ưu tiên RAM cao
   nếu Colab cấp được. Cell 3 xác minh
   checkpoint 100 epoch và ngưỡng Dev, rồi chuẩn bị 600 video Test với
   MTCNN và PRNet, 8 khung mỗi video. Nó tự chọn tối đa bốn tiến trình
   theo vCPU và RAM thực tế. Nó khôi phục các ZIP cũ rồi lưu từng video
   mới lên Drive. Dừng cell 3 của notebook cũ trước khi chạy bản này.
2. Khi thấy `TEST_DATA_READY`, chuyển sang GPU rồi chạy lại cell 1–3 để
   khôi phục cache trong runtime mới. Cell 4 đọc checkpoint đã khóa và
   chấm Test. Notebook in đường dẫn kết quả sau `CDCN_LOCKED_TEST_READY`.

Chỉ số dùng ngưỡng từ Dev và gộp ảnh in cùng video phát lại khi tính APCER.
Thư mục kết quả chứa JSON, điểm từng video, thông tin khóa và log."""),
    ("code", f"""#@title 1. Kết nối Drive và định vị lượt 100 epoch
from pathlib import Path
import os
import shutil
import sys
import time
import torch
from google.colab import drive

REMOUNT_DRIVE = False
drive.mount("/content/drive", force_remount=REMOUNT_DRIVE)
DATA = Path("/content/drive/MyDrive/face-pad/datasets/OULU-NPU")
BASE = Path("/content/drive/MyDrive/face-pad/cdcn-prnet-train-pilot-p1")
TRAIN_RUN = BASE / "full-runs" / "1794972293512067663" / "{RUN_NAME}"
EVAL_DIR = BASE / "locked-test-p1" / TRAIN_RUN.name
RUN = EVAL_DIR / str(time.time_ns())
WORK = Path("/content/cdcn-prnet-locked-test")
RESULT = RUN / "test"

def require_pending():
    saved = next(EVAL_DIR.glob("*/test/test_metrics.json"), None)
    if saved is not None:
        raise FileExistsError(f"Đã có kết quả Test tại {{saved}}")

require_pending()
if not TRAIN_RUN.is_dir():
    raise FileNotFoundError(TRAIN_RUN)
RUN.mkdir(parents=True)
print("Thư mục kết quả:", RUN)
print("Runtime:", torch.cuda.get_device_name() if torch.cuda.is_available() else "CPU")"""),
    ("code", LOAD_CODE.replace(
        "run_logged(args, label=label, log=log,",
        'run_logged(args, label=label, log=log, separate_process_group=(label == "prepare-locked-test"),'
    )),
    ("code", "#@title 3. Chuẩn bị hoặc khôi phục 600 video Test\n" + include_setup() + """

import json
from deepface_pad.colab_cache import SPLIT_ARCHIVES, copy_progress, file_hash

test_ready = False
require_pending()
package = WORK / "scripts"
sys.path.insert(0, str(package))
from cdcn_prnet_locked_test import verify_run

protocol = DATA / "Protocols.tar"
with Progress("Verify frozen model and Dev threshold"):
    locked = verify_run(TRAIN_RUN, protocol)
RESULT.mkdir(parents=True, exist_ok=True)
(RESULT / "test_lock.json").write_text(json.dumps(locked, indent=2), encoding="utf-8")
print("TEST_LOCKED", locked["epoch"], "| ngưỡng Dev:", locked["threshold_from_dev"], flush=True)

name, expected_bytes = SPLIT_ARCHIVES["test"]
source = DATA / name
if source.stat().st_size != expected_bytes:
    raise ValueError(f"Kiểm tra dung lượng Test TAR: {source}")
with source.open("rb") as stream:
    prefix_hash = hashlib.sha256(stream.read(65536)).hexdigest()

def test_cache_worker_hashes(workers):
    if (workers["cdcn_prnet_smoke.py"] == "71818e0945dc8bb715268abfb86f1b7f1a8be3342216f0eea72a4c4e7af921a8"
            and workers["cdcn_prnet_expanded.py"] in {
                "655fcf8ff5679dd0947cb6249ac4e9c8160dd7980fce758628c45a4a018c78c4",
                "3e9c63b08c0e0ca52908f0ac1b8b785e566494f0503df1386cf0e57d7aa635a2",
            }):
        return workers | {
            "cdcn_prnet_expanded.py": "6eb2a41eb6aa5b8cbc35b94677b8c940a27f56acea6ffd7a3db2a910a5fa4562",
        }
    return workers

def automatic_workers(cpus, memory_bytes):
    return min(4, max(1, cpus // 2), max(1, memory_bytes // (6 * 2**30)))

PREP_WORKERS = 0  # 0 tự chọn, 1 tuần tự, hoặc chọn cụ thể 2–4
START_FRESH = False  # True dùng cache riêng để dựng lại Test, giữ nguyên cache cũ
cpus = len(os.sched_getaffinity(0))
quota_path = Path("/sys/fs/cgroup/cpu.max")
if quota_path.is_file():
    quota, period = quota_path.read_text().split()
    if quota != "max":
        cpus = min(cpus, max(1, int(quota) // int(period)))
memory = next(int(line.split()[1]) * 1024 for line in Path("/proc/meminfo").read_text().splitlines()
              if line.startswith("MemAvailable:"))
memory_limit = Path("/sys/fs/cgroup/memory.max")
if memory_limit.is_file():
    limit = memory_limit.read_text().strip()
    if limit != "max":
        used = int(memory_limit.with_name("memory.current").read_text())
        memory = min(memory, max(0, int(limit) - used))
workers = min(PREP_WORKERS, cpus) if PREP_WORKERS else automatic_workers(cpus, memory)
print(f"CPU {cpus} vCPU | RAM còn {memory / 2**30:.1f} GiB | chọn {workers} tiến trình", flush=True)

worker_hashes = {script: hashlib.sha256((package / script).read_text(encoding="utf-8").encode()).hexdigest()
                 for script in ("cdcn_prnet_smoke.py", "cdcn_prnet_expanded.py")}
profile = "p1-test8-mtcnn-prnet-fresh-v1" if START_FRESH else "p1-test8-mtcnn-prnet"
config = {"protocol": locked["protocol_sha256"], "profile": profile,
          "archive": {"name": name, "bytes": expected_bytes, "prefix_sha256": prefix_hash},
          "workers": test_cache_worker_hashes(worker_hashes)}
key = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()[:20]
cache = BASE / "test-cache" / key
assets = WORK / f"assets-{key}"
run_config = config | {"requested_prep_workers": workers, "available_vcpus": cpus,
                       "available_memory_bytes": memory, "source_worker_hashes": worker_hashes}
(RUN / "cache-config.json").write_text(json.dumps(run_config, indent=2), encoding="utf-8")

REPAIR_CACHE = False  # đặt True nếu đủ 600 ZIP nhưng worker báo cache hỏng
zip_count = len(list((cache / "Test").glob("*.zip")))
print("TEST_CACHE", cache, "|", zip_count, "/ 600 ZIP", flush=True)
complete = zip_count == 600 and not REPAIR_CACHE
stage = []
if complete:
    python = sys.executable
else:
    prepare_prnet_environment()
    run("install-prep-io", sys.executable, "-m", "uv", "pip", "install", "--python", PY, "pandas==2.2.3")
    python = PY
    if shutil.disk_usage(WORK).free > expected_bytes + 12 * 2**30:
        stage = ["--stage-dir", WORK / "archives"]
    else:
        print("Đọc Test TAR trực tiếp từ Drive vì ổ runtime còn ít dung lượng.", flush=True)

run("prepare-locked-test", python, "-u", package / "cdcn_prnet_expanded.py",
    "--data", DATA, "--output", assets, "--cache", cache, "--prnet", WORK / "PRNet",
    "--renderer", WORK / "PRNet-Depth-Generation", "--full", "--splits", "Test", "--workers", workers,
    *stage, *(["--restore-only"] if complete else []))
manifest = assets / "smoke_summary.json"
copy_progress(manifest, RUN / "preparation.json", "Save Test preparation manifest")
if file_hash(manifest) != file_hash(RUN / "preparation.json"):
    raise OSError("Manifest Test trên Drive không khớp bản runtime")
test_ready = True
print("TEST_DATA_READY 600 videos | 4800 frames", flush=True)"""),
    ("code", """#@title 4. Chấm Test với checkpoint và ngưỡng đã khóa
if not globals().get("test_ready"):
    raise RuntimeError("Chạy cell 1–3 đến TEST_DATA_READY.")
if not torch.cuda.is_available():
    raise RuntimeError("Chuyển sang runtime GPU rồi chạy lại cell 1–4.")
require_pending()
run("score-locked-test", sys.executable, "-u", package / "cdcn_prnet_locked_test.py",
    "--run", TRAIN_RUN, "--assets", assets, "--protocol", protocol,
    "--work", WORK / "scoring" / RUN.name, "--output", RESULT, "--device", "cuda")"""),
]


if __name__ == "__main__":
    build_notebook(
        CELLS, "Face_PAD_OULU_NPU_CDCN_PRNet_Locked_Test.ipynb",
        ["__init__", "progress", "losses", "colab_cache", "oulu_npu", "data", "webcam",
         "models/__init__", "models/cdcn_official", "models/cdcn_depth_head",
         "models/depth_head", "models/mobilenet_baseline"],
        {f"scripts/{name}.py": ROOT / f"scripts/{name}.py"
         for name in ("cdcn_prnet_smoke", "cdcn_prnet_train_pilot", "cdcn_prnet_expanded",
                      "audit_cdc_n_p1_scores", "cdcn_prnet_locked_test")},
    )
