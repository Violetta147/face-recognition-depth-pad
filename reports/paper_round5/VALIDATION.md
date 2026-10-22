# Kiểm tra bản Word ngày 19 tháng 10 năm 2026

Bản kiểm tra: `Nhom1_Paper_CDCN_E0_E4_20261016.docx`.
Mục đích là bản thảo gửi giảng viên nhận xét, dựa trên kết quả đã có tới lượt 5.
Mẫu UD-JST là định dạng tham chiếu được lựa chọn; chưa xác nhận là một trong
hai mẫu của môn học. Bản này chưa được upload lên Drive.

## Bằng chứng và số liệu

- Bảng test và depth validation lấy từ hai báo cáo JSON đã kiểm tra trong
  repository. Toàn bộ sáu cấu hình dùng score CSV đã lưu để đối chiếu lại
  7.200 frame và 360 video mỗi cấu hình; nhãn, trung bình điểm theo video và
  chỉ số khớp artifact trong sai số 10⁻¹². Không train hoặc chấm checkpoint mới.
- E3 giữ lựa chọn từ validation. E4 không được chọn lại vì thứ hạng test.
- Chỉ báo kết quả seed 42 theo CASIA development protocol. Bài công khai
  việc test đã được quan sát nhiều lượt và khác biệt CUDA runtime lịch sử.
- Không thêm số liệu nhiều seed, khoảng tin cậy, benchmark độc lập, latency,
  webcam hoặc nhận diện danh tính chưa thực hiện.
- Hình pipeline là sơ đồ từ triển khai, không phải ảnh thí nghiệm tổng hợp.

## Kiểm tra tự động và bản dựng

Đã chạy bằng Python bundled của Codex:

```powershell
python -m unittest discover -s tests -p test_round5_paper.py -v
```

Kết quả: **5/5 test đạt**. Các test kiểm tra số liệu/bản dịch, độ dài abstract,
ô trống mẫu, bảng Word native, khổ giấy, section, căn lề trong ô và việc giữ
nguyên hash template cùng nội dung các phần font/theme/numbering/customXml.
XML được chuẩn hóa khi so để bỏ qua khác biệt dấu nháy ở declaration.
Tóm tắt Việt 187 từ, tiếng Anh 122 từ. Đã chuẩn hóa theo quy tắc học thuật và
loại nhật ký nội bộ; xem ghi chú BIEN_TAP_HOC_THUAT_2026-10-19.md trong reports/.

Renderer đóng gói không chạy được do máy thiếu LibreOffice. Đã dùng Microsoft
Word COM ở chế độ ẩn để xuất PDF kiểm tra, sau đó Poppler tạo PNG. Đây là
kiểm tra thực tế trong Word, không chỉ đọc cấu trúc XML.

- Số trang: **5**, trong giới hạn 6 trang của mẫu tham chiếu.
- Đã kiểm tra năm trang; các trang đổi được xem lại sau bổ sung số trang chẵn.
  PDF/PNG mới nằm trong `artifacts/academic-edit-20261019/`.
- Không phát hiện chữ/hình chồng nhau, nội dung bị cắt hoặc số xuống dòng trong ô.
- Bốn bảng chính và bốn bảng dịch đều chỉnh sửa được trong Word, không phải ảnh.
- Phụ lục tiếng Anh giữ cùng kích thước bảng/hình và số liệu với phần chính.
- Bản Word cuối và mã băm được lưu tại đây; PDF/PNG là tệp QA trong `artifacts/`.

## Những việc nhóm cần xác nhận trước nộp

1. Đọc bản Word và xác nhận tên, thứ tự tác giả, đơn vị và email liên hệ.
2. Nếu tìm lại được hai mẫu thầy gửi, ưu tiên mẫu môn học khi có khác biệt.
3. Hai thành viên kiểm tra lập luận, hiểu rõ kết quả âm tính và giới hạn.
4. Nộp file `.docx` vào đúng thư mục Article theo yêu cầu thầy; tạo file ở máy
   và commit nội bộ không đồng nghĩa đã nộp bài.

Không xóa `reports/bao_cao_cuoi_ky/`. Final report và paper là hai tài liệu
riêng; danh sách đề xuất dọn dẹp nằm trong báo cáo rà soát workspace.
