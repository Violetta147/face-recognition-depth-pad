# DeepFace-PAD

Nền móng cho hệ thống nhận diện khuôn mặt thời gian thực có Presentation Attack
Detection (PAD) bằng depth map. Phiên bản hiện tại hoàn thành **Buổi 1 (V0.1)** và
**Buổi 2 (V0.2)**: SCRFD face detection, ArcFace alignment/embedding, enrollment
nhiều frame, gallery cục bộ và nhận diện `UNKNOWN` bằng cosine threshold.

> Recognition ở V0.2 **chưa phải PAD** và vẫn có thể bị ảnh in/video replay đánh
> lừa. Các buổi sau phải đặt PAD trước bước recognition.

## Những gì đã hoàn thành

- Webcam hoặc video fallback; box, confidence, 5 landmarks, số mặt, FPS và latency.
- `q` giải phóng camera và đóng cửa sổ an toàn.
- Alignment theo template ArcFace về 112×112.
- Enrollment 15–30 frame (mặc định 20), lọc confidence/kích thước/độ mờ và không
  lưu raw frame.
- Template là trung bình các embedding đã L2-normalize; file gallery có model
  version, UTC enrollment time và sample count.
- Cosine matching và `UNKNOWN`; threshold nằm trong config và có công cụ chọn từ
  validation session riêng.
- Unit test không cần webcam, model hay mạng.
- [Kế hoạch dataset](data/README.md) cho OULU-NPU (A) và Replay-Attack (B).

Các ảnh chụp một mặt/nhiều mặt và bảng similarity thật phụ thuộc người/camera nên
không được giả lập trong repository. Lệnh demo và đánh giá bên dưới tạo các bằng
chứng đó trên máy nhóm.

## Cài đặt

Yêu cầu Python 3.11 hoặc 3.12. Dùng `uv` để tái lập môi trường:

```powershell
uv sync --extra runtime --extra dev
uv run python scripts/download_models.py
```

Script tải model pack `buffalo_s` chính thức của InsightFace. Model được lưu dưới
`artifacts/models/buffalo_s`, không commit vào Git. Bản nhỏ là mặc định để CPU
demo nhanh hơn; có thể tải `--pack buffalo_l` và đổi hai path trong config nếu cần
độ chính xác cao hơn. Với NVIDIA, cài
`onnxruntime-gpu` phù hợp máy rồi đổi `detector.device` thành `cuda`.

## Buổi 1 — detector demo

```powershell
uv run python scripts/run_webcam.py --detect-only
```

Video dự phòng dùng đúng pipeline:

```powershell
uv run python scripts/run_webcam.py --detect-only --source tests/fixtures/demo.mp4
```

Kiểm tra demo: một người, quay trái/phải, hai người, quan sát confidence/FPS, rồi
giữ chạy 5 phút. Repository không kèm video vì quyền riêng tư; nhóm tự thêm video
đã được đồng ý vào đường dẫn ignored `tests/fixtures/demo.mp4`.

Smoke test 5 phút không mở UI và không lưu frame:

```powershell
uv run python scripts/smoke_camera.py --duration 300
```

## Buổi 2 — enrollment và recognition

Đăng ký 20 mẫu hợp lệ (raw frame không được ghi xuống đĩa):

```powershell
uv run python scripts/enroll_face.py --person-id tv01 --name "Nguyen Van A"
```

Chạy recognition:

```powershell
uv run python scripts/run_webcam.py
```

UI hiển thị `NO_FACE`, `UNKNOWN`, hoặc tên người cùng raw similarity và latency.
Để đánh giá đúng, enrollment và validation phải quay ở hai phiên khác nhau.
Detector mặc định chạy mỗi 2 display frame (`interval_frames`) để UI CPU mượt hơn;
đặt về 1 khi benchmark độ trễ detector từng frame.

### Chọn threshold tạm thời

Tạo CSV từ validation riêng (không dùng test set):

```csv
score,is_genuine
0.71,true
0.66,true
0.28,false
0.35,false
```

Sau đó chạy:

```powershell
uv run python scripts/evaluate_recognition.py validation_scores.csv
```

Script ghi bảng vào `reports/tables/recognition_threshold.md`. Xem phân phối genuine
và impostor, rồi cập nhật `recognition.threshold` trong `configs/demo.yaml`. Giá trị
`0.47` ban đầu chỉ là điểm khởi đầu, không phải kết quả đã hiệu chỉnh.

## Kiểm thử

```powershell
uv run --extra dev pytest
```

Test xác nhận contract detector, alignment shape, L2 normalization, cùng embedding
có similarity gần 1, gallery round-trip, `UNKNOWN`, và threshold validation.

## Cấu hình và quyền riêng tư

Mọi camera index, model, device, gallery path, threshold và quality gate nằm tại
`configs/demo.yaml`; source không chứa đường dẫn máy cá nhân. Gallery chỉ chứa
embedding sinh trắc học và metadata, nhưng vẫn là dữ liệu nhạy cảm: chỉ lưu cục bộ,
kiểm soát truy cập và xóa khi không còn mục đích sử dụng. `privacy.save_frames` mặc
định là `false`.

## Giới hạn cần trình bày trung thực

- Kết quả FPS, nhận diện thành viên và 5 phút ổn định phải đo trên máy/camera thật.
- Model pack InsightFace có điều khoản sử dụng riêng; kiểm tra điều khoản trước
  mọi mục đích ngoài nghiên cứu/học tập.
- V0.2 cố ý chưa chặn ảnh in. Đây là động lực cho PAD ở Buổi 3 trở đi.
