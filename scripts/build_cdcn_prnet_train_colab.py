"""Build the self-contained CDCN OULU P1 Train/Dev pilot notebook."""

from build_cdcn_prnet_colab import CELLS as PREP_CELLS
from build_oulu_colab import ROOT, build_notebook


CELLS = [
    ("markdown", """# CDCN CVPR 2020 · Lượt chạy thử Train/Dev trên OULU-NPU
Chọn **GPU A100** và chạy các cell theo thứ tự. Lượt này dùng 3 video Train và
3 video Dev, mỗi video có 8 khung. Chạy 3 epoch từ khởi tạo mới. Mỗi epoch lấy
ngẫu nhiên một khung mỗi video Train. Dev dùng đủ 8 khung và tính trung bình
các tỷ số tổng depth dự đoán trên tổng map PRNet.

Cell 3 khôi phục ZIP tiền xử lý trên Drive nếu dấu vân tay cấu hình trùng.
Nếu cần dựng từ đầu, cell đó đọc các video được chọn trong TAR và ghi
snapshot lên Drive. Cell 4 lưu checkpoint, điểm video, chỉ số Dev và thời
gian. Chỉ số của 3 video Dev dùng để kiểm tra pipeline. Mốc của paper dùng
toàn bộ Protocol 1 và chấm trên Test.

Nếu đã có kết quả pilot, chạy cell 1–3 rồi chuyển thẳng đến cell 5 để đo
batch trên A100 bằng các khung Train đã có."""),
    ("code", PREP_CELLS[1][1].replace("cdcn-prnet-smoke", "cdcn-prnet-train-pilot") + """
import torch
if not torch.cuda.is_available():
    raise RuntimeError("Chọn runtime GPU trước khi tiếp tục")
print("GPU:", torch.cuda.get_device_name(), "| PyTorch:", torch.__version__)"""),
    ("code", PREP_CELLS[2][1].split('\nrun("install-uv"', 1)[0].replace(
        "2. Nạp code và cài môi trường tách riêng", "2. Nạp code đi kèm"
    )),
    ("code", """#@title 3. Khôi phục hoặc dựng 48 khung MTCNN–PRNet
import json
import zipfile

def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()

archives = {}
for name in ("Train_files.tar", "Dev_files.tar"):
    path = DATA / name
    with path.open("rb") as stream:
        archives[name] = {"bytes": path.stat().st_size,
                          "prefix_sha256": hashlib.sha256(stream.read(65536)).hexdigest()}
worker = (WORK / "scripts/cdcn_prnet_smoke.py").read_text(encoding="utf-8")
key = {"profile": "p1-3-videos-per-split-8-frames",
       "protocol": sha(DATA / "Protocols.tar"), "archives": archives,
       "preparer": hashlib.sha256(worker.encode("utf-8")).hexdigest()}
key_hash = hashlib.sha256(json.dumps(key, sort_keys=True).encode()).hexdigest()[:20]
cache = RUN.parent / "prepared-cache" / key_hash
cache.mkdir(parents=True, exist_ok=True)
assets = (WORK / f"assets-{time.time_ns()}").resolve()
cache_meta = cache / "snapshot.json"
if cache_meta.is_file():
    with Progress("Restore RGB/bbox/PRNet from Drive"):
        meta = json.loads(cache_meta.read_text())
        digest = meta["sha256"]
        if meta["key"] != key or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ValueError(f"Invalid snapshot metadata: {cache_meta}")
        snapshot = cache / f"assets-{digest}.zip"
        local = assets.with_suffix(".zip")
        shutil.copyfile(snapshot, local)
        if digest != sha(local):
            raise ValueError(f"Snapshot verification failed: {snapshot}")
        with zipfile.ZipFile(local) as archive:
            if any(not (assets / name).resolve().is_relative_to(assets) for name in archive.namelist()):
                raise ValueError("Invalid archive path")
            archive.extractall(assets)
        local.unlink()
else:
    prepare_prnet_environment()
    run("prepare-48-frames", PY, "-u", WORK / "scripts/cdcn_prnet_smoke.py",
        "--data", DATA, "--prnet", PRNET, "--renderer", RENDERER, "--training-pilot", "--output", assets)
    with Progress("Save RGB/bbox/PRNet to Drive"):
        local = Path(shutil.make_archive(str(assets), "zip", assets))
        digest = sha(local)
        snapshot = cache / f"assets-{digest}.zip"
        partial = cache / f"{RUN.name}-assets.zip.part"
        shutil.copyfile(local, partial)
        if sha(partial) != digest:
            raise ValueError("Snapshot copy differs from local ZIP")
        partial.replace(snapshot)
        metadata = cache / f"{RUN.name}-snapshot.json.part"
        metadata.write_text(json.dumps({"key": key, "sha256": digest}, indent=2))
        metadata.replace(cache_meta)
        local.unlink()
shutil.copyfile(assets / "smoke_summary.json", RUN / "preparation.json")
print("PILOT_DATA_READY", snapshot)"""),
    ("code", """#@title 4. Train CDCN, đọc lại checkpoint và tính điểm Dev
EPOCHS = 3
BATCH = 3
SEED = 43
result = RUN / f"train-{time.time_ns()}"
run("train-and-dev", sys.executable, "-u", WORK / "scripts/cdcn_prnet_train_pilot.py",
    "--assets", assets, "--output", result, "--epochs", EPOCHS, "--batch", BATCH,
    "--seed", SEED, "--device", "cuda")
print((result / "pilot_result.json").read_text())
print("RUN_DIR", result)"""),
    ("code", """#@title 5. Đo batch 8, 16, 32 và 56 trên A100
PROBE_BATCHES = (8, 16, 32, 56)
report = RUN / f"batch-probe-{time.time_ns()}.json"
run("batch-probe", sys.executable, "-u", WORK / "scripts/cdcn_prnet_batch_probe.py",
    "--assets", assets, "--output", report, "--warmup", 2, "--steps", 6,
    "--batches", *PROBE_BATCHES)
print(report.read_text())"""),
]


def include_setup():
    setup = PREP_CELLS[2][1].split('\nrun("install-uv"', 1)[1].splitlines()
    setup[0] = 'run("install-uv"' + setup[0]
    sources = PREP_CELLS[3][1].splitlines()[1:]
    end = next(i for i, line in enumerate(sources) if line.startswith('run("verify-prnet"'))
    lines = ["def prepare_prnet_environment():", "    global PY, PRNET, RENDERER"]
    lines.extend("    " + line if line else "" for line in setup + sources[:end])
    return "\n".join(lines)


if __name__ == "__main__":
    cells = CELLS.copy()
    title, body = cells[3][1].split("\n", 1)
    cells[3] = ("code", title + "\n" + include_setup() + "\n\n" + body)
    build_notebook(
        cells, "Face_PAD_OULU_NPU_CDCN_PRNet_Train_Pilot.ipynb",
        ["__init__", "losses", "progress", "models/__init__", "models/cdcn_official",
         "models/cdcn_depth_head", "models/depth_head", "models/mobilenet_baseline"],
        {f"scripts/{name}.py": ROOT / f"scripts/{name}.py"
         for name in ("cdcn_prnet_smoke", "cdcn_prnet_train_pilot",
                      "cdcn_prnet_batch_probe", "audit_cdc_n_p1_scores")},
        gpu=True,
    )
