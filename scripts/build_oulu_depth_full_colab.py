"""Build a CPU Colab notebook for complete OULU P1 pseudo-depth with Drive snapshots."""
from build_oulu_colab import ROOT, build_notebook
from build_oulu_depth_smoke_colab import CELLS as SMOKE_CELLS, SOURCES as SMOKE_SOURCES

SOURCES = [*SMOKE_SOURCES, "oulu_depth_full"]
SETUP = SMOKE_CELLS[3][1].replace('"onnx", "onnxruntime", "Cython", "setuptools"',
                                 '"onnx==1.23.2", "onnxruntime==1.32.0", "Cython==3.0.12", "setuptools"')
BUNDLE_SETUP = SMOKE_CELLS[2][1].split("MANIFEST, counts = prepare_smoke")[0]

CELLS = [
    ("markdown", """# OULU-NPU Protocol 1 · Tạo pseudo-depth cho Train/Dev
Chọn **CPU**. Nếu muốn dùng lại phiên smoke, chép cell 1–5 vào notebook đang mở và chạy theo thứ tự. Cần để phiên smoke hoàn thành trước. Notebook kiểm đúng hai ZIP RGB, dựng 3.360 map người thật và ghi 13.440 target attack bằng 0. Cache/snapshot ghi dưới một thư mục Drive riêng, mỗi nhóm tối đa 500 map thật. Nếu đổi runtime, chạy lại theo thứ tự để khôi phục snapshot. Dùng một runtime cho thư mục kết quả này.

Các cảnh báo xuất ONNX đã xuất hiện ở lượt smoke thành công. Nếu một map thật không dựng được, notebook lưu danh sách lỗi để xử lý trước khi train."""),
    ("code", SMOKE_CELLS[1][1].replace('RESULTS = BASE / "depth-smoke" / "p1-32-v1"',
                                     'SMOKE = BASE / "depth-smoke" / "p1-32-v1"\nRESULTS = BASE / "depth-full" / "p1-v1"')
             .replace('ROOT = WORK / "p1-32-v1"', 'ROOT = WORK / "full-p1-v1"')),
    ("code", BUNDLE_SETUP.replace("2. Nạp code và chuẩn bị 32 ảnh có kiểm hash",
                                  "2. Nạp code và khôi phục RGB Train/Dev") + '''
from deepface_pad.oulu_depth_full import restore_rgb, check_full_depth
from deepface_pad.colab_cache import file_hash, restore_cache
from deepface_pad.depth_jobs import prepare_depth_jobs
import json
from importlib.metadata import version

SMOKE_REPORT = json.loads((SMOKE / "smoke_summary.json").read_text(encoding="utf-8"))
assert SMOKE_REPORT["counts"] == {"rows": 32, "bona_fide": 24, "attack": 8}
MANIFEST = restore_rgb(RGB, WORK, ROOT)
print("FULL_RGB_READY", MANIFEST, "| source", BUNDLE_SHA256, flush=True)
'''),
    ("code", SETUP + '''
# Reuse the exact ONNX assets from smoke. A verified copy is retained for later runtimes.
paths = SMOKE_REPORT["environment"]["assets"]
assets = {path.name: path for path in (
    THREE_DDFA / "configs/mb1_120x120.yml",
    *(THREE_DDFA / "configs" / name for name in ("bfm_noneck_v3.pkl", "tri.pkl",
      "param_mean_std_62d_120x120.pkl", "bfm_noneck_v3.onnx")),
    THREE_DDFA / "weights/mb1_120x120.pth", THREE_DDFA / "weights/mb1_120x120.onnx",
    THREE_DDFA / "FaceBoxes/weights/FaceBoxesProd.pth",
    THREE_DDFA / "FaceBoxes/weights/FaceBoxesProd.onnx",
)}
asset_id = {"commit": COMMIT, "assets": paths}
asset_zip = RESULTS / "onnx-assets.zip"
local_asset_zip = WORK / "onnx-assets.zip"
generated = [path for path in assets.values() if path.suffix == ".onnx"]
if not all(path.is_file() for path in generated):
    if asset_zip.is_file():
        copy_progress(asset_zip, local_asset_zip, "Restore 3DDFA ONNX assets")
        restore_cache(THREE_DDFA, local_asset_zip, asset_id)
    else:
        # On a fresh runtime, export using the same smoke path before starting the full queue.
        probe = WORK / "asset-probe"
        probe_manifest, _ = prepare_smoke(RGB, probe)
        run("export-onnx-assets", sys.executable, WORK / "scripts/run_3ddfa_worker.py",
            "--3ddfa-root", THREE_DDFA, "--config", assets["mb1_120x120.yml"],
            "--pending", probe / "depth/3ddfa_pending.csv", "--ledger", probe / "depth/depth_status.csv",
            "--onnx", "--mode", "cpu", "--limit", 1)
if {name: file_hash(path) for name, path in assets.items()} != paths:
    raise ValueError("3DDFA assets differ from smoke. Use the smoke runtime to save the original ONNX assets.")
if not asset_zip.is_file():
    save_cache(THREE_DDFA, local_asset_zip, generated, asset_id)
    copy_progress(local_asset_zip, asset_zip, "Save verified 3DDFA ONNX assets")
print("DEPTH_ASSETS_READY", flush=True)
'''),
    ("code", '''#@title 4. Dựng map và lưu snapshot sau từng nhóm
from datetime import datetime, timezone
import pandas as pd

DEPTH = ROOT / "depth"
LEDGER = DEPTH / "depth_status.csv"
PENDING = DEPTH / "3ddfa_pending.csv"
WORKER = WORK / "scripts/run_3ddfa_worker.py"
CONFIG = assets["mb1_120x120.yml"]
WORKER_META = DEPTH / "depth_status.csv.worker.json"
identity = depth_identity(ROOT, MANIFEST, SMOKE / WORKER_META.name, list(assets.values()))
if file_hash(WORKER) != identity["worker"]["worker_script_sha256"]:
    raise ValueError("Worker source differs from successful smoke")
identity.update(data_root=str(ROOT),
                versions={name: version(name) for name in ("torch", "numpy", "onnx", "onnxruntime", "Cython")})
if identity["versions"] != SMOKE_REPORT["environment"]["versions"]:
    raise ValueError(f"Runtime dependency versions differ from smoke: {identity['versions']}")
snapshot = RESULTS / "depth-progress.zip"
local_snapshot = WORK / "depth-progress.zip"
marker = ROOT / "depth-identity.json"
if marker.is_file():
    if json.loads(marker.read_text(encoding="utf-8")) != identity:
        raise ValueError("Local depth preparation identity differs")
else:
    if snapshot.is_file():
        copy_progress(snapshot, local_snapshot, "Fetch latest depth snapshot")
        restore_cache(ROOT, local_snapshot, identity)
    marker.write_text(json.dumps(identity, indent=2), encoding="utf-8")

def save_depth_snapshot(archive, *extra_paths):
    local = WORK / archive.name
    files = [MANIFEST, marker, *extra_paths, *(p for p in DEPTH.iterdir() if p.suffix in {".npy", ".csv", ".json"})]
    save_cache(ROOT, local, files, identity)
    copy_progress(local, archive, f"Publish {archive.name}")

started = time.monotonic()
counts = prepare_depth_jobs(MANIFEST, ROOT, DEPTH)
if sum(counts.values()) != 16800:
    raise ValueError(f"Unexpected ledger population: {counts}")
# Even if a previous group recorded some failures, finish the other queued samples.
while counts["pending_3ddfa"]:
    before = counts["pending_3ddfa"]
    run("3ddfa-full", sys.executable, WORKER, "--3ddfa-root", THREE_DDFA, "--config", CONFIG,
        "--pending", PENDING, "--ledger", LEDGER, "--onnx", "--mode", "cpu",
        "--limit", 500, "--failure-report", DEPTH / "failures.csv")
    state = pd.read_csv(LEDGER, keep_default_na=False)
    counts = state.status.value_counts().to_dict()
    counts.setdefault("pending_3ddfa", 0)
    if json.loads(WORKER_META.read_text(encoding="utf-8")) != identity["worker"]:
        raise ValueError("Worker metadata differs from the registered worker")
    if counts["pending_3ddfa"] >= before:
        raise RuntimeError("Worker did not advance the pending queue")
    save_depth_snapshot(snapshot)
    print("DEPTH_BATCH_SAVED", counts, "|", round(time.monotonic() - started), "seconds", flush=True)
copy2(LEDGER, RESULTS / LEDGER.name)
if (DEPTH / "failures.csv").is_file():
    copy2(DEPTH / "failures.csv", RESULTS / "failures.csv")
print("DEPTH_QUEUE_FINISHED", counts, flush=True)
'''),
    ("code", '''#@title 5. Kiểm coverage và xuất manifest để train E1
from deepface_pad.depth_jobs import depth_provenance_path
report = check_full_depth(MANIFEST, LEDGER, ROOT)
report["identity"] = identity
report["validated_utc"] = datetime.now(timezone.utc).isoformat()
derived = ROOT / "train_dev_with_depth.csv"
summary = ROOT / "depth_summary.json"
summary.write_text(json.dumps(report, indent=2), encoding="utf-8")
save_depth_snapshot(RESULTS / "depth-final.zip", derived, depth_provenance_path(derived), summary)
copy2(summary, RESULTS / summary.name)
print("DEPTH_FULL_PASS", report["counts"], "|", RESULTS / summary.name, flush=True)
'''),
]
if __name__ == "__main__":
    build_notebook(CELLS, "Face_PAD_OULU_NPU_Depth_Full.ipynb", SOURCES,
                   {"scripts/run_3ddfa_worker.py": ROOT / "scripts/run_3ddfa_worker.py"})
