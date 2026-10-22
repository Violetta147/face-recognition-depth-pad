"""Build the clean, run-all notebook for frozen-result figure export."""
import json
from pathlib import Path


def markdown(text):
    return {"cell_type":"markdown","metadata":{},"source":text.splitlines(keepends=True)}


def code(text):
    return {"cell_type":"code","metadata":{},"execution_count":None,"outputs":[],"source":text.splitlines(keepends=True)}


def build():
    cells = [markdown("""# Xuất hình báo cáo/slides — E0, E1, E2, E3, E3b, E4

**Chọn GPU rồi Run all.** Cho phép mount Drive; source ZIP tự lấy từ thư mục bàn giao.
Notebook đọc các run đã hoàn tất, không train, không chọn lại model/ngưỡng từ test.

Xuất **31 hình** (PNG 300 dpi + PDF + SVG), CSV nguồn, caption, trang INDEX và ZIP.
Gồm 20 hình thống kê; MAE E1–E4; RGB gallery; 7 case RGB/target/mask/prediction/error;
2 hình hiệu năng cùng GPU. Kết quả nhiều seed và webcam chưa có nên không tạo số giả.
Mọi model/case giữ cả kết quả không cải thiện. Đây là CASIA development protocol, seed 42.

Ảnh xuất chứa các frame nghiên cứu; lưu trong thư mục riêng trên Drive của bạn.
Notebook sạch để phân phối; file notebook sau Run all có output ảnh nên giữ cùng artifact riêng.
"""),code('''#@title 0.1 Mount Drive và đường dẫn
from google.colab import drive, files
drive.mount("/content/drive")
from pathlib import Path
from datetime import datetime, timezone
import json, os, shutil, subprocess, sys
DRIVE_ROOT = Path("/content/drive/MyDrive/face-pad")
REPO_ROOT = Path("/content/figures-source/DeepFace-PAD")
HANDOFF = DRIVE_ROOT / "handoffs/figures-e0-e4-20261016"
MANIFEST = DRIVE_ROOT / "reports/casia_fasd_debug_with_depth.csv"
FREEZE = DRIVE_ROOT / "reports/round5-525c80889106/comparison_freeze.json"
DATA_ROOT = Path("/content/datasets/casia-fasd")
assert DRIVE_ROOT.is_dir(), "Thiếu MyDrive/face-pad; kiểm tra đúng tài khoản Drive"
assert MANIFEST.is_file() and FREEZE.is_file(), "Thiếu manifest/freeze; gửi lỗi cho Codex"
'''),code('''#@title 0.2 Nạp source mới dành cho xuất hình
archive = Path("/content/DeepFace-PAD-Figures-source.zip")
if not archive.is_file() and (HANDOFF / archive.name).is_file():
    shutil.copy2(HANDOFF / archive.name, archive)
if not archive.is_file():
    print("Upload DeepFace-PAD-Figures-source.zip được cung cấp cùng notebook.")
    files.upload()
assert archive.is_file(), "Thiếu source ZIP xuất hình"
shutil.unpack_archive(str(archive), "/content/figures-source")
assert (REPO_ROOT / "scripts/export_report_figures.py").is_file()
subprocess.run([sys.executable,"-m","pip","install","-q","-e",".[dev]"],cwd=REPO_ROOT,check=True)
FIGURE_SOURCE_COMMIT = (REPO_ROOT / "SOURCE_COMMIT.txt").read_text().strip()
print("Figure source commit:",FIGURE_SOURCE_COMMIT)
print("Checkpoint experiment source: 525c80889106c06525f5b758e8725c8ac9cee856")
'''),code('''#@title 0.3 Kiểm tra GPU và chuẩn bị output riêng
import torch
assert torch.cuda.is_available(), "Chọn Runtime > Change runtime type > GPU, rồi Run all lại"
print("Torch:",torch.__version__,"GPU:",torch.cuda.get_device_name(0))
RUN_TAG = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
OUTPUT_DIR = DRIVE_ROOT / "reports" / f"figures-e0-e4-{RUN_TAG}"
assert not OUTPUT_DIR.exists()
print("Output:",OUTPUT_DIR)
print("Chỉ inference/đo forward; không train hoặc sửa run gốc.")
'''),markdown("""## 1. Tạo toàn bộ hình

Cell dưới in tên hình và tiến độ từng model. MAE validation dùng 960 frame của cùng split;
ảnh minh họa dùng một frame giữa mỗi video được chọn trước. Nếu runtime còn dataset từ
Lượt 5 thì tái sử dụng; nếu thiếu chỉ lấy các RGB/target cần thiết từ ZIP/TAR cũ.
Không cần chạy lại notebook training. Nếu lỗi kiểm tra input, giữ nguyên file và gửi lỗi.
"""),code('''#@title 1.1 Xuất tất cả hình với log trực tiếp
command = [sys.executable,"scripts/export_report_figures.py",
    "--runs-dir",str(DRIVE_ROOT / "runs"),"--manifest",str(MANIFEST),"--freeze",str(FREEZE),
    "--output-dir",str(OUTPUT_DIR),"--data-root",str(DATA_ROOT),
    "--dataset-zip",str(DRIVE_ROOT / "casia-fasd.zip"),
    "--depth-tar",str(DRIVE_ROOT / "depth-checkpoints/casia-fasd-depth-checkpoint.tar"),"--phase","all"]
environment = os.environ.copy()
environment["PYTHONPATH"] = str(REPO_ROOT / "src") + os.pathsep + environment.get("PYTHONPATH","")
environment["OMP_NUM_THREADS"] = "1"
environment["MKL_NUM_THREADS"] = "1"
process = subprocess.Popen(command,cwd=REPO_ROOT,env=environment,stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT,text=True,bufsize=1)
for line in process.stdout:
    print(line,end="",flush=True)
return_code = process.wait()
assert return_code == 0, "Xuất hình chưa hoàn tất; gửi nguyên output lỗi, không bỏ qua assert"
manifest = json.loads((OUTPUT_DIR / "figure_manifest.json").read_text())
assert manifest["phase"] == "all" and len(manifest["figures"]) == 31
print("FIGURES_COMPLETE:",len(manifest["figures"]),"hình")
'''),code('''#@title 2.1 Xem trước một số hình chính
from IPython.display import display, Markdown
from PIL import Image
names = ["01_pipeline","05_test_metrics","06_test_error_rates","07_ROC",
         "12_paired_errors","13_quality_errors","15_depth_MAE_all_models","18_efficiency_common256"]
names += [row["name"] for row in manifest["figures"] if row["name"].startswith("17_case_")][:1]
for name in names:
    display(Markdown("**"+name+"**"))
    with Image.open(OUTPUT_DIR / "png" / f"{name}.png") as original:
        preview = original.copy()
        preview.thumbnail((1400,1000))
        display(preview)
print("Preview chỉ thu nhỏ trong notebook; PNG/PDF/SVG gốc giữ nguyên chất lượng.")
'''),code('''#@title 2.2 Đóng gói và tải tất cả hình
archive_path = Path(shutil.make_archive(str(OUTPUT_DIR),"zip",root_dir=OUTPUT_DIR))
print("THƯ MỤC HÌNH:",OUTPUT_DIR)
print("ZIP:",archive_path)
print("Mở INDEX.html sau khi giải nén để xem toàn bộ hình và caption.")
print("Dùng png/ cho Word/slides; pdf/ hoặc svg/ khi cần phóng lớn; data/ để đối chiếu số liệu.")
files.download(str(archive_path))
'''),markdown("""## Hoàn tất

Gửi Codex dòng `FIGURES_COMPLETE` và đường dẫn thư mục output để kiểm tra bộ hình cuối.
`CAPTIONS.csv` giải thích từng hình; `figure_manifest.json` ghi input hashes, code/runtime,
thang màu depth/error, chọn case, sai khác inference và điều kiện đo latency.
Không dùng forward latency làm FPS webcam hoặc dùng một seed để vẽ mean±SD nhiều seed.
""")]
    for index,cell in enumerate(cells): cell["id"] = f"figures-{index:02d}"
    return {"cells":cells,"metadata":{"accelerator":"GPU","colab":{"name":"Face_PAD_Export_All_Figures_E0_E4.ipynb"},
        "kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},"language_info":{"name":"python"}},"nbformat":4,"nbformat_minor":5}


if __name__ == "__main__":
    path = Path(__file__).resolve().parents[1] / "notebooks/Face_PAD_Export_All_Figures_E0_E4.ipynb"
    path.write_text(json.dumps(build(),ensure_ascii=False,indent=1)+"\n",encoding="utf-8")
    print(path)
