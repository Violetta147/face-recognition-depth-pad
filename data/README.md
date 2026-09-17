# Kế hoạch dữ liệu PAD sơ bộ (Buổi 1)

Không commit video khuôn mặt hoặc ảnh enrollment vào Git. Dữ liệu được đặt ngoài
repository và đường dẫn được cung cấp bằng config/biến môi trường ở các buổi sau.

## So sánh lựa chọn

| Dataset | Quy mô và bối cảnh | Attack / protocol | Truy cập và giấy phép | Vai trò đề nghị |
|---|---|---|---|---|
| OULU-NPU | Trang dự án hiện mô tả 4.950 video real/attack, quay bằng camera trước của 6 điện thoại trong 3 phiên với điều kiện sáng/nền khác nhau. Bài báo gốc mô tả bản đầy đủ 5.940 video, 55 subjects. | Print và video replay; 4 protocol kiểm tra điều kiện, thiết bị và attack instrument chưa thấy. | Phải ký EULA; người ký cần vị trí thường trực tại tổ chức; không nhận email công cộng; không được phân phối lại. | **Phương án A / dataset chính**, nếu giảng viên hoặc trường ký được EULA. |
| Replay-Attack | 1.300 clip của 50 clients; webcam laptop 320×240, khoảng 25 fps; controlled và adverse lighting. | Print, mobile, high-definition; photo/video; hand/fixed support; train/devel/test/enroll tách subject. | Tải qua cổng dữ liệu Idiap và tuân thủ điều khoản hiển thị khi yêu cầu dữ liệu; không đưa dữ liệu vào repo. | **Phương án B**, nhỏ hơn và phù hợp để dựng baseline nhanh. |

Nguồn kiểm tra ngày 17-09-2026:

- [OULU-NPU official database page](https://sites.google.com/site/oulunpudatabase/)
- [OULU-NPU paper record at University of Oulu](https://oulurepo.oulu.fi/handle/10024/24331)
- [Replay-Attack official page at Idiap](https://www.idiap.ch/en/scientific-research/data/replayattack/index_html?set_language=en)

## Quyết định và hành động

1. Xin EULA OULU-NPU bằng email tổ chức ngay trong Buổi 1.
2. Trong lúc chờ, xin Replay-Attack và dùng official `grandtest` split để dựng loader.
3. Giữ nguyên split theo subject/video; tuyệt đối không tách frame ngẫu nhiên.
4. Lưu checksum manifest, không lưu raw frame webcam/enrollment theo mặc định.

