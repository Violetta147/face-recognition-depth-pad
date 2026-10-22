# Biên tập report và paper theo quy tắc học thuật

Biên bản của lần sửa trước. Sau yêu cầu xác nhận của người dùng, bảng phân
công đã được khôi phục trong report; xem
[KHOI_PHUC_PHAN_CONG_REPORT_2026-10-19.md](KHOI_PHUC_PHAN_CONG_REPORT_2026-10-19.md)
cho bản hiện tại.

Áp dụng `notes/Quy_tac_chuan_hoa_van_phong_va_loc_nhat_ky_AI.md` ngày
19/10/2026. Đây là ghi chú nội bộ của dự án, tách khỏi hai tài liệu nộp.

## Thay đổi nội dung

- Xóa khỏi hai bản Word các đường dẫn, mã băm, định danh lần chạy, tên tệp
  kiểm toán, lệnh terminal, lịch sử lỗi notebook và nhắc nhở tài nguyên.
- Xóa các lời tự nhắc của AI; chuyển quy tắc chọn trọng số, ngưỡng và cách
  tính chỉ số thành mô tả phương pháp khách quan.
- Chuẩn hóa cách gọi nhánh phân loại, trung bình không gian, bản đồ giả độ
  sâu và lịch trình huấn luyện. Phân biệt đơn vị khung hình, video, chủ thể.
- Trình bày bốn thiết lập của nhánh phân loại theo cùng một cấp độ; giải thích
  rõ đối chiếu quyết định trên từng video tương ứng.
- Bỏ bảng phân công khỏi report; bảng trách nhiệm vẫn còn nguyên trong
  `bao_cao_cuoi_ky/PHAN_CONG_HAI_THANH_VIEN.md`.
- Thay bảng tiến độ nội bộ bằng các thiết kế nghiên cứu dự kiến. Phụ lục
  report chỉ còn quy ước đánh giá, không chứa nhật ký hay hướng dẫn chạy mã.
- Đồng bộ Markdown và caption do builder tạo; đánh lại số 12 bảng có caption
  trong report. Giữ bảng tác giả/MSSV ở bìa.

## Bảo toàn kết quả và định dạng

Các giá trị trong bảng dữ liệu, cấu hình, ngưỡng, chỉ số test, MAE, đối chiếu
video và độ trễ giữ nguyên. Năm công thức của report giữ nguyên. Các kiểm tra
so sánh với mốc trước biên tập nằm trong `test_academic_manuscripts.py` và
`ACADEMIC_EDIT_INVARIANTS_2026-10-19.json`.

Chỉnh trực tiếp XML trên bản Word hiện có. Các phần Styles, thiết lập trang,
font, ảnh, quan hệ ảnh và header/footer được giữ nguyên byte; giữ thứ tự
chín ngắt trang của report và một ngắt cột của paper. Chú thích bảng paper
được rút gọn và đặt thuộc tính giữ cả đoạn cùng bảng, không xóa thẻ ngắt.

Mục lục và PAGEREF của report đã cập nhật trong Microsoft Word. Renderer
đóng gói thiếu LibreOffice nên dùng Word COM ẩn và Poppler để kiểm tra.
PDF/PNG chỉ phục vụ QA trong `artifacts/academic-edit-20261019/`.

## Trạng thái bản hiện tại

- Paper: 5 trang, tám bảng native, hai hình; tóm tắt Việt 187 từ, Anh 122 từ.
- Report: 23 trang, 12 bảng có caption cộng bảng bìa, bốn hình; vượt mục tiêu
  cũ 15–20 trang, chưa biên tập rút ngắn để đạt 20 trang.
- Giữ một seed 42, giao thức phát triển CASIA-FASD và lựa chọn E3 từ tập kiểm
  định. Không có huấn luyện, suy luận checkpoint hoặc kết quả mới.
- Đã kiểm tra toàn bộ trang; các trang không đổi được đối chiếu, trang thay
  đổi được xem lại. Không thấy mất chữ, ảnh, bảng hoặc lỗi field tham chiếu.
- 16 kiểm tra đạt: tám report/khung, năm paper và ba kiểm tra quy tắc/bảo toàn.

Mốc trước biên tập là `0e04b2e`; hai bản trước đó có thể lấy lại từ Git.
File Downloads của người dùng không bị chỉnh sửa. Chưa push hoặc nộp lên Drive.
