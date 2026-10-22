# Bài báo nghiên cứu sau lượt 5

Cập nhật 19/10/2026: đã biên tập theo quy tắc chuẩn hóa học thuật và loại nhật
ký nội bộ người dùng cung cấp; nguồn `PAPER.md` được đồng bộ. Bản hiện tại
vẫn 5 trang. Xem [ghi chú biên tập](../BIEN_TAP_HOC_THUAT_2026-10-19.md).
Mốc trước biên tập là `0e04b2e`; bản gốc trước khi nhận văn phong vẫn có tại
`bb9d38a`. Caption trong builder được đồng bộ và giữ liền bảng khi sang trang.

`PAPER.md` là nguồn nội dung. Comment `table:*` được builder điền thành bảng
Word editable từ audit JSON; không phải ô trống trong bản nộp. Bản Word là
`Nhom1_Paper_CDCN_E0_E4_20261016.docx`. File không được upload tự động.

Đọc `FORMAT_AND_CHECKLIST.md` cho mẫu chính thức đã tìm và các điểm cần xác
nhận trước nộp. Bản này phục vụ thầy nhận xét, chưa phải tuyên bố bài đã đạt
mọi điều kiện đăng tạp chí hoặc nghiên cứu đã hoàn tất lượt 6–8.

Builder giữ bản gốc template UD-JST trong `artifacts/workspace-audit-20261016/`
và thay nội dung minh họa trên bản sao. Dùng Python bundled do workspace
dependency loader cung cấp để chạy `scripts/build_round5_paper.py`.
Định dạng tham khảo: khổ 19 × 26,5 cm, lề 1 cm, TNR 10, hai cột và khối
đầu và hình một cột, bảng phụ lục hai cột. Không giữ ISSN/VOL/NO giả trong bản sinh viên.

Sơ đồ pipeline được dựng lại bằng code từ các module đã triển khai, dùng nhãn
tiếng Anh và caption Việt/Anh; không phải ảnh thí nghiệm hoặc số liệu mới.
Bảng và hình phụ lục giữ cùng kích thước với phần tiếng Việt. Email liên hệ, thứ tự
tác giả và mẫu cụ thể của môn cần nhóm xác nhận; không điền thông tin giả.

Chạy kiểm tra: `python -m unittest discover -s tests -p test_round5_paper.py`.
Renderer đóng gói thiếu LibreOffice trên máy Windows này; Word COM ẩn và
Poppler được dùng để kiểm tra thực tế. Ảnh/PDF QA ở `artifacts/`, không phải
file cần nộp thay bản Word.

Trên checkout mới, cần tải mẫu Word từ đường dẫn chính thức trong checklist
về `artifacts/workspace-audit-20261016/Template_UD_JST_original.docx` trước
khi build. Mã SHA-256 của bản đã dùng được ghi trong `paper_provenance.json`;
không tự thay template khác rồi coi đó là cùng phiên bản. Bản Word cuối và
provenance được lưu cùng source trong Git; ảnh QA có thể tạo lại.
