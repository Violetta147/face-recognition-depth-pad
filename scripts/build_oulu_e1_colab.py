"""Build the standalone Colab notebook for OULU Protocol 1 E1."""
from build_oulu_colab import ROOT, SOURCES, build_notebook
from build_oulu_depth_full_colab import BUNDLE_SETUP

CELLS = [
    ("markdown", """# OULU-NPU Protocol 1 · E1 CDCN
Chọn runtime **A100 GPU**. Chạy cell 1–3 để khôi phục dữ liệu và đo batch 8/16. Cell 4 huấn luyện E1 seed 43 trong 5 epoch với batch được chọn. Checkpoint và ngưỡng dùng Dev. Checkpoint tốt nhất sẽ làm điểm khởi tạo cho đối chứng E1–E3."""),
    ("code", '''#@title 1. Mount Drive và kiểm tra GPU
from pathlib import Path
from google.colab import drive
import torch

drive.mount("/content/drive")
assert torch.cuda.is_available(), "Chọn GPU A100 rồi kết nối lại"
print(torch.cuda.get_device_name(), torch.cuda.get_device_properties(0).total_memory / 2**30, "GiB")
assert "A100" in torch.cuda.get_device_name() and torch.cuda.is_bf16_supported()
BASE = Path("/content/drive/MyDrive/face-pad/oulu-fast-p1")
RGB = BASE / "prepared-cache"
DEPTH = BASE / "depth-full/p1-v1"
RESULTS = BASE / "cdcn-e1-p1"
RESULTS.mkdir(parents=True, exist_ok=True)
WORK = Path("/content/deepface-pad-oulu-depth")
ROOT = WORK / "full-p1-v1"
'''),
    ("code", BUNDLE_SETUP.split("from deepface_pad.oulu_depth_smoke")[0].replace(
        "2. Nạp code và chuẩn bị 32 ảnh có kiểm hash", "2. Khôi phục RGB và pseudo-depth từ Drive") + '''
import json
from deepface_pad.colab_cache import copy_progress, file_hash, restore_cache
from deepface_pad.oulu_depth_full import restore_rgb
from deepface_pad.oulu_fast import checked_manifest
from deepface_pad.progress import Progress

DEPTH_SHA = "fda2b58e871258906ce7c006e00880fb7d22dcf80aa80480c1992f8724ebc935"
MANIFEST = restore_rgb(RGB, WORK, ROOT)
archive = copy_progress(DEPTH / "depth-final.zip", WORK / "depth-final.zip", "Fetch final pseudo-depth snapshot")
with Progress("Verify final depth ZIP"):
    if file_hash(archive) != DEPTH_SHA:
        raise ValueError("Final depth ZIP differs from the verified Colab artifact")
summary = json.loads((DEPTH / "depth_summary.json").read_text(encoding="utf-8"))
identity = summary["identity"]
if (summary["counts"] != {"rows": 16800, "bona_fide": 3360, "attack": 13440}
        or not summary["audit"]["valid"] or identity["data_root"] != str(ROOT)
        or identity["rgb_manifest_sha256"] != file_hash(MANIFEST)):
    raise ValueError("Depth snapshot does not bind the current Train/Dev manifest")
restore_cache(ROOT, archive, identity)
if (ROOT / "depth_summary.json").read_bytes() != (DEPTH / "depth_summary.json").read_bytes():
    raise ValueError("Standalone summary differs from the frozen ZIP")
for split in ("train", "val"):
    checked_manifest(ROOT / f"p1/{split}.csv", ROOT, split)
source_zip = RESULTS / f"source-{BUNDLE_SHA256}.tar.gz"
with source_zip.open("wb") as saved:
    saved.write(bundle)
print("E1_DATA_READY", summary["counts"], "| source", BUNDLE_SHA256, flush=True)
'''),
    ("code", '''#@title 3. Đo tốc độ E1 ở batch 8 và 16
from deepface_pad.oulu_e1 import e1_config, probe

PROBE_PATH = RESULTS / f"probe-{time.time_ns()}.json"
measurements = []
for batch in (8, 16):
    try:
        row = probe(e1_config(ROOT, RESULTS / "runs", batch))
    except torch.cuda.OutOfMemoryError:
        row = {"batch_size": batch, "status": "out_of_memory"}
    torch.cuda.empty_cache()
    measurements.append(row)
    print(row, flush=True)

valid = [row for row in measurements if "frames_per_second" in row]
assert valid, "Both candidates ran out of GPU memory"
selected = max(valid, key=lambda row: row["frames_per_second"])
BATCH = selected["batch_size"]
PROBE_PATH.write_text(json.dumps({"measurements": measurements, "selected": selected}, indent=2))
print("E1_BATCH_READY", BATCH, "|", PROBE_PATH, flush=True)
'''),
    ("code", '''#@title 4. Train E1 seed 43 và khóa checkpoint từ Dev
import yaml
from deepface_pad.progress import run_logged

run_name = f"e1-{time.time_ns()}"
config = e1_config(ROOT, RESULTS / "runs", BATCH)
config_path = RESULTS / f"{run_name}.yaml"
config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
log = RESULTS / f"{run_name}.log"
env = {**os.environ, "PYTHONPATH": str(WORK / "src"), "PYTHONUNBUFFERED": "1"}
print("Optimizer updates per epoch:", 9600 // BATCH, "| epochs:", config["training"]["epochs"])
entrypoint = "import sys; from deepface_pad.train import run; print('RUN_DIR=' + str(run(sys.argv[1])))"
run_logged([sys.executable, "-u", "-c", entrypoint, config_path], label="E1 Train/Dev", log=log, env=env)
with log.open(encoding="utf-8") as file:
    run_dir = Path(next(line.strip().split("=", 1)[1] for line in file if line.startswith("RUN_DIR=")))
artifacts = ("config.yaml", "best.ckpt", "threshold.json", "metrics.json", "train_log.csv",
             "checkpoint_selection.json", "runtime.json", "depth_input_snapshot.json")
lock = {
    "protocol": 1,
    "source_bundle_sha256": BUNDLE_SHA256,
    "depth_zip_sha256": DEPTH_SHA,
    "probe_sha256": file_hash(PROBE_PATH),
    "sha256": {name: file_hash(run_dir / name) for name in artifacts},
}
(run_dir / "e1_dev_lock.json").write_text(json.dumps(lock, indent=2))
print((run_dir / "metrics.json").read_text())
print("E1_DEV_READY", run_dir, flush=True)
'''),
]

if __name__ == "__main__":
    build_notebook(CELLS, "Face_PAD_OULU_NPU_E1_CDCN.ipynb",
                   [*SOURCES, "oulu_depth_smoke", "oulu_depth_full", "oulu_e1"], gpu=True)
