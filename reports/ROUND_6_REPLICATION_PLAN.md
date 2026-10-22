# Lượt 6: thiết kế lặp lại E1 và E3 nhiều seed

Trạng thái 22/10/2026: **replication ba cặp E1/E3 seed 43/44/45 đã hoàn tất
train/validation, freeze trước test và kiểm toán test đã lưu**. Mean video
ACER E1 4,3210%, E3 3,7037%; paired delta E3 − E1 = −0,6173 điểm phần trăm,
sample SD 2,6857 điểm phần trăm. E3 tốt hơn ở 2/3 seed, kém hơn seed 44;
chưa kết luận cải thiện nhất quán. Xem `ROUND_6_RESULTS_2026-10-22.md/.json`.
Đăng ký và source gói chạy vẫn giữ nguyên. Thiết kế bên dưới là bản đã dùng,
không phải yêu cầu chạy lại. Đo chi phí E1/E3/E4 và đối chiếu protocol paper
chưa hoàn tất. E3 vẫn là ứng viên chọn từ validation Lượt 5.

## Câu hỏi và điều kiện giữ nguyên

Kiểm tra chênh lệch E3–E1 có ổn định khi đổi khởi tạo/thứ tự train không. Dữ
liệu vẫn là CASIA 12.000 frame/600 video, cùng split, cache 3DDFA, normalization,
augmentation, evaluator và quy tắc threshold. Không sinh lại pseudo-depth.

E1 lịch sử: torch 2.11.0+cu128; các run Lượt 5: torch 2.11.0+cu130. Đợt mới
cần ghi và giữ cùng torch/CUDA runtime/GPU cho các cặp. Seed 42 hiện tại giữ
làm kết quả lịch sử; không trộn vào mean/std của đợt kiểm soát môi trường mới.

## Phương án đủ ba seed

| Seed mới | Đối chứng E1 | Ứng viên E3 | Tổng epoch |
| --- | --- | --- | ---: |
| 43 | Depth-only 30 epoch | Joint BCE 16 epoch, nạp best E1 seed 43 | 46 |
| 44 | Depth-only 30 epoch | Joint BCE 16 epoch, nạp best E1 seed 44 | 46 |
| 45 | Depth-only 30 epoch | Joint BCE 16 epoch, nạp best E1 seed 45 | 46 |

Sáu run, **138 epoch**. Dự trù khoảng 2–3 giờ A100 gồm setup/QA và đánh giá,
ước lượng từ các run vừa thực hiện; phải xem tiến độ thực tế. Không chạy lại
run seed 42 đã hoàn tất. Mỗi E3 phải nạp initializer E1 đúng seed, không dùng
chung E1 seed 42 để gọi là ba seed pipeline độc lập.

E1 giữ config cũ: Adam LR 10^-4, weight decay 5×10^-5, batch 8, official depth
loss MSE + contrast MSE, chọn minimum val depth loss. E3 giữ config Lượt 5:
Adam LR 10^-4, weight decay 10^-4, batch 8, joint depth + BCE 16 epoch, chọn
minimum validation classification BCE. Đây là so sánh hai cấu hình đã có,
không cô lập riêng tác dụng head/freeze khi hyperparameter khác.

Khóa config/source/môi trường/budget trước khi train. Tất cả sáu run hoàn tất
validation rồi freeze trước test mới của đợt. Cấu hình E3 cố định xuyên seed,
không chọn lại một model khác ở từng seed. Threshold và checkpoint vẫn chọn
riêng từ validation của mỗi run theo quy tắc cố định.

Báo từng run và mean/sample SD (ddof=1) của APCER/BPCER/ACER/EER/AUC. Chỉ số
chính là video ACER; báo paired delta ACER = E3 − E1 theo từng seed và trung
bình. Mean delta < 0 mới có cải thiện trung bình trong đợt này; ba seed vẫn
không đủ để khẳng định tổng quát hoặc độc lập với CASIA đã quan sát. Nếu delta
không giảm, giữ kết luận âm tính. Không loại seed xấu hoặc chỉ trình bày best.

## Nếu ngân sách hạn chế

Có thể chạy trước **một cặp seed 43**, hai run/46 epoch, rồi thêm hai cặp khi
có compute. Đây là tiến độ một seed mới; chưa được đánh dấu đủ ba seed hoặc
mean/std ổn định. Giữ đăng ký và cùng môi trường khi tiếp tục; đổi môi trường
phải ghi lại và xem xét một block riêng.

## Những việc khác của Lượt 6

- Đo lại E1/E3/E4 cùng GPU và input, warm-up, nhiều lượt, đổi thứ tự; báo params,
  checkpoint size, p50/p95 và phạm vi forward. Không suy ra webcam FPS từ đây.
- Bảng paper ghi chính xác dataset/protocol/split/unit/threshold và table nguồn.
  CASIA nhóm khác protocol paper thì chỉ so bối cảnh.
- Error analysis đã có paired video và subgroup quality; ảnh RGB/target/
  prediction/error map và webcam vẫn thuộc phần cần thực hiện của Lượt 7.

Ngân sách đã được người dùng xác nhận ngày 22/10/2026; sáu run đã thực hiện
trên A100 theo đăng ký và freeze. Ước lượng 2–3 giờ ở bản thiết kế không phải
phép đo tổng runtime. Không chạy lại hoặc chọn lại cấu hình từ kết quả test.
Hai bản Word hiện có giữ nguyên ở kết quả Lượt 5.
Xem `../docs/handoffs/ROUND6_2026-10-22.md` cho các điều kiện thực thi và
`../docs/PROJECT_REVIEW_FOR_ROUND6_2026-10-22.md` cho kết quả rà soát mã nguồn.
