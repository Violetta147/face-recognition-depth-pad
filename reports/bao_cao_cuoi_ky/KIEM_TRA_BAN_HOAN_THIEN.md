# Kiểm tra bản report sau biên tập học thuật ngày 19 tháng 10 năm 2026

Bản hiện tại: `ban_thao/Nhom1_Bao_cao_cuoi_ky_DeepFace_PAD_20261016.docx`.
Đã áp dụng quy tắc người dùng trong `notes/Quy_tac_chuan_hoa_van_phong_va_loc_nhat_ky_AI.md`.

## Nội dung

- Giữ kết quả một seed 42 trên giao thức phát triển CASIA-FASD. E1/E2 đạt
  ACER 2,7778%; E3/E3b 5,0000%; E4 4,4444%. E3 là cấu hình chọn từ validation.
- Giữ các giá trị dữ liệu, siêu tham số, số tham số, ngưỡng, paired counts,
  MAE, latency và năm công thức. Kiểm tra số liệu vẫn đối chiếu audit JSON.
- Nội dung nộp không còn đường dẫn, hash, run ID, tên tệp kiểm toán, lệnh CLI,
  ghi chú lỗi notebook hoặc nhắc nhở ngân sách GPU.
- Các thuật ngữ về nhánh phân loại, lịch trình huấn luyện và đối chiếu kết quả
  trên từng video được viết rõ theo ngữ cảnh.
- Bảng phân công trách nhiệm nằm sau bìa, trước tóm tắt. Phụ lục chỉ
  trình bày quy ước đánh giá; bảng hướng phát triển nêu thiết kế nghiên cứu.
- Không có kết quả nhiều seed, webcam, nhận diện danh tính hoặc huấn luyện mới.

## Word

- Bản hiện tại 24 trang A4, vẫn vượt mục tiêu cũ 15–20 trang; chưa rút nội dung
  để đạt 20 trang. Có 12 bảng có caption, cộng bảng bìa và bảng phân công, và bốn hình.
- Chỉnh trực tiếp trên XML Word hiện có. Giữ nguyên byte các phần Styles,
  font, thiết lập trang, ảnh, quan hệ ảnh và header/footer. Chín thẻ ngắt
  trang cũ được giữ; thêm một ngắt trang cho phần phân công.
- Mục lục, danh mục và PAGEREF đã cập nhật trong Microsoft Word.
- Đã xem các trang và đối chiếu các trang không đổi; không thấy lỗi cắt chữ,
  mất hình, mất bảng, lỗi field hoặc tiêu đề đứng riêng cuối trang.
- Renderer đóng gói thiếu LibreOffice; QA dùng Word COM ẩn và Poppler.
  PDF/PNG ở `artifacts/restore-allocation-20261019/`, không phải file nộp.
- Markdown khớp toàn bộ 14 bảng và nội dung đoạn văn của Word, trừ phần kết
  quả field do Word cập nhật tự động.

## Kiểm tra và phiên bản

Tám kiểm tra report/khung, năm kiểm tra paper và ba kiểm tra biên tập học
thuật đạt: tổng cộng 16 kiểm tra. Có kiểm tra cả nội dung Word hiện tại,
nguyên vẹn số liệu/công thức và việc giữ Styles/ngắt trang/ảnh.

Xem `../BIEN_TAP_HOC_THUAT_2026-10-19.md` và
`../ACADEMIC_EDIT_INVARIANTS_2026-10-19.json` để đọc phạm vi và mốc đối chiếu.
Bản trước biên tập được giữ tại commit `0e04b2e`. Chưa push hoặc nộp Drive.

Yêu cầu khôi phục phân công và phạm vi bảo toàn được ghi tại
`../KHOI_PHUC_PHAN_CONG_REPORT_2026-10-19.md`. Paper giữ nguyên.
