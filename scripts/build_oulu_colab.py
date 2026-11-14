"""Build the self-contained OULU-NPU Colab notebook with a small source bundle."""
import base64
import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ["__init__","data","metrics","oulu_metrics","oulu_npu","oulu_fast","progress","colab_cache","preflight","train","webcam","losses","depth_jobs","depth_qa","models/__init__","models/mobilenet_baseline","models/cdcn_official","models/cdcn_depth_head","models/depth_head"]
CELLS = [
  [
    "markdown",
    "# DeepFace-PAD · OULU-NPU Protocol 1 trên Colab\nChạy cell 1 và 2, rồi cell 4 và 5. Cell 3 là pilot tùy chọn. Chọn runtime GPU A100 và bấm **Connect**. Cell đầu xác nhận GPU, VRAM và thư mục Drive. Nếu bộ dữ liệu ở Shared with me, thêm shortcut vào My Drive và điền đúng đường dẫn vào `DATA`.\n\nLượt nhanh dùng MobileNetV3-Small, 8 khung hình/video và 3 epoch. Code và YuNet đã đi kèm notebook. Kết quả ghi vào My Drive. Phần Test ở cell riêng, chạy sau khi đã có checkpoint và ngưỡng khóa từ Dev."
  ],
  [
    "code",
    "#@title 1. Kết nối Drive và kiểm tra GPU\nfrom pathlib import Path\nfrom google.colab import drive\nimport shutil\nimport subprocess\nimport sys\nimport torch\n\ndrive.mount(\"/content/drive\")\nDATA = Path(\"/content/drive/MyDrive/OULU-NPU\")  # sửa nếu tên shortcut khác\nWORK = Path(\"/content/deepface-pad-oulu\")\nCACHE = WORK / \"cache\"\nRUNS = Path(\"/content/drive/MyDrive/face-pad/oulu-fast-p1\")\nassert torch.cuda.is_available(), \"Chọn runtime GPU rồi chạy lại cell này\"\nprecision = \"bf16\" if torch.cuda.is_bf16_supported() else \"fp32\"\nsubprocess.run([\"nvidia-smi\", \"--query-gpu=name,memory.total,driver_version\", \"--format=csv\"], check=True)\nfor name, size in {\"Train_files.tar\": 37753662976, \"Dev_files.tar\": 28151992320,\n                   \"Protocols.tar\": 417792}.items():\n    path = DATA / name\n    assert path.is_file() and path.stat().st_size == size, f\"Kiểm tra đường dẫn và dung lượng: {path}\"\nprint(\"precision:\", precision, \"| disk free (GiB):\", round(shutil.disk_usage(\"/content\").free / 2**30, 1))\nRUNS.mkdir(parents=True, exist_ok=True)"
  ],
  [
    "code",
    "#@title 2. Nạp code đi kèm notebook\nimport base64\nimport hashlib\nimport io\nimport os\nimport tarfile\n\nbundle = base64.b64decode(BUNDLE)\nassert hashlib.sha256(bundle).hexdigest() == BUNDLE_SHA256\nWORK.mkdir(parents=True, exist_ok=True)\nwith tarfile.open(fileobj=io.BytesIO(bundle), mode=\"r:gz\") as archive:\n    for member in archive:\n        destination = (WORK / member.name).resolve()\n        assert member.isfile() and destination.is_relative_to(WORK)\n        destination.parent.mkdir(parents=True, exist_ok=True)\n        destination.write_bytes(archive.extractfile(member).read())\nimport time\nsys.path.insert(0, str(WORK / \"src\"))\nfrom deepface_pad.progress import run_logged\nfrom deepface_pad.colab_cache import prepare_oulu_split\nENV = {**os.environ, \"PYTHONPATH\": str(WORK / \"src\")}\ndef call(module, *args):\n    label = \"-\".join([module.rsplit(\".\", 1)[-1], str(args[0])])\n    run_logged([sys.executable, \"-u\", \"-m\", module, *args], label=label,\n               log=RUNS / \"logs\" / f\"{label}-{time.time_ns()}.log\", env=ENV)\n\nFRAMES = 8\ndef prepare(split, pilot=False, backup=True):\n    return prepare_oulu_split(DATA, WORK, RUNS / \"prepared-cache\", split, FRAMES, pilot, call, backup=backup)\n\nwith open(RUNS / f\"source-{BUNDLE_SHA256[:12]}.tar.gz\", \"wb\") as output:\n    output.write(bundle)\nimport cv2\nimport torchvision\nimport yaml\nprint(\"code sha256\", BUNDLE_SHA256, \"| torch\", torch.__version__, \"| torchvision\", torchvision.__version__, \"| OpenCV\", cv2.__version__)"
  ],
  [
    "code",
    "#@title 3. Pilot tùy chọn, 30 video mỗi split\nprepare(\"train\", pilot=True)\nprepare(\"val\", pilot=True)\nprint(\"Mỗi split pilot cần có 30 video / 240 khung. Xem crop_counts và seconds trong log.\")"
  ],
  [
    "code",
    "#@title 4. Khôi phục hoặc chuẩn bị Train/Dev và lưu lên Drive\nBACKUP_RGB = True  # đặt False để train ngay; chạy lại cell này để lưu sau\n\nfor split in (\"train\", \"val\"):\n    manifest = prepare(split, backup=BACKUP_RGB)\n    summary = manifest.with_suffix(\".json\")\n    shutil.copyfile(summary, RUNS / f\"prep-{split}-{BUNDLE_SHA256[:12]}.json\")\nprint(\"Mốc kiểm: Train 1.200 / 9.600; Dev 900 / 7.200.\")"
  ],
  [
    "code",
    "#@title 5. Đo batch 64/128, rồi train và khóa ngưỡng từ Dev\n# 0 = tự đo batch 64/128. Thời gian mỗi epoch được in ra khi chạy.\nBATCH = 0\nWORKERS = 2\nEPOCHS = 3\nSEED = 43\ncall(\"deepface_pad.oulu_fast\", \"train\", \"--root\", CACHE, \"--directory\", CACHE / \"p1\",\n     \"--runs\", RUNS, \"--batch\", BATCH, \"--workers\", WORKERS, \"--epochs\", EPOCHS,\n     \"--seed\", SEED, \"--precision\", precision)"
  ],
  [
    "code",
    "#@title 6. Chấm Test một lần với checkpoint đã khóa\n# Điền đúng đường dẫn từ RUN_DIR= ở cuối cell 5.\nRUN_DIR = \"\"\nassert RUN_DIR, \"Điền RUN_DIR từ cell 5\"\nrun_dir = Path(RUN_DIR)\nassert (run_dir / \"freeze.json\").is_file(), \"Run chưa khóa\"\nassert not (run_dir / \"test_metrics.json\").exists(), \"Run này đã có kết quả Test\"\nprepare(\"test\")\nshutil.copyfile(CACHE / \"p1/test.json\", run_dir / \"test_preparation.json\")\ncall(\"deepface_pad.oulu_fast\", \"score\", \"--root\", CACHE, \"--manifest\", CACHE / \"p1/test.csv\",\n     \"--output\", run_dir)"
  ],
  [
    "markdown",
    "Nếu có lỗi, gửi nguyên traceback và dòng ngay trước đó. Nếu chạy xong, gửi `runtime.json`, `train_log.csv`, `metrics.json`, `test_metrics.json` và `throughput.json` (ở thư mục setup của lượt chạy). APCER và BPCER trong JSON là tỷ lệ 0–1. Nhân 100 để đọc phần trăm."
  ]
]


