# Quyết định khi đọc báo cáo Deep PAD

Hồ sơ này ghi các điểm đã chốt và phương án cần chọn trước khi cập nhật báo cáo, bài báo, slide hoặc kế hoạch thí nghiệm. Nguồn phương pháp chi tiết vẫn là [kế hoạch V01–V09](../fair_comparison_20261030/KE_HOACH.md).

## Phạm vi và cách làm việc đã chốt

- Dự án nghiên cứu Face PAD. Giữ xác thực sinh trắc học khuôn mặt làm bối cảnh. Bỏ mục tiêu xây phần mềm nhận diện hoặc điểm danh và câu coi thiếu nhận diện danh tính là phần việc chưa hoàn thành. Chương 1 phân tích ưu và nhược của từng phương pháp trong công trình liên quan.
- Dùng tên mô tả cấu hình khi giải thích và giữ mã E0–E4 để đối chiếu. Mô tả phần việc cá nhân theo bảng phân công và công việc thực tế.
- Sau mỗi thắc mắc, đưa vài phương án ngắn gọn. Chờ người dùng chọn trước khi mở rộng phân tích hoặc đổi thiết kế. Người dùng đang đọc bản in. Những chỉnh sửa dưới đây là nội dung đề xuất để đồng bộ sau.
- Dùng skill `scientific-report-authoring` cho báo cáo sau mỗi thí nghiệm, highlight cách 2 cho tài liệu phù hợp. Khi dùng Antigravity, chỉ chọn Gemini 3.8 Flash hoặc Gemini 4 Hydrogen, ở mức Low đến High. Dùng `/boost` cho vấn đề coding khó, `/swarm` cho các phần độc lập cần điều phối qua một bảng chung. Giữ số agent tối thiểu.
- Khi review đầu ra mới, giao bản cần đọc cùng tiêu chí và nguồn kiểm cho một agent hoặc phiên độc lập. Yêu cầu trích bằng chứng, nêu điểm chưa xác minh, và kiểm cả diễn giải thuận lẫn bất lợi. Không gửi kết luận mong muốn hoặc lời giải của người viết. Không tự động coi hai lần đọc chung một nguồn là hai thí nghiệm độc lập.

## E1 và E3 trong Lượt 6

<strong style="background-color:#DDF7E9;color:#0B6B45;padding:1px 4px;border-radius:3px;">Đã xác minh</strong> E3 được chọn trên validation để chạy với seed 43–45, còn E1 là mốc CDCN tính điểm bằng trung bình bản đồ. Trong từng cặp, E1 huấn luyện 30 epoch. E3 khởi tạo từ checkpoint tốt nhất của E1 cùng seed rồi cập nhật thêm cả mạng và bộ phân loại trong 16 epoch. E1 dùng weight decay 5×10⁻⁵ và giai đoạn tinh chỉnh E3 dùng 10⁻⁴. E3 có ACER thấp hơn E1 ở seed 43 và 45, cao hơn ở seed 44. [Lượt 6](../../../reports/ROUND_6_RESULTS_2026-10-22.md).

<strong style="background-color:#FFF3C4;color:#755100;padding:1px 4px;border-radius:3px;">Chờ chọn phương án thực nghiệm</strong>

1. **Giữ phép so sánh hiện có.** Diễn giải là hiệu quả của cả quy trình tinh chỉnh E3 xuất phát từ E1. Cặp E1–E2 trả lời hẹp hơn về việc đổi cách tính điểm với mạng dự đoán độ sâu cố định. Đây là phương án đề xuất cho bảo vệ.
2. **Thêm đối chứng ngang lịch cập nhật.** Từ cùng E1, chạy hai nhánh thêm 16 epoch. Một nhánh chỉ học độ sâu, nhánh kia học đồng thời độ sâu và phân loại. Giữ cùng weight decay, LR, dữ liệu và số bước cập nhật. So sánh hai nhánh khi cả hai đều tính điểm bằng trung bình bản đồ để xem việc thêm mục tiêu phân loại thay đổi biểu diễn ra sao. Trên cùng checkpoint của nhánh học đồng thời, so sánh cách lấy trung bình với điểm từ bộ phân loại để đo ảnh hưởng của cách tính điểm. Chốt trước epoch hoặc tiêu chí chọn checkpoint chung, rồi chọn ngưỡng riêng cho từng cách tính điểm bằng cùng quy tắc validation. So sánh trực tiếp nhánh chỉ học độ sâu và dùng trung bình với nhánh học đồng thời và dùng bộ phân loại đánh giá cả quy trình ở ngân sách ngang nhau.
3. **Kiểm riêng weight decay nếu cần.** Chạy hai nhánh E3 từ cùng checkpoint E1, chỉ đổi 5×10⁻⁵ và 10⁻⁴. Chạy thử một seed trước khi quyết định lặp. Phép thử này trả lời độ nhạy của E3 với hệ số, chưa tách tác dụng của bộ phân loại khỏi 16 epoch tinh chỉnh.

## Lựa chọn E3 và phép so sánh BCE với Focal

Xem [ghi chú riêng về E3 và Focal](CHON_E3_VA_FOCAL.md). Báo cáo cuối giữ câu hỏi, yếu tố được thay đổi, tiêu chí chính, kết quả và giới hạn cần để đọc đúng kết luận. Chi tiết thiết kế đối chứng, cấu hình, log và lần chạy nằm trong hồ sơ thí nghiệm. Sau khi đọc xong PDF, đồng bộ những chỉnh sửa đã chốt.

### Hướng xử lý khác biệt E1 và E3

