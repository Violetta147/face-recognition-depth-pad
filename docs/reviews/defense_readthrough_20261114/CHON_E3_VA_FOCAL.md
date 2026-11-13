# Chọn E3 và đánh giá Focal Loss

<strong style="background-color:#DDF7E9;color:#0B6B45;padding:1px 4px;border-radius:3px;">Có thể đo BCE trên mô hình học bằng Focal.</strong> Với hai nhãn live và spoof, BCE đo mức độ phù hợp giữa điểm dự đoán và nhãn thật. Focal thay đổi mức đóng góp của mẫu dễ và khó **trong lúc cập nhật trọng số**. Tính BCE trên tập kiểm định không làm thay đổi các trọng số đã học. Tuy nhiên, **dùng BCE để chọn checkpoint** quyết định bộ trọng số nào được giữ lại, nên có thể ảnh hưởng đến lợi ích của Focal mà phép đánh giá quan sát được. BCE cấp khung hình và tỷ lệ lỗi ở một ngưỡng cấp video đo hai thuộc tính khác nhau.

| Bước | Cách nhóm đã làm |
| --- | --- |
| Huấn luyện | E3 và E3b dùng BCE cho phân loại, E4 dùng Focal. Khi huấn luyện joint, mạng dự đoán độ sâu và bộ phân loại cùng được cập nhật. |
| Chọn checkpoint | Ở giai đoạn head/joint, dùng BCE cấp khung hình trên validation cho cả ba cấu hình. Giai đoạn chỉ học độ sâu dùng loss độ sâu. |
| Chọn ngưỡng | Với checkpoint đã chọn, lấy ngưỡng tối thiểu hóa ACER cấp video trên validation. Quy tắc xử lý hòa và tập ngưỡng ứng viên được ghi trong hồ sơ kỹ thuật. |
| Chọn cấu hình đi tiếp | E3/E3b/E4 cùng đạt ACER 0%, EER 0% và AUC 1 trên validation. E3 đi tiếp do BCE thấp hơn theo quy tắc phân định đã định trước. |

Chọn E3 để chạy nhiều seed có căn cứ theo quy tắc lịch sử. Muốn đánh giá Focal có giúp giảm lỗi PAD hay không, cặp phù hợp là **E3b–E4**, hai cấu hình dùng cùng lịch huấn luyện theo giai đoạn. Trên E4, epoch 3 của joint có tổng loss validation thấp nhất, còn epoch 6 có BCE validation thấp nhất. Chênh lệch đó cho thấy hai tiêu chí chọn thời điểm khác nhau. Muốn biết tác động đến PAD cần điểm video hoặc checkpoint của các epoch liên quan. [Hồ sơ kiểm toán BCE–Focal](../fair_comparison_20261030/KET_QUA.md) · [Validation Lượt 5](../../../reports/ROUND_5_FULL_VALIDATION_2026-10-16.md).

## Việc tiếp theo

1. Các thư mục run đã kiểm chỉ có checkpoint tốt nhất theo stage. Kiểm tra bản lưu khác nếu có. Nếu vẫn thiếu checkpoint hoặc điểm validation theo epoch, chuẩn bị cặp chạy Colab cùng một seed và lưu đủ hai loại đầu ra. Thay lựa chọn cuối head có thể đổi điểm khởi tạo joint, nên nhánh đó phải huấn luyện joint từ checkpoint mới.
2. Chốt tiêu chí PAD, cách phân định khi hòa và quy tắc ngưỡng trước khi chạy. Giữ chung dữ liệu, seed, thứ tự mẫu, tăng cường dữ liệu, checkpoint khởi tạo E1, lịch và cấu hình Adam. Ghi alpha/gamma và cách ghép loss của Focal. So BCE với Focal dưới cùng tiêu chí chọn checkpoint. Nếu kiểm ảnh hưởng của tiêu chí, so hai tiêu chí trong từng loss. Khóa ngưỡng bằng validation rồi báo ACER, APCER và BPCER trên video kiểm tra. Ghi rõ test CASIA này đã được quan sát trong quá trình phát triển.
3. Trong báo cáo cuối, giữ câu hỏi, thay đổi chính, tiêu chí chọn, kết quả và giới hạn cần hiểu. Đưa ma trận các nhánh, giá trị cấu hình, quy tắc hòa đầy đủ, lệnh, log và kiểm tra vào hồ sơ thí nghiệm riêng. [Kế hoạch 5.1 và 5.2](../fair_comparison_20261030/KE_HOACH.md).

**Câu dùng trong báo cáo hiện tại.** Nhóm chọn E3 để đánh giá trên nhiều seed vì ba cấu hình hòa về các chỉ số PAD trên tập kiểm định, còn E3 có BCE thấp nhất theo quy tắc phân định đã đặt trước. Muốn kiểm tra ảnh hưởng của tiêu chí chọn checkpoint đối với Focal, nhóm cần một phép đối chứng riêng giữa E3b và E4.
