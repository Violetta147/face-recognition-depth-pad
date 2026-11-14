"""Build the expanded OULU CDCN Train/Dev notebook."""

from build_cdcn_prnet_train_colab import CELLS as PILOT_CELLS, include_setup
from build_oulu_colab import ROOT, build_notebook


SETUP = PILOT_CELLS[1][1].replace('WORK = Path("/content/cdcn-prnet-train-pilot")',
    'WORK = Path("/content/cdcn-prnet-expanded")')
SETUP = SETUP.replace('RUN = Path("/content/drive/MyDrive/face-pad/cdcn-prnet-train-pilot-p1") / str(time.time_ns())',
    '''BASE = Path("/content/drive/MyDrive/face-pad/cdcn-prnet-train-pilot-p1")
RUN = BASE / "expanded-runs" / str(time.time_ns())''')

CELLS = [
    ("markdown", """# CDCN trên OULU-NPU · Train/Dev mở rộng
Chọn A100 rồi chạy cell 1–4. Tập Train có 40 video, Dev có 30 video. Mỗi
video dùng 8 khung. Mẫu lấy phiên 1, điện thoại 1 với 5 loại video mỗi
người. Lượt train dùng batch 32, FP32 và 10 epoch.

Cell 3 dựng RGB, hộp mặt và PRNet trên CPU. Cell này lưu từng video đã
hoàn tất lên Drive và dùng lại sau khi Colab đổi runtime. Có thể chạy
cell 1–3 trên CPU rồi chuyển sang GPU và chạy lại cell 1–4. Cell 4 ghi
checkpoint, điểm và thời gian Dev."""),
    ("code", SETUP.replace(
        'if not torch.cuda.is_available():\n    raise RuntimeError("Chọn runtime GPU trước khi tiếp tục")\n'
        'print("GPU:", torch.cuda.get_device_name(), "| PyTorch:", torch.__version__)',
        'print("GPU:", torch.cuda.get_device_name() if torch.cuda.is_available() else "CPU",'
        ' "| PyTorch:", torch.__version__)'
    )),
    PILOT_CELLS[2],
    ("code", "#@title 3. Khôi phục hoặc dựng 560 khung MTCNN–PRNet\n" + include_setup() + """

import json
import zipfile

def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()

package = WORK / "scripts"
archive_binding = {}
for name in ("Train_files.tar", "Dev_files.tar"):
    path = DATA / name
    with path.open("rb") as stream:
        archive_binding[name] = {"bytes": path.stat().st_size,
                                 "prefix_sha256": hashlib.sha256(stream.read(65536)).hexdigest()}
config = {"protocol": digest(DATA / "Protocols.tar"), "archives": archive_binding,
          "scripts": {name: hashlib.sha256((package / name).read_text(encoding="utf-8").encode()).hexdigest()
                      for name in ("cdcn_prnet_smoke.py", "cdcn_prnet_expanded.py")}}
key = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()[:20]
cache = BASE / "expanded-cache" / key
cache.mkdir(parents=True, exist_ok=True)
(RUN / "cache-config.json").write_text(json.dumps(config, indent=2))

pilot = BASE / "prepared-cache" / "c375c1dfc4bce1acc988"
metadata = pilot / "snapshot.json"
baseline = []
if metadata.is_file():
    meta = json.loads(metadata.read_text())
    if (meta["key"]["archives"] == archive_binding and meta["key"]["protocol"] == config["protocol"]
            and meta["key"]["preparer"] == config["scripts"]["cdcn_prnet_smoke.py"]):
        expected = "50ca8a42b3a5c3241714c181222b4b06e5098383b02b46a65071d5753be07443"
        if meta["sha256"] != expected:
            raise ValueError(f"Unexpected pilot snapshot: {metadata}")
        snapshot = pilot / f"assets-{expected}.zip"
        seed = (WORK / f"seed-{time.time_ns()}").resolve()
        with Progress("Restore the existing 48 frames"):
            local = seed.with_suffix(".zip")
            shutil.copyfile(snapshot, local)
            if digest(local) != expected:
                raise ValueError("Pilot ZIP checksum differs")
            with zipfile.ZipFile(local) as archive:
                if any(not (seed / name).resolve().is_relative_to(seed) for name in archive.namelist()):
                    raise ValueError("Invalid ZIP entry")
                archive.extractall(seed)
            local.unlink()
        baseline = ["--baseline", seed]

prepare_prnet_environment()
assets = WORK / f"expanded-{time.time_ns()}"
try:
    run("prepare-expanded", PY, "-u", package / "cdcn_prnet_expanded.py",
        "--data", DATA, "--cache", cache, "--output", assets, "--prnet", PRNET,
        "--renderer", RENDERER, *baseline)
finally:
    manifest = assets / "smoke_summary.json"
    if manifest.is_file():
        shutil.copyfile(manifest, RUN / "preparation.json")
print("EXPANDED_CACHE", cache)"""),
    ("code", """#@title 4. Train 10 epoch và chấm Dev
if not torch.cuda.is_available():
    raise RuntimeError("Chọn A100 và chạy lại cell 1–4 để khôi phục cache rồi train")
result = RUN / f"train-{time.time_ns()}"
run("train-expanded", sys.executable, "-u", WORK / "scripts/cdcn_prnet_train_pilot.py",
    "--assets", assets, "--output", result, "--epochs", 10, "--batch", 32,
    "--seed", 43, "--device", "cuda", "--profile", "expanded")
print((result / "pilot_result.json").read_text())
print("RUN_DIR", result)"""),
]


if __name__ == "__main__":
    build_notebook(
        CELLS, "Face_PAD_OULU_NPU_CDCN_PRNet_Expanded.ipynb",
        ["__init__", "progress", "losses", "models/__init__", "models/cdcn_official",
         "models/cdcn_depth_head", "models/depth_head", "models/mobilenet_baseline"],
        {f"scripts/{name}.py": ROOT / f"scripts/{name}.py"
         for name in ("cdcn_prnet_smoke", "cdcn_prnet_train_pilot", "cdcn_prnet_expanded",
                      "audit_cdc_n_p1_scores")},
        gpu=True,
    )
