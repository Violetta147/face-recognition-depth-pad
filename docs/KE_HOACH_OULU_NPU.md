# Kế hoạch thực nghiệm DeepFace-PAD trên OULU-NPU

Cập nhật ngày 14/11/2026. **Điểm bắt đầu khi quay lại: khôi phục cache RGB Train/Dev và chạy thử tạo pseudo-depth trên một nhóm nhỏ.** Kế hoạch này ghi các bước dự kiến. Lượt thực nghiệm đã hoàn tất hiện là MobileNetV3-Small trên Protocol 1, seed 43.

## Mốc kết quả đã khóa

| Hạng mục | Giá trị |
| --- | --- |
| Train / Dev / Test | 1.200 / 900 / 600 video, 8 khung/video, tách theo người |
| Mô hình | MobileNetV3-Small khởi tạo từ ImageNet, BCE, AdamW |
| Cấu hình đã chạy | A100 80 GB, BF16, batch 128, LR 0,0003, 3 epoch, 75 bước cập nhật/epoch |
| Chọn checkpoint và ngưỡng | Epoch 3, ngưỡng 0,45529577 từ Dev, điểm video là trung bình điểm các khung |
| Dev | ACER 1,25%, từ chối nhầm 2/180 video thật |
| Test | ACER 16,25%, từ chối nhầm 38/120 video thật (BPCER 31,67%) |
| Tấn công lọt qua trên Test | In 1/240 (0,42%), phát lại 2/240 (0,83%). APCER chung lấy tỷ lệ cao hơn |
| Chỉ số bổ sung trên Test | AUC 0,9790, EER 6,77% |

**Câu hỏi tiếp theo:** mô hình dự đoán độ sâu và đầu phân loại có giúp giảm từ chối nhầm người thật ở phiên quay khác trong khi giữ tỷ lệ lọt của từng loại tấn công ở mức thấp không? Kết quả MobileNet mới có một seed. Test Protocol 1 đã được xem, nên các phép so sánh tiếp theo trên tập này là bằng chứng phát triển. Mọi quyết định chọn checkpoint, ngưỡng và cấu hình cho lượt mới dựa trên Train/Dev.