def build():
    buffer = io.BytesIO()
    files = {f"src/deepface_pad/{name}.py": ROOT / f"src/deepface_pad/{name}.py" for name in SOURCES}
    files["yunet.onnx"] = ROOT / "artifacts/round7/detector/face_detection_yunet_2023mar.onnx"
    with tarfile.open(fileobj=buffer, mode="w") as archive:
        for name, path in files.items():
            data = path.read_bytes()
            info = tarfile.TarInfo(name)
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
    bundle = gzip.compress(buffer.getvalue(), mtime=0)
    code = []
    for index, (kind, source) in enumerate(CELLS):
        cell = {"cell_type": kind, "id": f"oulu-{index:02d}", "metadata": {}}
        if kind == "code":
            cell.update(execution_count=None, outputs=[])
        if index == 2:
            encoded = base64.b64encode(bundle).decode()
            chunks = "\n".join(f"    {encoded[i:i+100]!r}" for i in range(0, len(encoded), 100))
            title, body = source.split("\n", 1)
            source = f"{title}\nBUNDLE_SHA256 = {hashlib.sha256(bundle).hexdigest()!r}\nBUNDLE = (\n{chunks}\n)\n{body}"
        cell["source"] = source.splitlines(keepends=True)
        code.append(cell)
    result = {"cells": code, "metadata": {"kernelspec": {"display_name": "Python 3",
              "language": "python", "name": "python3"}, "colab": {"provenance": []},
              "accelerator": "GPU"}, "nbformat": 4, "nbformat_minor": 5}
    path = ROOT / "notebooks/Face_PAD_OULU_NPU_A100.ipynb"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    build()
