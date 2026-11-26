"""Build the A100 notebook for continuing CDCN from epoch 100 on Train/Dev."""
from build_cdcn_prnet_full_colab import CELLS as FULL
from build_oulu_colab import ROOT, build_notebook


CELLS = [
    ("markdown", """# CDCN và PRNet · Tiếp tục từ epoch 100 trên OULU-NPU P1

Chọn **A100 40 GB hoặc 80 GB**. Chạy **cell 1 → 2 → 3 → 4**. Cell 3 khôi phục
1.200 video Train và 900 video Dev từ cache, tổng 36.000 khung.

Batch 56 đã chạy được trong phép đo A100 40 GB. Người dùng đã duyệt
tiếp tục trên 40 GB với thiết kế huấn luyện và đánh giá ban đầu.
Lượt nguồn 100 epoch chạy trên A100 80 GB. Môi trường của phần tiếp tục
được ghi để báo cáo việc chuyển GPU. Độ khớp từng bit chưa được kiểm chứng.

Cell 4 tiếp tục từ `resume.pt` epoch 100, gồm trọng số, Adam, lịch LR
và bộ sinh số ngẫu nhiên. Cấu hình dùng batch 56, seed 43 và bốn worker
đọc ảnh. Lịch chấm Dev cố định tại epoch 150, 200, …, 1.300. Chọn ACER
gộp Dev thấp nhất, hòa giữ epoch sớm hơn, gồm cả mốc 100.

Mỗi năm epoch lưu trạng thái phục hồi lên Drive. Để dừng, chờ
`RECOVERY_CHECKPOINT` rồi dừng cell 4. Khi quay lại, chạy cell 1–4 với
cùng cấu hình. Notebook tự tìm trạng thái đã lưu và các mốc Dev hoàn tất.
`DEV_SELECTION` cho biết checkpoint tốt nhất theo Dev đã chấm.

`schedule.json` ghi GPU, phiên bản thư viện và các tùy chọn tính toán
theo lần tiếp tục. Thông tin môi trường phục vụ truy vết. Các kiểm tra
manifest, checkpoint, trạng thái phục hồi và cấu hình học vẫn được áp dụng.

Log A100 80 GB ghi trung vị **16,93 giây mỗi epoch** sau khởi động,
Dev **120,21 giây**. Phần còn lại gồm **1.200 epoch và 24 lượt Dev**,
tương đương **6,45 giờ** ở tốc độ đã đo. Quy đổi tham khảo bằng tỷ lệ
batch 56 đã đo trên hai GPU cho khoảng **7,05 giờ** trên 40 GB.
Đây là ước lượng, chưa phải thời gian đo của lượt tiếp tục trên 40 GB.

Với **307,65 CU** còn lại và **8,16 CU mỗi giờ** do người dùng cung cấp,
7,05 giờ tương ứng khoảng **57,5 CU**, chưa tính khôi phục và lưu dữ liệu.
Dự trù 8–10 giờ tương ứng **65,3–81,6 CU**. Dải dự trù phục vụ ước tính
chi phí. Mốc kết thúc vẫn là tổng 1.300 epoch và lịch Dev vẫn mỗi 50 epoch.

Kết quả cuối ở `dev_selection.json`, log và các thư mục epoch trên Drive.
Lượt Test epoch 100 đã hoàn tất với ACER gộp 6,67% và được ghi trong tài
liệu kết quả của dự án."""),
    ("code", FULL[1][1].replace("full-runs", "dev-continuation-logs")),
    FULL[2],
    FULL[3],
    ("code", """#@title 4. Tiếp tục tới epoch 1300, chấm Dev mỗi 50 epoch
if not torch.cuda.is_available():
    raise RuntimeError("Chọn runtime A100 40 GB hoặc 80 GB rồi chạy lại cell 1–4.")
if set(globals().get("PREPARED_SPLITS", ())) != {"Train", "Dev"}:
    raise RuntimeError("Chạy cell 3 với đủ Train và Dev.")

INITIAL_RUN = BASE / "full-runs/1794972293512067663/train-1794973542248985819"
CONTINUATION = BASE / "dev-continuation-p1/from100-seed43-to1300-every50"
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
