# Biên bản hoàn thành Buổi 1 và Buổi 2

Ngày kiểm tra kỹ thuật: **17-09-2026**  
Phiên bản: **V0.2**

## Đã xác minh tự động

- [x] Dependency được khóa trong `uv.lock` trên Python 3.12.10.
- [x] SCRFD ONNX load và inference thành công trên CPU.
- [x] ArcFace ONNX trả embedding 512 chiều, L2 norm = 1.0.
- [x] 13/13 unit test pass.
- [x] CLI detector, enrollment và recognition parse được tham số.
- [x] Không có đường dẫn máy cá nhân trong config/source.
- [x] Gallery không lưu raw frame; có model version, UTC time và sample count.
- [x] Dataset A/B và quy trình xin quyền được ghi trong `data/README.md`.
- [x] Webcam stability test 300,3 giây: 6.566 frame, 6.501 face detections,
  21,86 effective FPS, 0 raw frame được lưu, không crash.

## Nghiệm thu Buổi 1 cần thực hiện với camera

- [x] Chạy liên tục 5 phút không crash (đã đo 300,3 giây ngày 17-09-2026).
- [ ] Chụp một ảnh có một mặt và một ảnh có nhiều mặt (có đồng ý của người tham gia).
- [ ] Ghi FPS của đúng máy demo và kiểm tra tất cả thành viên ở điều kiện phòng học.

Lệnh: `uv run python scripts/run_webcam.py --detect-only`

## Nghiệm thu Buổi 2 cần thực hiện với người tham gia

- [ ] Enrollment mỗi thành viên ở phiên 1 (15–30 frame).
- [ ] Validation ở phiên 2; thu genuine/impostor scores.
- [ ] Chọn threshold từ validation và cập nhật `configs/demo.yaml`.
- [ ] Xác nhận người đã đăng ký nhận đúng và người ngoài gallery là `UNKNOWN` trong phần lớn thử nghiệm.
- [ ] Trình diễn ảnh in có thể đánh lừa recognition thuần túy (chỉ khi có đồng ý sử dụng ảnh).

Lệnh enrollment:
`uv run python scripts/enroll_face.py --person-id tv01 --name "Nguyen Van A"`

Lệnh recognition: `uv run python scripts/run_webcam.py`

Không đánh dấu các mục phụ thuộc người/camera ở trên trước khi thực sự quay và đo.
