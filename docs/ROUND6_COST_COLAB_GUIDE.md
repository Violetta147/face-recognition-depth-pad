# Chạy phần đo chi phí còn lại của Lượt 6

**Đã hoàn tất và kiểm toán ngày 22/10/2026.** Đã nhận notebook executed;
không còn bước cần chạy trên Colab. Nội dung dưới giữ làm hướng dẫn lịch sử.
Kết quả: `reports/ROUND_6_COST_RESULTS_2026-10-22.md`; chốt Lượt 6 tại
`docs/handoffs/ROUND6_CLOSEOUT_2026-10-22.md`. Không đo lại để chọn số nhanh.

Chỉ cần mở lại Colab A100. Không train, sinh pseudo-depth hoặc score test lại.
Gói source cho phép đo khác gói training đã khóa; không thay source/registration
training cũ. Cổng đo mặc định đóng để kiểm đúng GPU, checkpoint và input trước.

## Hai file cần mở/tải lên

Trong `artifacts/round6-cost-colab-20261022/`:

- `Face_PAD_Round6_Cost_E1_E3_E4.ipynb`: mở bằng Google Colab.
- `DeepFace-PAD-Round6-cost-source.zip`: upload khi cell 0.1 yêu cầu.

Source commit `d316f72ff2093fb336cc20c7a0e522cbda9363c6`; ZIP SHA-256
`ddef2dc1fbfb309c07b043f32dd82e8d8c5b6f109692bbd519caf337039598b9`.
Notebook SHA-256 `162819cc7b1b2557fe8fc7e7d240e7726d1c7d2794e15b5a1ec367def0f1ce7b`.
31 source file đã kiểm lock và ZIP; bản giải nén riêng đạt 20 CPU tests.
Bộ test repository tại commit đó: 186 passed, 1 skipped, 64 subtests passed.

## Bước hiện tại: setup và preflight

1. Trong Colab: Runtime → Change runtime type → chọn A100 GPU → Save.
2. File → Upload notebook → chọn notebook đo chi phí ở trên.
3. Chạy cell **0.1**. Đăng nhập/mount đúng Google Drive đang có thư mục
   `MyDrive/face-pad`. Khi hiện nút upload, chọn ZIP source đo chi phí.
4. Chạy cell **0.2**. Chờ dòng CPU tests `20 passed` và tên GPU A100.
5. Chạy cell **1.1**. Cell đọc đúng ba checkpoint và hai ảnh validation từ
   `MyDrive/face-pad/casia-fasd.zip`. Không cần upload lại dataset.
6. Gửi bảng params và nguyên khối **COST PREFLIGHT PASS**, kèm kết quả test.
   Giữ runtime đang kết nối. Chưa chạy **2.1** và chưa đổi `RUN_BENCHMARK`.

Nếu lỗi: dừng tại cell đó và gửi traceback, tên cell. Không Run all, không
xóa registration/timing/failure để thử chọn một kết quả nhanh hơn. Nếu Drive
thiếu file, gửi đúng tên đường dẫn báo thiếu; không đổi model hoặc split.

## Sau khi preflight được kiểm

Đây là bước tiếp theo, chưa mở cổng tại thời điểm phát hành hướng dẫn:

1. Đổi duy nhất `RUN_BENCHMARK = False` thành `True` trong cell **2.1**.
2. Chạy cell **2.1** một lần, giữ nguyên `BLOCK_ID = "a100-01"`.
3. Chờ đủ sáu vòng × ba model, mỗi model có 1.200 mẫu đo. Gửi bảng kết quả
   cùng dòng `COST COMPLETE` và đường dẫn output trên Drive.
4. File → Download → Download .ipynb, lưu bản đã chạy thành
   `notebooks/Face_PAD_Round6_Cost_E1_E3_E4_Executed.ipynb`, báo Codex đã lưu.
5. Chờ kiểm toán raw timing/hash trước khi chốt bảng latency. Không cần gửi
   toàn bộ 3.600 dòng timing trong chat; dữ liệu nằm trong `timings.csv`.

Output dự kiến:
`MyDrive/face-pad/reports/round6-cost-d316f72ff209/a100-01/` gồm
`registration.json`, `timings.csv`, `results.json` hoặc `failure.json` nếu lỗi.
Ghi nhận môi trường mới riêng với môi trường training cũ. Latency chỉ đo
forward float32 batch 1; decode, preprocess, chuyển GPU và ghi Drive ngoài
khoảng đo. Không quy đổi thành FPS webcam.
