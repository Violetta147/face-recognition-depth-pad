"""Build the full-membership OULU-NPU P1 Train/Dev notebook."""

from build_cdcn_prnet_expanded_colab import CELLS as EXPANDED
from build_cdcn_prnet_train_colab import include_setup
from build_oulu_colab import ROOT, build_notebook


MOUNT = (EXPANDED[1][1].replace("cdcn-prnet-expanded", "cdcn-prnet-full")
         .replace("expanded-runs", "full-runs")
         .replace('drive.mount("/content/drive")',
                  'REMOUNT_DRIVE = False  # đổi thành True nếu mount vừa báo Errno 107\n'
                  'drive.mount("/content/drive", force_remount=REMOUNT_DRIVE)'))

LOAD_CODE = EXPANDED[2][1].split("\ndef run(label, *args):", 1)[0] + """

# Ghi tiến trình lên ổ runtime. Chỉ chép log lên Drive sau khi lệnh kết thúc.
LOCAL_LOGS = WORK / "logs" / RUN.name

def run(label, *args):
    log = LOCAL_LOGS / f"{label}-{time.time_ns()}.log"
    try:
        run_logged(args, label=label, log=log,
                   env={**os.environ, "PYTHONPATH": str(WORK / "src"), "TF_ENABLE_ONEDNN_OPTS": "0"})
    finally:
        if log.is_file():
            try:
                shutil.copyfile(log, RUN / log.name)
            except OSError as exc:
                print(f"Chưa chép được log lên Drive: {exc} | Log cục bộ: {log}", flush=True)
"""

