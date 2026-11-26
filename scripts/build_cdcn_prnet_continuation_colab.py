"""Build the A100 notebook for continuing CDCN from epoch 100 on Train/Dev."""
from build_cdcn_prnet_full_colab import CELLS as FULL
from build_oulu_colab import ROOT, build_notebook


CELLS = [
    ("markdown", """# CDCN và PRNet · Tiếp tục từ epoch 100 trên OULU-NPU P1

Chọn **A100 40 GB hoặc 80 GB**, chạy **cell 1 → 2 → 3 → 4**. Cell 3 khôi phục
1.200 video Train và 900 video Dev từ cache, tổng 36.000 khung.

Batch 56 đã chạy trong phép đo A100 40 GB trước đó, với đỉnh bộ nhớ
PyTorch giữ khoảng 35,50 GiB. Có thể dùng A100 40 GB đang được cấp để
tiếp tục. RAM hệ thống và RAM GPU được Colab hiển thị riêng.

Cell 4 tiếp tục từ `resume.pt` epoch 100, gồm trọng số, Adam, lịch LR
và bộ sinh số ngẫu nhiên. Cấu hình dùng batch 56, seed 43 và bốn worker
đọc ảnh. Lịch chấm Dev cố định tại epoch 150, 200, …, 1.300. Chọn ACER
gộp Dev thấp nhất, hòa giữ epoch sớm hơn, gồm cả mốc 100.

Mỗi năm epoch lưu trạng thái phục hồi lên Drive. Để dừng, chờ
`RECOVERY_CHECKPOINT` rồi dừng cell 4. Khi quay lại, chạy cell 1–4 với
cùng cấu hình. Notebook tự tìm trạng thái đã lưu và các mốc Dev hoàn tất.
`DEV_SELECTION` cho biết checkpoint tốt nhất theo Dev đã chấm.

Ước lượng từ lượt A100 80 GB trước là khoảng **6–7 giờ** cho 1.200 epoch bổ sung
và 24 lượt Dev, cộng khôi phục cache và lưu checkpoint. Thời gian thực tế
trên A100 40 GB cần xem log các epoch đầu. Mốc 1.300 theo giới hạn huấn luyện trong paper.
Tần suất Dev 50 epoch là lựa chọn của dự án.

Kết quả cuối ở `dev_selection.json`, log và các thư mục epoch trên Drive.
Lượt Test epoch 100 đã hoàn tất với ACER gộp 6,67% và được ghi trong tài
liệu kết quả của dự án."""),
    ("code", FULL[1][1].replace("full-runs", "dev-continuation-logs")),
    FULL[2],
    FULL[3],
    ("code", """#@title 4. Tiếp tục tới epoch 1300, chấm Dev mỗi 50 epoch
if not torch.cuda.is_available():
    raise RuntimeError("Chọn A100 40 GB hoặc 80 GB rồi chạy lại cell 1–4.")
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