- [Thư mục run đã khóa trên Drive](https://drive.google.com/drive/folders/1RWkKGFNrKqfIFnCJ6DWKjXS7Oy-RSEDJ)
- [Ba ZIP cache RGB trên Drive](https://drive.google.com/drive/folders/1oQMEbg0Bh_rRrplUWTqAVff75Jq5PKbh). Đã kiểm tên và kích thước sau khi Colab ghi file.
- [Notebook đã chạy](../notebooks/Face_PAD_OULU_NPU_A100_Executed.ipynb). Bản lưu cục bộ có cả lỗi crop Dev ban đầu và kết quả cuối.

## Thứ tự triển khai

| Bước | Việc cần làm | Đầu ra để đi tiếp |
| --- | --- | --- |
| 1. Khôi phục RGB | Mở [notebook sạch](../notebooks/Face_PAD_OULU_NPU_A100.ipynb), chạy cell 1, 2 và 4 để khôi phục/cache đúng cấu hình. Kiểm tra Train 9.600 và Dev 7.200 khung, cùng SHA-256 của manifest và ảnh. | Hai split sẵn sàng. Nếu Colab báo cache khác phiên bản, kiểm tra phiên bản OpenCV và thông tin trong ZIP trước khi chép lại TAR. |
| 2. Kiểm tra pseudo-depth | Chuẩn bị notebook gọi worker 3DDFA V2 hiện có. Chạy một nhóm nhỏ ảnh người thật từ Train/Dev, lấy mẫu qua vài camera và phiên quay. Kiểm tra kích thước 32 × 32, giá trị hữu hạn, bản đồ thật có biến thiên và target attack bằng 0. Kiểm tra trực quan vài cặp RGB/target và ghi thời gian. | Log smoke, độ phủ và lỗi theo mẫu, cùng cấu hình worker và hash tài sản. Dùng tốc độ đã đo để ước lượng thời gian xử lý đủ. |
| 3. Tạo pseudo-depth đầy đủ | Tạo target cho Train/Dev theo nhóm và lưu snapshot ra Drive, rồi thử khôi phục một snapshot. Tổng đầu vào theo manifest hiện tại là 3.360 khung người thật cần dựng và 13.440 khung tấn công có target bằng 0. Rà lỗi dựng mặt trước khi train. | Manifest có depth và preflight đạt. Snapshot có map, ledger, hàng đợi, provenance và đối chiếu hash RGB, cấu hình, trọng số. [Hướng dẫn cache](COLAB_PROGRESS_AND_CACHE.md) |
| 4. Đo E1 rồi đối chứng E1–E3 | Train E1 (CDCN đọc điểm bằng trung bình bản đồ độ sâu) một seed 43. Từ cùng checkpoint E1, so sánh **E1 tiếp tục học độ sâu** với **E3 học chung độ sâu và phân loại BCE**. Giữ cùng dữ liệu, seed, số bước cập nhật thêm, batch, optimizer, LR, weight decay và quy tắc chọn theo PAD trên Dev. | Có log số bước thực tế, checkpoint, điểm video và chỉ số Dev của hai nhánh. Thêm E2, chỉ học đầu phân loại trên backbone khóa, nếu cần tách tác dụng đọc điểm khỏi việc cập nhật backbone. |
| 5. So BCE–Focal | Ưu tiên sau khi E1–E3 chạy ổn. So E3b và E4 với cùng checkpoint khởi tạo và cùng lịch depth → head → joint. Hai nhánh dùng một quy tắc chọn checkpoint và ngưỡng. Với Focal, ghi rõ alpha, gamma và hệ số loss. | So sánh được tác động của thay đổi loss phân loại trong cùng lịch. Sau lượt đầu, dự kiến chạy cặp seed 44 và 45 cho đối chứng chính nếu còn ngân sách. |
| 6. Mở rộng đánh giá | Khóa danh sách run, checkpoint và ngưỡng từ Dev trước khi chấm Test. Nếu muốn thử thêm một thay đổi rẻ, so mean với median khi gộp khung trên Dev bằng cùng checkpoint. Sau đó chạy Protocol 2 nếu câu hỏi là độ bền trước máy in và màn hình khác. | Kết quả theo protocol và theo seed, kèm số video lỗi. Protocol 2 có thể trùng video hoặc người với nguồn đã quan sát ở Protocol 1. |

## Quy tắc cho lần chạy mới

- Dùng video làm đơn vị đánh giá. Báo BPCER, APCER print, APCER replay, APCER chung và ACER, kèm tử số/mẫu số. Báo thêm AUC và EER để phân biệt chất lượng xếp hạng với lỗi tại ngưỡng đã khóa. Nếu mô hình giảm BPCER nhưng tăng APCER, trình bày cả hai thay đổi.
- Chạy thử vài batch CDCN trên GPU thực tế để chốt batch và precision. Batch 128 đã đo cho MobileNetV3-Small. Với hai nhánh cần đối chứng, dùng chung cấu hình đã chốt và ghi số cập nhật cùng thời gian. Giữ riêng thời gian khôi phục cache, dựng depth, train và chấm.
- Nếu một video hoặc map lỗi, lưu đúng ID và traceback, dùng lại phần cache đã hoàn tất rồi chạy lại phần lỗi. Rà lại bất kỳ thay đổi nào về số khung, nội dung ảnh hoặc cấu hình dựng depth trước khi tiếp tục từ cache.

Tham chiếu thiết kế thí nghiệm và triển khai [hướng dẫn OULU-NPU của dự án](OULU_NPU.md), [bàn giao BCE–Focal của CASIA](reviews/defense_readthrough_20261114/CHON_E3_VA_FOCAL.md) và [Kassis và cộng sự, Scientific Agent Skills (2026)](https://arxiv.org/abs/2609.00065).