CELLS = [
    ("markdown", """# CDCN trên OULU-NPU · Train/Dev đầy đủ của Protocol 1
Chạy **cell 1–3 trên CPU** để chuẩn bị 1.200 video Train và 900 video Dev.
Train lấy 24 khung rải đều qua mỗi video, Dev giữ 8 khung. Cell 3 lưu
từng video đã hoàn tất lên Drive và có thể chạy lại sau khi đổi runtime.

Nếu Drive báo **Errno 107**, đặt `REMOUNT_DRIVE = True` ở cell 1 rồi chạy
lại cell 1–3. Cell 3 in `CACHE_ZIPS` trước khi chuẩn bị. Nếu đã đủ ZIP
Train, có thể đặt `SPLITS = ["Dev"]` để chuẩn bị riêng Dev. Log gốc nằm
trong `/content/cdcn-prnet-full/logs` cho đến khi runtime bị xóa.

Sau khi cell 3 báo đủ 36.000 khung, chuyển sang **A100 80 GB** và chạy
lại **cell 1–4** với cả hai tập trong `SPLITS`. Cell 4 chạy 3 epoch
từ đầu với batch 56 rồi chấm toàn bộ Dev, để đo thời gian trước khi chốt
lượt huấn luyện dài. Kết quả lưu trên Drive."""),
    ("code", MOUNT),
    ("code", LOAD_CODE),
    ("code", "#@title 3. Khôi phục hoặc chuẩn bị Train/Dev đầy đủ\nPREPARED_SPLITS = ()\n" + include_setup() + """

import json
import statistics
from deepface_pad.colab_cache import SPLIT_ARCHIVES, file_hash

# Có thể chạy một split trước rồi chạy lại cả hai. Cache theo video nằm trên Drive.
SPLITS = ["Train", "Dev"]
STAGE_TARS = True  # chép TAR thiếu vào ổ cục bộ để đọc nhanh hơn
REPAIR_CACHE = False  # đặt True nếu log báo ZIP thiếu hoặc hỏng dù đã đủ số tệp

def normalize_splits(splits):
    if isinstance(splits, str):
        splits = (splits,)
    if (not isinstance(splits, (list, tuple)) or not splits
            or any(split not in ("Train", "Dev") for split in splits)
            or len(set(splits)) != len(splits)):
        raise ValueError('Đặt SPLITS = ["Train"], ["Dev"] hoặc ["Train", "Dev"].')
    return tuple(splits)

SPLITS = normalize_splits(SPLITS)

def cache_worker_hashes(scripts):
    # This exact worker revision only changes where ZIPs are opened.
    if scripts == {
        "cdcn_prnet_smoke.py": "71818e0945dc8bb715268abfb86f1b7f1a8be3342216f0eea72a4c4e7af921a8",
        "cdcn_prnet_expanded.py": "f0794f5537278642aa3c5c795c42f0321b1feeec6295af151aa06db13b6f8134",
    }:
        return scripts | {
            "cdcn_prnet_expanded.py": "9611f0b3464a441ea1582eca0ceca61741f2d644fa1230cb892592ca0751652a",
        }
    return scripts

package = WORK / "scripts"
archives = {}
for key in ("train", "val"):
    name, size = SPLIT_ARCHIVES[key]
    path = DATA / name
    with path.open("rb") as stream:
        archives[name] = {"bytes": size, "prefix_sha256": hashlib.sha256(stream.read(65536)).hexdigest()}
protocol = file_hash(DATA / "Protocols.tar")
scripts = {name: hashlib.sha256((package / name).read_text(encoding="utf-8").encode()).hexdigest()
           for name in ("cdcn_prnet_smoke.py", "cdcn_prnet_expanded.py")}
config = {"profile": "p1-full-train24-dev8", "protocol": protocol, "archives": archives,
          "scripts": cache_worker_hashes(scripts)}
key = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()[:20]
cache = BASE / "full-cache" / key
cache.mkdir(parents=True, exist_ok=True)
(RUN / "cache-config.json").write_text(json.dumps(config, indent=2))

def count_zips(directory):
    try:
        return sum(path.name.endswith(".zip") for path in directory.iterdir())
    except FileNotFoundError:
        return 0

expected_counts = {"Train": 1200, "Dev": 900}
cache_counts = {split: count_zips(cache / split) for split in expected_counts}
print("FULL_CACHE", cache, flush=True)
print("CACHE_ZIPS", cache_counts, "| số tệp trước khi kiểm nội dung ZIP", flush=True)

# Reuse Dev ZIPs from the verified 70-video run with the same source archives.
reference = BASE / "expanded-runs/1794680667780116476/cache-config.json"
old = json.loads(reference.read_text()) if reference.is_file() else {}
seed = []
if (old.get("protocol") == protocol and old.get("archives") == archives
        and old.get("scripts") == {
            "cdcn_prnet_smoke.py": "6a412b53c46c6af547a9834ce3f145538969c4aa0e3e80d8883621047d9bd947",
            "cdcn_prnet_expanded.py": "67e62819a56459056959811bbe995c8a125f479504ae59b17caba5a353dae4dc",
        }):
    old_key = hashlib.sha256(json.dumps(old, sort_keys=True).encode()).hexdigest()[:20]
    seed = ["--dev-cache", BASE / "expanded-cache" / old_key / "Dev"]

complete = not REPAIR_CACHE and all(cache_counts[split] == expected_counts[split] for split in SPLITS)
if complete:
    python = sys.executable
    mode = ["--restore-only"]
else:
    prepare_prnet_environment()
    run("install-prep-io", sys.executable, "-m", "uv", "pip", "install", "--python", PY, "pandas==2.2.3")
    python = PY
    mode = []
stage = []
if STAGE_TARS and not complete:
    needed = 0
    for split in SPLITS:
        if not REPAIR_CACHE and cache_counts[split] == expected_counts[split]:
            continue
        name = f"{split}_files.tar"
        local = WORK / "archives" / name
        if not local.is_file() or local.stat().st_size != archives[name]["bytes"]:
            needed += archives[name]["bytes"]
    if shutil.disk_usage(WORK).free > needed + 28 * 2**30:
        stage = ["--stage-dir", WORK / "archives"]
    else:
        print("Ổ cục bộ còn ít dung lượng, đọc TAR trực tiếp từ Drive.")

assets = WORK / f"assets-{key}"
summary_copy = RUN / "preparation.json"
summary_copy.unlink(missing_ok=True)
manifest = assets / "smoke_summary.json"
try:
    run("prepare-full", python, "-u", package / "cdcn_prnet_expanded.py",
        "--data", DATA, "--cache", cache, "--output", assets, "--prnet", WORK / "PRNet",
        "--renderer", WORK / "PRNet-Depth-Generation", "--full", "--splits", *SPLITS, *seed, *stage, *mode)
except (RuntimeError, OSError):
    if manifest.is_file():
        try:
            shutil.copyfile(manifest, RUN / "preparation-incomplete.json")
        except OSError as exc:
            print(f"Chưa lưu được manifest lỗi: {exc} | Manifest cục bộ: {manifest}", flush=True)
    raise
shutil.copyfile(manifest, summary_copy)
PREPARED_SPLITS = SPLITS"""),
    ("code", """#@title 4. Đo train batch 56 và chấm Dev đầy đủ
if not torch.cuda.is_available():
    raise RuntimeError("Chọn runtime A100 rồi chạy lại cell 1–4.")
if set(globals().get("PREPARED_SPLITS", ())) != {"Train", "Dev"}:
    raise ValueError("Chuẩn bị đủ Train và Dev ở cell 3 trước khi train.")
EPOCHS = 3
BATCH = 56
WORKERS = 4
result = RUN / f"train-{time.time_ns()}"
run("train-full-pilot", sys.executable, "-u", WORK / "scripts/cdcn_prnet_train_pilot.py",
    "--assets", assets, "--output", result, "--epochs", EPOCHS, "--batch", BATCH,
    "--seed", 43, "--device", "cuda", "--profile", "full", "--protocol", DATA / "Protocols.tar",
    "--workers", WORKERS)
report = json.loads((result / "pilot_result.json").read_text())
print(json.dumps(report, indent=2))
if EPOCHS > 1:
    typical = statistics.median(row["seconds"] for row in report["history"][1:])
    print(f"Trung vị epoch sau khởi động: {typical:.2f}s")
print("RUN_DIR", result)"""),
]


if __name__ == "__main__":
    build_notebook(
        CELLS, "Face_PAD_OULU_NPU_CDCN_PRNet_Full_Train_Dev.ipynb",
        ["__init__", "progress", "losses", "colab_cache", "oulu_npu", "data", "webcam",
         "models/__init__", "models/cdcn_official", "models/cdcn_depth_head",
         "models/depth_head", "models/mobilenet_baseline"],
        {f"scripts/{name}.py": ROOT / f"scripts/{name}.py"
         for name in ("cdcn_prnet_smoke", "cdcn_prnet_train_pilot",
                      "cdcn_prnet_expanded", "audit_cdc_n_p1_scores")},
    )
