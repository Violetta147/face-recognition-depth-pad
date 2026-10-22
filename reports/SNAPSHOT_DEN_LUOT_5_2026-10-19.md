# Lưu trạng thái dự án đến lượt 5 trước khi nhận bản Word sửa văn phong

Ngày kiểm tra: 19/10/2026. Phạm vi là các tài liệu, notebook và sản phẩm đã có
trong workspace; không chạy thêm thí nghiệm, suy luận checkpoint hoặc chấm test.

## Hai bản gốc được giữ trong Git trước khi thay thế

| Tài liệu | Đường dẫn | SHA-256 trước thay thế |
| --- | --- | --- |
| Paper | `reports/paper_round5/Nhom1_Paper_CDCN_E0_E4_20261016.docx` | `699aed26bb58f645489f7b8b4fe7f7954b21f85f26e1a1e8858cb49b60fbc0bb` |
| Report | `reports/bao_cao_cuoi_ky/ban_thao/Nhom1_Bao_cao_cuoi_ky_DeepFace_PAD_20261016.docx` | `9458e236032c0dad7be267fadd8bc01b68e3abc987a387af6f331530bbf838c6` |

Hai file gốc đã có tại commit `c881de5` (paper được tạo từ `aba532d`). Commit
chứa ghi chú này cũng giữ nguyên hai file trước khi nhận bản sửa của người dùng.

## Công việc còn lại được lưu cùng đợt

- Notebook Official E1 có output lịch sử và các cell khắc phục lỗi. Có một
  `CalledProcessError` còn lưu ở bước materialize; giữ nguyên bằng chứng này.
  Không coi notebook đã chạy thẳng từ đầu đến cuối trên phiên hiện tại.
- Notebook Round 4 lưu thêm output; nguồn của 18 cell không đổi so với HEAD.
- Slide Markdown, PowerPoint đã xuất, template DUT, sơ đồ kiến trúc và hướng
  dẫn Marp là sản phẩm phục vụ trình bày đến lượt 5.
- [2003.04092v1.pdf](../references/papers/2003.04092v1.pdf) là tài liệu tham khảo có sẵn, đã chuyển từ root ngày 21/10; `notes/` là câu hỏi học tập,
  không phải kết quả nghiên cứu hoặc bằng chứng đã chạy lượt 6–8.
- Những thay đổi chỉ về kết thúc dòng trong kế hoạch và khung báo cáo cũng
  được đưa vào đợt lưu nếu Git ghi nhận thay đổi.

`.obsidian/` là cấu hình giao diện, trạng thái cửa sổ và mã plugin cài tại máy;
được giữ trên đĩa và bỏ qua trong Git. `artifacts/`, dataset, cache và trọng số
tiếp tục theo quy tắc ignore đã có; không tuyên bố Git chứa toàn bộ dữ liệu Drive.

## Kiểm tra trước commit

- Cú pháp các cell Python của hai notebook lịch sử đọc được; đây không phải
  kiểm chứng thực thi trên Colab/GPU.
- Bảy kiểm tra `test_marp_report.py` đạt, gồm số liệu, nguồn hình, template,
  cấu trúc 22 slide và tính tương thích nội dung với PowerPoint.
- Giữ nguyên kết quả âm tính: E1/E2 ACER 2,7778%; E3/E3b 5,0000%; E4 4,4444%.
  E3 vẫn là ứng viên chọn từ validation; lượt 6–8 chưa hoàn thành.
