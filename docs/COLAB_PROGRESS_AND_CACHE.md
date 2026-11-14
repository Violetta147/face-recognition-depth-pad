# Tiến độ và dữ liệu chuẩn bị trên Colab

Notebook OULU-NPU dùng `deepface_pad.progress.Progress` cho bước đọc
archive, crop, chép dữ liệu, kiểm hash, huấn luyện, validation và suy luận.
Mỗi bước in lúc bắt đầu và kết thúc. Khi chạy lâu, bộ đếm cập nhật khoảng
30 giây. ETA dùng tốc độ trung bình đã đo, nên có thể dao động. Khi số
đếm đứng lâu, log cho biết đã bao lâu chưa có thêm mục hoàn tất.

Các notebook sạch CASIA E1, Lượt 4, 5, 6, đo chi phí và xuất hình dùng cùng bộ chạy lệnh để in
stdout/stderr và lưu log trong `MyDrive/face-pad/notebook-logs`.
Với source ZIP lịch sử, tiến độ chi tiết vẫn phụ thuộc vào mã trong ZIP.
Notebook huấn luyện mới dùng `deepface_pad.train.run` sẽ có thêm số batch
Train/Dev trong từng epoch. Worker 3DDFA mới cũng báo số bản đồ đã thử
và duy trì hàng đợi để tiếp tục sau khi khôi phục.

## Lưu và khôi phục pseudo-depth

Dùng môi trường đã cài repo và một thư mục depth riêng nằm dưới data
root. Sau khi worker dừng hoặc xử lý xong một nhóm (ví dụ dùng
`--limit 500`), lưu snapshot từ một runtime Colab. Dùng cùng đường dẫn
data root khi khôi phục vì ledger chứa đường dẫn tuyệt đối.

```bash
python -m deepface_pad.colab_cache save \
  --root /content/deepface-pad-oulu/cache \
  --archive /content/drive/MyDrive/face-pad/oulu-fast-p1/prepared-cache/depth-run01.zip \
  --rgb-manifest /content/deepface-pad-oulu/cache/p1/train_dev.csv \
  --worker-metadata /content/deepface-pad-oulu/cache/depth/depth_status.csv.worker.json \
  --asset /content/3DDFA_V2/configs/mb1_120x120.yml \
  --asset /content/3DDFA_V2/weights/mb1_120x120.pth \
  --depth-dir /content/deepface-pad-oulu/cache/depth
```

Chọn đường dẫn thực tế theo thí nghiệm. Thêm `--asset` cho từng trọng số,
BFM và tệp cấu hình thực tế của backend, gồm các trọng số ONNX nếu dùng.
Snapshot chứa NPY, ledger, danh sách chờ và JSON metadata. Nếu manifest
depth đã materialize, có thể thêm `--derived-manifest` để lưu kèm sidecar
provenance. Cả hai tệp đó phải nằm trong data root.

Trong runtime mới, khôi phục RGB trước. Tạo lại các tệp cấu hình và
metadata worker từ cấu hình đã đăng ký, hoặc dùng bản metadata đã lưu
riêng sau khi đối chiếu worker hiện tại. Dùng lệnh trên với `restore`
thay cho `save` và bỏ `--depth-dir`. Mã so SHA-256 manifest RGB, nội dung
ảnh crop, metadata worker, backend, kích thước đầu ra và từng asset chỉ
định. Nếu khớp, nó xác minh hash từng mục khi khôi phục. Sau đó tiếp tục
worker từ ledger. Chạy bước materialize/preflight của repo trước khi train.
Chức năng này tiếp tục chuẩn bị dữ liệu. Việc tiếp tục optimizer sau khi
runtime ngắt là một luồng riêng.
