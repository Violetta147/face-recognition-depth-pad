# Kiểm tra bản trình chiếu ngày 16/10/2026

- Marp CLI 4.5.1, Marp Core 4.4.0; nội dung Unicode tiếng Việt, 16:9.
- 22 trang: 18 trang chính và 4 trang phụ lục; 12 hình không trùng lặp, giữ
  nguyên byte từ nguồn. Ba nền DUT lấy từ bản sao template, giữ logo/artwork.
- 7 kiểm thử nguồn đạt: Markdown không phụ thuộc HTML, số trang, ảnh/provenance, ACER, selection BCE, depth
  MAE, giới hạn hiển thị và thao tác làm sạch bản sao template.
- Bản HTML có đủ ảnh; kiểm tra DOM 22 trang không có phần tử ra ngoài slide
  hoặc chú thích chồng lên nội dung. Asset nằm cạnh HTML để chuyển máy được.
- Đã render PDF và xem toàn bộ 22 trang; không thấy chữ tràn, ảnh thiếu hoặc
  nội dung che logo. Chi tiết của hai sơ đồ kiến trúc nên xem phóng to trong
  PDF khi cần đọc từng lớp; phần trình bày chính tập trung vào luồng và head.
- PowerPoint mở thành công PPTX 22 trang; đã đối chiếu trang 1/10/14/18/22
  với PDF. PPTX có đủ 22 speaker notes, các slide xuất thành ảnh theo Marp.
- Chưa kiểm tra giao diện plugin Marp Slides trong Obsidian trên máy người dùng.
- E3 giữ lựa chọn validation; E1/E2 ACER 2,7778%, E3/E3b 5%, E4 4,4444%.
  Không có kết quả nhiều seed, webcam hoặc latency GPU mới trong deck.

Nhật ký render, audit bố cục và ảnh preview cục bộ nằm trong
`artifacts/marp-report-20261016/` (không đưa vào Git).

## Sửa lỗi xuất PowerPoint hiện thẻ HTML

Đã xác nhận bản người dùng xuất hiện nguyên văn `<div class="note">` ở slide 2.
Chuyển note sang blockquote Markdown, takeaway sang paragraph, bold sang `**`;
bỏ HTML trong nội dung. Xuất lại không có cờ `--html` vẫn hiển thị đúng.
Bản sửa dùng nội dung người dùng vừa cập nhật; không ghi đè PPTX đang mở.
Đầu ra: `exports/Bao_cao_DeepFace_PAD_Khong_HTML.pptx`.
