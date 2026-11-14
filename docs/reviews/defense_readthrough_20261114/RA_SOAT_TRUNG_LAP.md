# Rà soát trùng lặp và nhất quán trước khi sửa báo cáo

Một phiên Antigravity Swarm trong project DeepFace-PAD đã nhận đủ bốn báo cáo từ `scope`, `science`, `delivery` và `verifier`. Cả bốn dùng Gemini 3.8 Flash Low. Các phát hiện dưới đây đã được đối chiếu với nguồn và các đoạn liên quan trong PDF 42 trang. Hồ sơ này dùng để đồng bộ sau khi đọc xong PDF.

| Ưu tiên | Phát hiện | Xử lý đề xuất |
| --- | --- | --- |
| <strong style="background-color:#FDE7E7;color:#941C30;padding:1px 4px;border-radius:3px;">Lệch phạm vi</strong> | PDF trang 1 vẫn gọi đề tài là hệ thống nhận diện thời gian thực. Trang 7, 32 và 41 coi nhận diện danh tính là phần chưa tích hợp. | Dùng tên Face PAD và giữ một đoạn bối cảnh xác thực khuôn mặt. Bỏ câu coi nhận diện danh tính là chức năng còn thiếu. Giữ bằng chứng webcam như giới hạn của nguyên mẫu PAD. |
| Làm rõ khi trình bày | Báo cáo và paper đã ghi nguồn khởi tạo của E3 từ checkpoint tốt nhất của E1 cùng seed. | Giữ chi tiết ở phần phương pháp theo quyết định mới nhất. |
| Giảm lặp giữa hai ghi chú | [Quyết định](QUYET_DINH.md) đã dẫn [ghi chú Focal](CHON_E3_VA_FOCAL.md) nhưng vẫn giữ bảng bốn bước và đoạn giải thích dài. Hai đoạn trong Quyết định cũng lặp thiết kế đối chứng E1–E3. | Sau khi chốt, để Quyết định giữ trạng thái, lựa chọn và liên kết. Đưa quy tắc chọn checkpoint/ngưỡng và ma trận thí nghiệm vào hồ sơ kỹ thuật. |
| Giảm lặp trong báo cáo | Tóm tắt và kết luận lặp bảng ACER, số liệu qua seed và chi phí A100. Mục UCDCN đã được rút gọn ở commit `02506b5`. | Tóm tắt mở bằng câu hỏi và kết quả chính. Chương 3 giữ số đầy đủ. |
| Câu chữ | “Giao thức phát triển” còn ở nhiều trang. Đã bỏ ghi chú phiên bản khỏi thân Chương 1 và giữ lý do chọn CDCN vì mã nguồn công khai ở mục chọn đối chứng. | Dùng “quy trình đánh giá do nhóm thiết lập trên CASIA-FASD” khi giới thiệu lần đầu. |

**Hai nhận xét của Swarm cần thu hẹp.** Các đoạn về E3 tại §3.2 báo cáo và phần phương pháp paper đã nói ba cấu hình hòa ACER/EER/AUC rồi phân định bằng BCE. Có thể nêu hệ quả của lựa chọn này trong thảo luận, giữ nguyên mô tả lịch sử. Câu ở đầu paper phân biệt PAD với nhận diện có thể giữ như định nghĩa bối cảnh. Câu ở phần giới hạn coi nhận diện là chức năng chưa tích hợp mới cần bỏ.

**Vị trí kiểm chứng.** [Bìa](../../../reports/round8_documents_20261023/BAO_CAO.md#L5) · [UCDCN](../../../reports/round8_documents_20261023/BAO_CAO.md#L104) · [Phương pháp Lượt 6](../../../reports/round8_documents_20261023/BAO_CAO.md#L271) · [Lựa chọn E3 trong paper](../../../reports/round8_documents_20261023/PAPER.md#L78) · [Nguồn slide](../../../reports/defense_20261115/build_defense_slides.mjs#L91).

Người dùng yêu cầu làm lại phép so sánh với số bước và weight decay được kiểm soát, sau khi khôi phục trạng thái dự án. Tại thời điểm rà lại chưa có kết quả đã xác minh cho phép thử này. Bản báo cáo chính chỉ cần nêu giới hạn của so sánh hiện có và câu hỏi mà phép thử sau sẽ xử lý. Số liệu nhắc ngắn trong slide, câu hỏi bảo vệ và bảng giải trình phục vụ các cách đọc độc lập.
