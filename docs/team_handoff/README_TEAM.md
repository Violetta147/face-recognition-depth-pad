# DeepFace-PAD

Dự án nghiên cứu dùng Official CDCN và bộ phân loại từ bản đồ độ sâu để phân
biệt mặt thật, ảnh in và video phát lại. Dữ liệu đang dùng là CASIA-FASD với
split theo người của dự án. Đây là kết quả CASIA development, không dùng để
xếp hạng trực tiếp với paper có protocol khác.

## Bắt đầu trên máy mới

1. Pull main nếu đã có clone; nếu chưa có, clone repository.
2. Đọc [trạng thái và việc còn lại](docs/PROJECT_STATUS.md).
3. Làm theo [thiết lập máy mới](docs/SETUP.md).
4. Xem [dữ liệu và video ngoài Git](docs/DATA_ASSETS.md) nếu công việc cần chúng.

Repository mô tả dự án và đủ ngữ cảnh để làm tiếp. Không cần lịch sử chat.

## Đã có

- Mã nguồn: src/deepface_pad/, scripts/, configs/, tests/.
- Checkpoint, threshold, score của 12 lượt chạy chính: evidence/face-pad/runs/.
- Manifest nguồn và manifest depth: data/manifests/.
- Kết quả, hình, Word, paper và slide: reports/.
- Bằng chứng số Lượt 6–7: các thư mục đã chọn trong artifacts/.
- Danh mục tệp và SHA-256: delivery/FILES.json.

Lượt 6 đã có sáu model, 138 epoch và ba cặp seed E1/E3. E3 chỉ tốt hơn ở 2/3
seed. Lượt 7 đã có phân tích lỗi, 20 panel, median window và FPS/TTD thực đo.
Demo còn từ chối live, thiếu print và chưa kiểm quay lại đủ cửa sổ.
Word/paper/slide hiện tại chỉ đến Lượt 5. Phần còn lại là hoàn tất Lượt 7–8
theo kế hoạch; không có yêu cầu train mới.

Đọc các tài liệu trên trước. Chỉ mở báo cáo hoặc notebook lịch sử liên quan
đến việc đang làm. Chúng là bằng chứng của từng thời điểm, không phải lệnh
chạy lại các lượt đã hoàn tất. Không đưa chat hoặc bản xuất chat vào repository.
