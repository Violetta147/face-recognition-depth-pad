# Báo cáo cuối kỳ DeepFace PAD

Cập nhật ngày 19/10/2026: đã biên tập lại theo quy tắc học thuật người dùng
cung cấp, loại nhật ký vận hành và chuẩn hóa thuật ngữ. Xem
[ghi chú biên tập](../BIEN_TAP_HOC_THUAT_2026-10-19.md). Bản hiện tại 24 trang,
dài hơn mục tiêu cũ 15–20 trang; chưa rút lại nội dung để đạt 20 trang.
Đã hoàn thiện
nội dung báo cáo học phần với bằng chứng đến lượt 5, gồm E0, Official E1, E2,
E3, E3b và E4 ở seed 42. Bản hiện tại dùng khung A4 một cột đã chốt; paper là
tài liệu riêng, không thay final report.

## File đang dùng

| File | Vai trò |
| --- | --- |
| [Báo cáo Word](ban_thao/Nhom1_Bao_cao_cuoi_ky_DeepFace_PAD_20261016.docx) | Bản đọc và gửi giảng viên nhận xét |
| [Nguồn Markdown](ban_thao/BAO_CAO_CUOI_KY.md) | Nội dung hoàn chỉnh, bảng thật và hình có nguồn |
| [Checklist hiện tại](KE_HOACH_HOAN_THANH.md) | Các khối đã soạn/kiểm tra và phần còn chờ nhóm |
| [Phân công hai thành viên](PHAN_CONG_HAI_THANH_VIEN.md) | Chia trách nhiệm đề xuất theo tám lượt |
| [Bảng bằng chứng](BANG_BANG_CHUNG.md) | Lịch sử khóa nguồn và cập nhật kiểm toán lượt 5 |
| [Danh mục nguồn](nguon/DANH_MUC_NGUON.md) | Notebook, config, JSON, hình và thông tin bìa |
| [Kiểm tra bản hoàn thiện](KIEM_TRA_BAN_HOAN_THIEN.md) | Test, render và giới hạn bàn giao |
| [Khung cũ](ban_thao/BAO_CAO_CUOI_KY_KHUNG.docx) | Bản gốc giữ nguyên để đối chiếu |

Khoa Công nghệ thông tin; giảng viên TS. Huỳnh Hữu Hưng; lớp học phần
1021673.2610.23.14. Khoa/lớp do người dùng xác nhận; tên/học vị giảng viên được
đọc từ https://scv.udn.vn/hhhung. Bảng phân công trách nhiệm nằm sau bìa, trước tóm tắt để phục vụ đánh giá
học phần. Bảng mô tả trách nhiệm chuyên môn và công việc phối hợp, không chia
theo lượt. Kế hoạch chi tiết vẫn được giữ ở tài liệu riêng. Xem
[ghi chú khôi phục](../KHOI_PHUC_PHAN_CONG_REPORT_2026-10-19.md).

## Dựng và kiểm tra

Dùng Python bundled được workspace dependency loader cung cấp:

```powershell
python scripts/build_final_report_completed.py
python -m unittest discover -s tests -p test_final_report_completed.py -v
```

Builder đọc Markdown hoàn chỉnh, dùng khung Word giữ nguyên làm tham chiếu và
ghi ra file mới. Builder cũ build_final_report_scaffold.py chỉ dành cho khung.
Nội dung Word sửa văn phong đã được đồng bộ sang Markdown. Các nhãn PAGE là
20 khối nội dung lịch sử, không phải số trang bản mới; builder cho nội dung
chảy liên tục trong từng chương. Không sửa Word rồi bỏ qua đồng bộ. Sau khi
dựng, mở Word, cập nhật toàn bộ field/mục lục bằng Ctrl+A, F9 và lưu trước khi
kiểm tra phân trang.

Ảnh notebook trong hinh_anh/notebook/ là bản tham chiếu cục bộ bị Git ignore.
Sơ đồ pipeline trong hinh_anh/hoan_thien/ được dựng từ code. Khi clone trên
máy mới, lấy lại đúng ảnh có hash trong REPORT_PROVENANCE.json; không thay
bằng ảnh hoặc số minh họa. Renderer đóng gói thiếu LibreOffice trên máy này;
Word COM ẩn và Poppler được dùng để kiểm tra PDF/PNG trong artifacts/.
Ảnh/PDF QA không thay yêu cầu nộp Word. Provenance ghi hash sau cập nhật field.

## Phạm vi bàn giao

Đã soạn các phần với kết quả hiện có, giữ kết quả âm tính và chọn E3 từ
validation. Lượt 6 nhiều seed, benchmark chi phí mới, ảnh lỗi test, webcam và
nhận diện danh tính chưa được biến thành kết quả đã làm. Các mục này nằm
trong hướng phát triển. Paper nằm riêng ở reports/paper_round5/.

Hai thành viên cần đọc, kiểm tra nội dung thuộc trách nhiệm của mình và luyện
giải thích. File mới chưa upload lên Drive. Không push Git hoặc chạy GPU mới
trong công việc hoàn thiện báo cáo này.
