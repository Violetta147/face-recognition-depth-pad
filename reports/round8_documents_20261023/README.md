# Báo cáo và paper mới ngày 23 tháng 10 năm 2026

Gói mới theo yêu cầu phiên này. Các file báo cáo, paper và builder lịch sử
không bị sửa. Nguồn đọc: báo cáo/paper đến Lượt 5, kết quả và chi phí Lượt 6,
đối chiếu protocol, phân tích lỗi và các lượt webcam đã đo ở Lượt 7.

- `BAO_CAO.md`: báo cáo tiếng Việt có đúng ba chương. Giới hạn tổng phần
  chính 50 trang; chương 1 tối đa 15, chương 2 tối đa 25, chương 3 tối đa 20.
  Kiểm cả tổng và từng chương trên bản Word render, không cộng 15+25+20.
- `PAPER.md`: paper tiếng Việt, tóm tắt tiếng Việt; bố cục bài nghiên cứu với
  giới thiệu, liên quan, phương pháp, thiết lập, kết quả, thảo luận và kết luận.
  Định dạng tham chiếu IEEE conference A4 hai cột, 10 pt; chưa chọn nơi nộp.
- `assets/`: sáu hình sao chép nguyên byte từ các nguồn hiện có.
- `TABLES_NEW.json`: các bảng kết quả mới từ JSON bằng chứng đã khóa.

Builder mới `scripts/build_round8_documents.py` chỉ dựng tài liệu, không gọi
model, train, chấm lại tập dữ liệu hoặc webcam. Dùng Python bundled do Codex
cung cấp để chạy builder và `python -m unittest discover -s tests -p
test_round8_documents.py -v`. File `.provenance.json` truy nguồn từng đầu vào.
Kiểm nội dung không xác nhận bố cục; xem `VALIDATION.md` khi render hoàn tất.

Nguồn định dạng chính thức: [IEEE Author Center](https://conferences.ieeeauthorcenter.ieee.org/write-your-paper/authoring-tools-and-templates/)
và [trang mẫu IEEE CAI](https://cai.ieee.org/2025/manuscript-templates-for-conference-proceedings/).
Đường tải DOCX canonical trả HTTP 202 với nội dung rỗng; các mirror thử đọc
trả HTTP 406. Bản này dựng theo bố cục tham chiếu, không tuyên bố đã dùng
nguyên template chính thức hoặc đã đạt quy định của một nơi xuất bản.
Tiếng Việt và bộ từ khóa chuyên ngành là lựa chọn người dùng, cần điều chỉnh nếu
nơi nộp sau này có yêu cầu ngôn ngữ khác.

Phiên này chỉ tạo tài liệu theo bằng chứng hiện có. Các bước đo webcam còn
thiếu, slide, luyện trình bày, train mới, push và nộp bài nằm ngoài phạm vi.

## Bản mới đã kiểm tra

| Tệp | Vai trò |
| --- | --- |
| [Báo cáo Word](Nhom1_Bao_cao_DeepFace_PAD_20261023.docx) | 35 trang; ba chương 5/10/11 trang, phần chính kể cả kết luận 27 trang |
| [Paper Word](Nhom1_Paper_CDCN_IEEE_VI_20261023.docx) | Sáu trang; tiếng Việt, không có abstract tiếng Anh, từ khóa chuyên ngành |
| [Nguồn báo cáo](BAO_CAO.md) và [nguồn paper](PAPER.md) | Nội dung chỉnh sửa được |
| [Biên bản xác minh](VALIDATION.md) | Giới hạn trang, kiểm nội dung, bố cục và trạng thái nộp |
| [Danh mục nguồn](SOURCES.md) | Nối bảng/hình với bằng chứng |
| [Kiểm CSV hiện tại](SOURCE_RECHECK.json) | Hash và số học từ score/timing đã lưu |
| [Kiểm Word](DOCUMENTS_QA.json) | Hash sau cập nhật field, số trang và phạm vi rà |

Khi sửa nguồn, chạy builder, chờ dựng xong, render bằng
scripts/render_round8_documents.ps1 với tên attemptNN mới rồi kiểm lại trang
đổi. Chờ render và commit kết thúc trước sửa tiếp để receipt kiểm thử gắn
đúng một trạng thái tệp. Builder mới chỉ trỏ output vào gói này.
