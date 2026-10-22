# Khung báo cáo cuối kỳ

**Cập nhật 16/10:** bản hoàn thiện nội dung đến lượt 5 là
`ban_thao/BAO_CAO_CUOI_KY.md` và
`ban_thao/Nhom1_Bao_cao_cuoi_ky_DeepFace_PAD_20261016.docx`.
Hướng dẫn dưới dành cho khung cũ giữ nguyên. Dựng bản mới bằng
`scripts/build_final_report_completed.py`, không dùng builder khung để ghi
đè bản hoàn thiện. Mở README và checklist hiện hành trước khi sửa tiếp.

Khung được tạo ngày 15/10/2026 theo yêu cầu 15–20 trang. Đây là bản cấu trúc có
hướng dẫn điền, bảng trống và vị trí chèn hình, chưa phải báo cáo đã hoàn thành.
Nội dung và số liệu thực nghiệm sẽ được bổ sung sau khi đối chiếu nguồn.

## File và cách sử dụng

- `ban_thao/BAO_CAO_CUOI_KY_KHUNG.docx`: bản Word editable, mục lục tự động.
- `ban_thao/BAO_CAO_CUOI_KY_KHUNG.md`: nguồn văn bản đồng bộ, chia thành 18 phần trang.
- Thay các đoạn trong ngoặc vuông bằng nội dung thật và cập nhật mục lục.
- Định dạng: A4, Times New Roman 13, giãn dòng 1,3; lề trái 3 cm, các lề còn lại
  2 cm. Bảng 11 pt, tiêu đề chương 16 pt, đề mục 14 pt.
- Phân công thực tế và giảng viên/lớp còn thiếu được để trống; không tự gán việc.

## Phân bổ dung lượng

| Trang dự kiến | Nội dung |
| --- | --- |
| 1 | Bìa |
| 2 | Tóm tắt và đóng góp thành viên |
| 3 | Mục lục, danh mục hình và bảng |
| 4–5 | Chương 1 Tổng quan bài toán và hướng nghiên cứu |
| 6–8 | Chương 2 Dữ liệu và quy trình xử lý |
| 9–12 | Chương 3 Phương pháp và triển khai |
| 13–16 | Chương 4 Thực nghiệm và đánh giá |
| 17 | Kết luận và hướng phát triển |
| 18 | Tài liệu tham khảo và phụ lục ngắn |

Phân bổ hiện tính cả bìa, mục lục, tài liệu tham khảo và phụ lục. Sau khi điền,
có thể điều chỉnh ngắt trang hoặc dành thêm tối đa hai trang cho nội dung cần
thiết để tổng báo cáo nằm trong 15–20 trang; không giữ khoảng trống chỉ để đủ số.

## Cơ sở chọn bố cục

Đây là mẫu làm việc của nhóm, không phải mẫu chính thức của giảng viên. Bố cục
tham khảo báo cáo MS-ILA của Hà Đức Kiên và Huỳnh Thảo Nhi, đồng thời đối chiếu
báo cáo phân loại rác nhóm 08 và phân loại lá cà chua nhóm 2, 22ES. Các tài liệu
được đọc để chọn cấu trúc; không kế thừa số liệu hay tuyên bố của các nhóm.

- MS-ILA: https://docs.google.com/document/d/1Fuhi_EfFILksT5ors5ozHrVD00XP1Xt_T9aG0Uf4kOk/edit
- Phân loại rác: https://docs.google.com/document/d/1Y-DU5vDne5D8tEVd9C3Bk6x7Vr43i5-b/edit
- Lá cà chua: https://docs.google.com/document/d/1IjgLqnh5n5-_XLmYxfqoG6pXLx5Qhz0U/edit

## Dựng và kiểm tra

Sử dụng Python do `load_workspace_dependencies` trả về:

```text
python scripts/build_final_report_scaffold.py reports/bao_cao_cuoi_ky/ban_thao/BAO_CAO_CUOI_KY_KHUNG.md artifacts/BAO_CAO_CUOI_KY_DUNG_LAI.docx
python -m unittest discover -s tests -p test_final_report_scaffold.py
```

Test kiểm tra đủ 18 phần trang, toàn bộ đề mục, 10 bảng editable, mục lục tự động,
placeholder số liệu, không có ảnh thực nghiệm và không có font theme/border ở
các style tiêu đề. Test dùng unittest vì runtime bundled không có pytest.
Sau khi gom thư mục, có thêm test kiểm tra các link trong README để tránh đường
dẫn cũ bị hỏng; tổng cộng 2 test đã chạy thành công.

Lệnh dựng xuất file riêng trong `artifacts/` để không ghi đè bản Word đang được
chỉnh thủ công. Chỉ cập nhật bản làm việc sau khi so sánh nội dung và phân trang.

Renderer LibreOffice của skill Documents không chạy được do bundle Windows
không có soffice.exe. Bản giao được mở bằng Microsoft Word COM ở chế độ ẩn,
cập nhật mục lục và xuất PDF; PDF được rasterize bằng Poppler bundled để xem
từng trang. PDF và ảnh QA nằm trong `artifacts/`, không phải file giao.

## Cập nhật sau Khối 1

Ngày 15/10 đã đối chiếu số liệu trong `BANG_BANG_CHUNG.md`, cập nhật riêng bảng
test 4.2, đoạn validation, epoch chọn và ghi chú nguồn vào Word/Markdown. Word
được sửa trên bản hiện có sau khi so nội dung với Markdown; không dựng đè từ
khung. Bản trước chỉnh sửa được giữ trong `artifacts/final-report-block1-qa/backups/`.
Kiểm thử khung: 2 test đạt; kiểm tra bổ sung xác nhận đoạn văn và 10 bảng khớp
giữa Word/Markdown, notebook gốc không thay đổi, tỷ lệ lỗi khớp mẫu số.

Renderer đóng gói vẫn thiếu `soffice.exe`; đã dùng Microsoft Word COM ẩn để
cập nhật mục lục và xuất PDF, rồi Poppler để xem đủ 18 trang. Bản thảo giữ 18
trang và chưa hoàn chỉnh ở các khối còn lại. Ảnh/PDF kiểm tra nằm trong
`artifacts/final-report-block1-qa/render/`, không phải bản nộp.
