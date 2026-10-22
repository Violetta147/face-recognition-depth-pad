# Phiếu đăng ký thí nghiệm mới

Sao chép mẫu này thành tài liệu mới. Điền các mục trước khi chạy.
Một mục chưa điền nghĩa là chưa được chốt; không tự coi là đã hoàn tất.

| Mục | Giá trị cần điền |
| --- | --- |
| ID | Mã mới, không trùng run đã có. |
| Câu hỏi | Một câu hỏi đo được. |
| Giả thuyết | Hướng thay đổi và điều kiện bác bỏ. |
| Đối chứng | Model, checkpoint và hash. |
| Biến thay đổi | Một thay đổi chính; liệt kê thay đổi phụ không tránh được. |
| Dữ liệu | Nguồn, quyền truy cập, hash, đơn vị và mẫu số. |
| Split | Quy tắc chia người/video và chống leakage. |
| Phạm vi test cũ | Tập nào đã được quan sát; không gọi lại là test độc lập. |
| Calibration | Tập chọn threshold; tách tập đánh giá. |
| Seed | Danh sách chốt trước; giữ cả seed bất lợi. |
| Train | Epoch, batch, LR, optimizer, weight decay và augmentation. |
| Chọn checkpoint | Metric validation, tie-break và thời điểm khóa. |
| Metric chính | Công thức, đơn vị và đơn vị tổng hợp. |
| Metric phụ | Định nghĩa, giới hạn diễn giải. |
| Thiết bị | CPU/GPU/camera, phiên bản và precision. |
| Budget | Tài nguyên, thời lượng tối đa và người duyệt. |
| Điều kiện dừng | Hết budget, lỗi hash, thiếu dữ liệu hoặc lỗi protocol. |
| Output | Config, code commit, log, checkpoint, score, figures, receipt và thất bại. |
| Người thực hiện | Tên và trách nhiệm. |
| Người kiểm | Tên và hạng mục rà soát. |

Đối với webcam, bổ sung detector, crop, track reset, window, warm-up, thời
điểm bắt đầu đo, cách tính FPS/TTD và nhãn cảnh. Đối với speed, ghi rõ phần
pipeline được đo. Đối với kiến trúc, giữ đối chứng và budget đủ để giải thích
chênh lệch. Khi không cô lập được biến, ghi đúng giới hạn đó.

Sau khi chạy, thêm bảng kết quả thực tế. Dẫn file nguồn cho từng con số.
Giữ kết quả âm tính. Nếu sửa kế hoạch, tạo revision và ghi thời điểm sửa so
với thời điểm xem validation/test. Không sửa bản đăng ký cũ như chưa từng đổi.
