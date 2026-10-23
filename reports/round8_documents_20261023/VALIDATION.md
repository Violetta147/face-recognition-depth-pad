# Xác minh tài liệu mới ngày 23 tháng 10 năm 2026

Hai bản mới dùng bằng chứng đến Lượt 7 và giữ nguyên các tài liệu lịch sử.
Không train, chấm checkpoint, thu webcam hoặc tạo slide mới.

## Giới hạn trang đã đo trong Microsoft Word

| Phần | Trang | Số trang | Giới hạn |
| --- | --- | --- | --- |
| Chương 1 Tổng quan nghiên cứu liên quan | 7–11 | 5 | 15 |
| Chương 2 Giải pháp và thiết kế thực nghiệm | 12–21 | 10 | 25 |
| Chương 3 Đánh giá kết quả | 22–32 | 11 | 20 |
| Ba chương và kết luận | 7–33 | 27 | 50 tổng phần chính |
| Kể cả tài liệu tham khảo | 7–34 | 28 | Vẫn dưới 50 |
| Toàn bộ báo cáo | 1–35 | 35 | Gồm cả phần đầu và phụ lục |
| Paper | 1–6 | 6 | Chưa có giới hạn riêng của nơi nộp |

Báo cáo có 19 bảng Word native, gồm bìa và phân công, sáu hình và năm công
thức native có chỉ số dưới/mũ. Paper có chín bảng native, hai hình và chỉ
có tóm tắt tiếng Việt. Từ khóa dùng thuật ngữ chuyên ngành đã thống nhất.

## Bằng chứng và số liệu

Seed 42 kế thừa JSON kiểm toán. Sáu lần E1/E3 seed 43–45 được kiểm độc lập
từ CSV đã lưu: 43.200 bản ghi frame, 2.160 bản ghi video trên cùng 360 video,
đúng nhãn và trung bình 20 frame/video. FA/FR, ACER và AUC khớp. p50/p95 từ
toàn bộ 3.600 timing cũng khớp. SOURCE_RECHECK.json ghi phép kiểm và hash.

Giữ seed 44, paired delta −0,6173 ± 2,6857 điểm phần trăm, khác biệt budget/
weight decay, sai khác CPU/CUDA và lỗi từ chối live. Webcam dùng audit cũ,
không được ghi thành phép đo mới hoặc benchmark độc lập. Thiếu cửa sổ thì
thiếu TTD, không điền 0. Các công trình khác protocol được trình bày riêng.

## Bố cục thực tế

Renderer đóng gói đã thử nhưng thiếu LibreOffice. Bản cuối dùng Word COM ẩn
để cập nhật TOC/PAGEREF và xuất PDF, rồi Poppler tạo PNG 110 dpi. QA cuối ở
artifacts/round8-documents-20261023/attempt06. PDF/PNG chỉ phục vụ kiểm tra.

Đã kiểm toàn bộ 35 trang báo cáo và sáu trang paper ở độ phân giải gốc.
Các trang không đổi được so pixel với bản đã xem; mọi trang đổi đều xem lại.
Không còn trang trắng, lỗi field, chữ/hình bị cắt hoặc chồng nhau, header
bảng đứng riêng. Cột paper trước hình đã cân lại; caption đi cùng hình/bảng;
tham khảo căn trái. Bảng 8 báo cáo sang trang có header lặp và dữ liệu.
DOCUMENTS_QA.json ghi hash, số trang và phạm vi xem lại.

Nội dung bảng trong Word sau lưu được đối chiếu với Markdown. Hash nguồn và
DOCX khớp provenance. Hai Word và hai Markdown lịch sử giữ nguyên hash.

## Kiểm thử và trạng thái

Bốn test tài liệu mới đạt. Bộ kiểm tra toàn repository có lượt thành công
218 passed, 1 skipped, 34 subtests passed; chốt lại trên toàn bộ tệp cuối
trước commit bàn giao. Test phần mềm không thay kiểm bố cục hoặc chứng nhận
PAD chính xác.

Log FAIL/STALE được giữ trong artifacts/project-hooks/validation. Một lượt
test launcher PowerShell mất khoảng 3,044 giây so với ngưỡng 3 giây; đã chạy
lại bộ kiểm tra thật và đạt, không sửa hoặc bỏ test đó.

Paper là bản thảo tiếng Việt theo bố cục tham chiếu IEEE conference, chưa
chọn nơi xuất bản. Chưa push, upload Drive, nộp bài hoặc xác nhận hai thành
viên đã luyện trình bày. Các bước này cần công việc riêng.
