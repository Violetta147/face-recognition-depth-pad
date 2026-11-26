"""Build the A100 notebook for continuing CDCN from epoch 100 on Train/Dev."""
from build_cdcn_prnet_full_colab import CELLS as FULL
from build_oulu_colab import ROOT, build_notebook


CELLS = [
    ("markdown", """# CDCN và PRNet · Tiếp tục từ epoch 100 trên OULU-NPU P1

Nhánh tiếp tục chính dùng **A100 80 GB**, cùng GPU đã ghi ở lượt 100 epoch.
Chạy **cell 1 → 2 → 3 → 4**. Cell 3 khôi phục
1.200 video Train và 900 video Dev từ cache, tổng 36.000 khung.

Batch 56 đã chạy được trong phép đo A100 40 GB. Độ tương đương của kết
quả huấn luyện giữa 40 GB và 80 GB chưa được kiểm chứng. Nhánh này chọn
giữ cùng GPU để giảm thay đổi điều kiện tính toán. Cell 4 kiểm GPU trước
khi train. Chi tiết quyết định có trong `docs/reviews/A100_CONTINUATION_20261126.md`.

Cell 4 tiếp tục từ `resume.pt` epoch 100, gồm trọng số, Adam, lịch LR
và bộ sinh số ngẫu nhiên. Cấu hình dùng batch 56, seed 43 và bốn worker
đọc ảnh. Lịch chấm Dev cố định tại epoch 150, 200, …, 1.300. Chọn ACER
gộp Dev thấp nhất, hòa giữ epoch sớm hơn, gồm cả mốc 100.

Mỗi năm epoch lưu trạng thái phục hồi lên Drive. Để dừng, chờ
`RECOVERY_CHECKPOINT` rồi dừng cell 4. Khi quay lại, chạy cell 1–4 với
cùng cấu hình. Notebook tự tìm trạng thái đã lưu và các mốc Dev hoàn tất.
`DEV_SELECTION` cho biết checkpoint tốt nhất theo Dev đã chấm.

`schedule.json` ghi GPU, phiên bản thư viện và các tùy chọn tính toán.
Các thông tin này được đối chiếu khi tiếp tục cùng lượt. Cùng loại GPU
vẫn chưa bảo đảm kết quả trùng từng bit. Bộ kiểm thử cục bộ kiểm logic
phục hồi. Độ khớp trên Colab cần bằng chứng thực nghiệm tương ứng.

Ước lượng từ lượt A100 80 GB trước là khoảng **6–7 giờ** cho 1.200 epoch bổ sung
và 24 lượt Dev, cộng khôi phục cache và lưu checkpoint. Mốc 1.300 theo giới hạn huấn luyện trong paper.
Tần suất Dev 50 epoch là lựa chọn của dự án.

Kết quả cuối ở `dev_selection.json`, log và các thư mục epoch trên Drive.
Lượt Test epoch 100 đã hoàn tất với ACER gộp 6,67% và được ghi trong tài
liệu kết quả của dự án."""),
    ("code", FULL[1][1].replace("full-runs", "dev-continuation-logs")),
    FULL[2],
    FULL[3],
    ("code", """#@title 4. Tiếp tục tới epoch 1300, chấm Dev mỗi 50 epoch
if not torch.cuda.is_available():
    raise RuntimeError("Nhánh tiếp tục chính dùng A100 80 GB rồi chạy lại cell 1–4.")
gpu_name = torch.cuda.get_device_name()
if gpu_name != "NVIDIA A100-SXM4-80GB":
    raise RuntimeError(f"Nhánh này giữ GPU của lượt 100 epoch, A100-SXM4-80GB. Hiện tại {gpu_name}.")
if set(globals().get("PREPARED_SPLITS", ())) != {"Train", "Dev"}:
    raise RuntimeError("Chạy cell 3 với đủ Train và Dev.")

INITIAL_RUN = BASE / "full-runs/1794972293512067663/train-1794973542248985819"
CONTINUATION = BASE / "dev-continuation-p1/from100-seed43-to1300-every50-a10080"
run("continue-train-dev", sys.executable, "-u", WORK / "scripts/cdcn_prnet_dev_schedule.py",
    "--initial", INITIAL_RUN, "--assets", assets, "--protocol", DATA / "Protocols.tar",
    "--output", CONTINUATION, "--epochs", 1300, "--dev-every", 50,
    "--checkpoint-every", 5, "--workers", 4)
selection = json.loads((CONTINUATION / "dev_selection.json").read_text())
print(json.dumps(selection["best"], indent=2))
print("DEV_SELECTION_FILE", CONTINUATION / "dev_selection.json")"""),
]


if __name__ == "__main__":
    build_notebook(
        CELLS, "Face_PAD_OULU_NPU_CDCN_PRNet_Continue_Train_Dev.ipynb",
        ["__init__", "progress", "losses", "colab_cache", "oulu_npu", "data", "webcam",
         "models/__init__", "models/cdcn_official", "models/cdcn_depth_head",
         "models/depth_head", "models/mobilenet_baseline"],
        {f"scripts/{name}.py": ROOT / f"scripts/{name}.py"
         for name in ("cdcn_prnet_smoke", "cdcn_prnet_train_pilot", "cdcn_prnet_expanded",
                      "audit_cdc_n_p1_scores", "cdcn_prnet_locked_test", "cdcn_prnet_dev_schedule")},
        gpu=True,
    )