Chuẩn bị phép thử ngang số bước cập nhật từ cùng checkpoint E1 theo phương án 2 ở trên. Khóa weight decay của cả hai nhánh ở 10⁻⁴ như giai đoạn E3 lịch sử, giữ cùng Adam, LR, batch và dữ liệu. Thử một seed trên Colab trước, lưu đủ checkpoint và score theo epoch. Tách phép so sánh mục tiêu học (cùng tính điểm bằng trung bình) khỏi phép so sánh cách tính điểm (cùng checkpoint joint). Chỉ mở phép thử đổi riêng weight decay nếu cần đo độ nhạy của hệ số. Đây là thiết kế cần chuẩn bị, chưa có kết quả.

### Ghi chú khi sửa mục 1.5.3

UCDCN là tiền lệ gần vì vừa dự đoán độ sâu vừa dùng bộ phân loại cho quyết định thật/giả. Giải thích hợp nhất đặc trưng là kết hợp thông tin từ nhiều tầng để hỗ trợ dự đoán bản đồ. Nêu đánh đổi về độ phức tạp và cách tác giả rút gọn mạng. Chi tiết ngưỡng giữa các bảng và so sánh GPU chuyển sang hồ sơ đối chiếu nếu cần. Mục này cần kết nối với câu hỏi của Deep-PAD về cách tính điểm trên CDCN. [Bài báo UCDCN](https://link.springer.com/article/10.1007/s40747-024-01397-0).

### Quy trình lựa chọn E3 trong Lượt 5

| Bước | Quy tắc lịch sử | Ý nghĩa |
| --- | --- | --- |
| Huấn luyện | E3/E3b dùng BCE cho phân loại, E4 dùng Focal. Cả ba có giai đoạn joint, lịch trước joint khác giữa E3 và E3b/E4 | Xác định cách cập nhật trọng số |
| Chọn checkpoint | Điểm BCE validation cấp khung hình trong head/joint, gồm cả E4. Stage chỉ học độ sâu dùng loss độ sâu | Tiêu chí chung nhưng có thể bỏ qua epoch có chỉ số PAD video tốt hơn |
| Chọn ngưỡng | Tối thiểu ACER video validation. Nếu hòa, ưu tiên chênh lệch hai tỷ lệ lỗi thấp hơn, rồi ngưỡng thấp hơn trong tập ứng viên | Chọn ranh giới quyết định cho từng checkpoint đại diện |
| Chọn cấu hình đi tiếp | Ưu tiên ACER, EER, AUC rồi BCE. E3/E3b/E4 hòa 0%, 0%, 1 trên ba chỉ số đầu. E3 đi tiếp do BCE thấp nhất | Đủ căn cứ chọn ứng viên theo quy tắc đã định. Ba chỉ số PAD validation vẫn hòa |

Dùng BCE chung có nghĩa thống nhất phép đo điểm dự đoán. Điều đó chưa xác lập E3 hơn Focal về PAD. Cặp E3b–E4 gần hơn cho câu hỏi về loss vì cùng lịch, còn tiêu chí chọn checkpoint vẫn là một phần của thiết kế. Các phương án là giữ kết luận theo quy tắc lịch sử, kiểm độ nhạy ngưỡng bằng score validation đã lưu, hoặc làm phép thử 5.1 dùng chỉ số PAD video để chọn checkpoint cho cả BCE và Focal. Đổi lựa chọn ở cuối joint có thể phân tích từ checkpoint/score từng epoch nếu có đủ. Nếu đổi checkpoint cuối head, cần chạy lại joint từ checkpoint được chọn mới. [Kết quả rà soát](../fair_comparison_20261030/KET_QUA.md).

### Câu sửa đề xuất

> Nhóm chọn E3 để đánh giá ở ba seed (giá trị khởi tạo bộ sinh số ngẫu nhiên) vì E3, E3b và E4 có cùng ACER, EER và AUC trên tập kiểm định, còn E3 có BCE thấp nhất theo quy tắc phân định đã đặt ra. Với mỗi lần so sánh, nhóm lấy trọng số tốt nhất của CDCN dùng điểm trung bình bản đồ (E1) để khởi tạo E3 rồi tinh chỉnh thêm 16 epoch. E3 có ACER thấp hơn E1 ở seed 43 và 45, cao hơn ở seed 44. So sánh này đánh giá cả quy trình tinh chỉnh, trong đó cách tính điểm, mục tiêu huấn luyện và weight decay cùng thay đổi.

Nơi cần đối chiếu khi đồng bộ: tóm tắt, mục 1.6, 2.15, 3.8 và 3.15 của báo cáo, phần phương pháp/kết quả của paper, slide 5 và 10, giải trình DG56 R04–R07, và kế hoạch V01/V03/V08.

## Trạng thái kiểm tra Antigravity

CLI 1.5.8 đã gọi thành công Gemini 3.8 Flash Low ở chế độ một prompt. Khi thử `/swarm board` qua `-p`, phiên hết thời gian chờ và chưa xác nhận mở bảng. Chế độ tương tác đã hiển thị Gemini 3.8 Flash Low rồi yêu cầu chọn điều khoản và tùy chọn sử dụng dữ liệu trong thiết lập ban đầu. Người dùng cần tự quyết định ở màn hình này. Sau đó có thể kiểm menu `/` và `/swarm board` trước. Chỉ chạy `/boost` hoặc khởi tạo swarm khi xác minh được gói hỗ trợ và các agent tuân thủ giới hạn model đã chốt. [Tài liệu Boost](https://antigravity.google/docs/boost/) · [Tài liệu lệnh Antigravity](https://antigravity.google/docs/slash-commands/).
