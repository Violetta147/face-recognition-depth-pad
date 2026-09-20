# Bàn giao giữa kỳ Lượt 1–3

Ngày chốt trạng thái: 20 tháng 9 năm 2026.

## Đã hoàn tất trong repository

- Đặc tả, kế hoạch hai thành viên, threat model và giới hạn nghiên cứu.
- Literature matrix gồm ít nhất năm công trình và quy tắc so sánh công bằng.
- Protocol CASIA-FASD tạm thời: 600 video, 12.000 frame, tách subject giữa train, validation và test.
- E0 MobileNetV3 năm epoch; threshold chọn trên validation rồi khóa trước test.
- Kết quả test E0: APCER 0%, BPCER 11,11%, ACER 5,56%, EER 2,41%, ROC AUC 0,99798.
- Failure analysis E0 theo quality, subject và video khó.
- Queue, ledger, retry, provenance, QA và worker 3DDFA V2 có khả năng resume.
- CDCN E1, contrastive depth loss và chuyển checkpoint E1 sang E2.
- 38 unit test đều pass.

## Việc duy nhất cần người dùng thực hiện

Codex không thể tự mở phiên Colab trả phí, truy cập Google Drive hoặc dataset trong tài khoản của người dùng. Vì vậy người dùng cần chạy phần GPU theo đúng mục **Consolidated CASIA midterm run** trong `COLAB.md`.

1. Đưa các thay đổi repository hiện tại lên GitHub hoặc tải chúng vào Colab, rồi cài lại package editable.
2. Chạy tạo batch visualization và queue depth trên CPU.
3. Cài 3DDFA V2 chính thức; chạy smoke test 50 bona fide frame trên A100.
4. Mở vài depth map và chỉ tiếp tục nếu vùng mặt có cấu trúc hợp lý, không rỗng và không phải map hằng.
5. Chạy hết queue, xử lý/retry failure có lý do, materialize manifest và chạy depth audit.
6. Chỉ khi `casia-depth-qa.json` có `valid: true`, chạy `casia_e1_smoke.yaml`, sau đó mới chạy `casia_e1_cdcn.yaml`.
7. Không dùng test để chỉnh threshold hoặc chọn checkpoint. Threshold E1 phải được khóa từ validation trước khi mở test.

## Bằng chứng cần gửi lại

- Ảnh `casia-val-batch.png`.
- Ảnh `casia-depth-smoke.png` và thư mục `e1-depth-cases`, gồm case đúng và case lỗi nếu có.
- File `casia-depth-qa.json` và số lượng complete/failed trong ledger.
- Đường dẫn run E1 smoke và E1 full trên Drive.
- `train_log.csv`, `metrics.json`, `threshold.json`, raw validation/test scores và `depth_input_snapshot.json` của E1.

Khi nhận các bằng chứng trên, có thể đánh dấu các tiêu chí còn lại của Lượt 3, rà soát toàn bộ số liệu và chỉ lúc đó mới làm slide giữa kỳ. Không cần zip dataset hoặc commit frame, depth map, checkpoint hay dữ liệu sinh trắc học lên GitHub.
