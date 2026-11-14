"""Build the full-membership OULU-NPU P1 Train/Dev notebook."""

from build_cdcn_prnet_expanded_colab import CELLS as EXPANDED
from build_cdcn_prnet_train_colab import include_setup
from build_oulu_colab import ROOT, build_notebook


CELLS = [
    ("markdown", """# CDCN trên OULU-NPU · Train/Dev đầy đủ của Protocol 1
Chạy **cell 1–3 trên CPU** để chuẩn bị 1.200 video Train và 900 video Dev.
Train lấy 24 khung rải đều qua mỗi video, Dev giữ 8 khung. Cell 3 lưu
từng video đã hoàn tất lên Drive và có thể chạy lại sau khi đổi runtime.

Sau khi cell 3 báo đủ 36.000 khung, chuyển sang **A100 80 GB** và chạy
lại **cell 1–4**. Cell 3 khôi phục dữ liệu đã chuẩn bị. Cell 4 chạy 3 epoch
từ đầu với batch 56 rồi chấm toàn bộ Dev, để đo thời gian trước khi chốt
lượt huấn luyện dài. Kết quả lưu trên Drive."""),
    ("code", EXPANDED[1][1].replace("cdcn-prnet-expanded", "cdcn-prnet-full").replace("expanded-runs", "full-runs")),
    EXPANDED[2],
    ("code", "#@title 3. Khôi phục hoặc chuẩn bị Train/Dev đầy đủ\n" + include_setup() + """

import json
import statistics
from deepface_pad.colab_cache import SPLIT_ARCHIVES, file_hash

# Có thể chạy một split trước rồi chạy lại cả hai. Cache theo video nằm trên Drive.
SPLITS = ("Train", "Dev")
STAGE_TARS = True  # chép TAR thiếu vào ổ cục bộ để đọc nhanh hơn
REPAIR_CACHE = False  # đặt True nếu log báo ZIP thiếu hoặc hỏng dù đã đủ số tệp
package = WORK / "scripts"
archives = {}
for key in ("train", "val"):
    name, size = SPLIT_ARCHIVES[key]
    path = DATA / name
    with path.open("rb") as stream:
        archives[name] = {"bytes": size, "prefix_sha256": hashlib.sha256(stream.read(65536)).hexdigest()}
protocol = file_hash(DATA / "Protocols.tar")
config = {"profile": "p1-full-train24-dev8", "protocol": protocol, "archives": archives,
          "scripts": {name: hashlib.sha256((package / name).read_text(encoding="utf-8").encode()).hexdigest()
                      for name in ("cdcn_prnet_smoke.py", "cdcn_prnet_expanded.py")}}
key = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()[:20]
cache = BASE / "full-cache" / key
cache.mkdir(parents=True, exist_ok=True)
(RUN / "cache-config.json").write_text(json.dumps(config, indent=2))

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

complete = not REPAIR_CACHE and all(
    len(list((cache / split).glob("*.zip"))) == (1200 if split == "Train" else 900)
    for split in SPLITS
)
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
        expected = 1200 if split == "Train" else 900
        if not REPAIR_CACHE and len(list((cache / split).glob("*.zip"))) == expected:
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
try:
    run("prepare-full", python, "-u", package / "cdcn_prnet_expanded.py",
        "--data", DATA, "--cache", cache, "--output", assets, "--prnet", WORK / "PRNet",
        "--renderer", WORK / "PRNet-Depth-Generation", "--full", "--splits", *SPLITS, *seed, *stage, *mode)
finally:
    manifest = assets / "smoke_summary.json"
    if manifest.is_file():
        shutil.copyfile(manifest, summary_copy)
print("FULL_CACHE", cache)"""),
    ("code", """#@title 4. Đo train batch 56 và chấm Dev đầy đủ
if not torch.cuda.is_available():
    raise RuntimeError("Chọn runtime A100 rồi chạy lại cell 1–4.")
if set(SPLITS) != {"Train", "Dev"} or not summary_copy.is_file():
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
