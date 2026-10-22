# Lượt 6: đăng ký phép đo chi phí suy luận

Trạng thái 22/10/2026: phép đo A100 đã xong và kiểm toán PASS; kết quả ở
`ROUND_6_COST_RESULTS_2026-10-22.md/.json`. Notebook replication đã nhận tại
`notebooks/Face_PAD_Round6_CASIA_E1_E3_Executed.ipynb`, giữ nguyên byte; biên nhận
ở `ROUND_6_EXECUTED_NOTEBOOK_2026-10-22.json`. Bảng đối chiếu protocol paper đã
có tại `ROUND_6_PAPER_PROTOCOL_COMPARISON_2026-10-22.md/.json`. Đã nhận cost
notebook executed, đủ 3.600 mẫu đo và 18 lượt, không còn việc cần Colab.
Hướng dẫn đăng ký ban đầu giữ tại `docs/ROUND6_COST_COLAB_GUIDE.md` để truy
provenance; không chạy lại training hoặc phép đo đã hoàn tất.

## Model và câu hỏi

Đo chi phí của forward thực tế E1, E3 và E4 trên cùng phiên A100. E1/E3 lấy
seed 43 vì đó là seed đầu tiên trong đăng ký, không chọn checkpoint theo thứ
hạng test. E4 dùng checkpoint validation đã khóa của Lượt 5 seed 42, chỉ để đo
chi phí. Không cộng E4 hoặc seed 42 vào thống kê accuracy của ba seed mới.
Hash checkpoint/config và mọi thông số cố định ở `configs/round6_cost.json`.
Runner: `src/deepface_pad/cost.py`. Test CPU dùng ảnh/timer fixture để kiểm
transform, thứ tự đo, loại warm-up, đồng bộ, quantile và cổng mặc định đóng;
chúng không tạo hoặc thay thế timing A100 thực tế.

Đã nạp strict cả ba checkpoint trên CPU, kiểm SHA-256 trước khi nạp bằng
`weights_only=True`; không forward. Biên nhận `ROUND_6_COST_STATIC_2026-10-22.json`:

| Model | Params | Byte parameter FP32 | Byte state gồm buffer | Byte file checkpoint |
| --- | ---: | ---: | ---: | ---: |
| E1 | 2.245.016 | 8.980.064 | 8.993.056 | 9.020.220 |
| E3 | 2.246.281 | 8.985.124 | 8.998.116 | 9.029.106 |
| E4 | 2.246.281 | 8.985.124 | 8.998.116 | 9.029.042 |

Head thêm 1.265 parameter (khoảng 0,0563% so với E1). p50/p95 GPU đã có trong
báo cáo kết quả nêu trên; các thông số đăng ký bên dưới được giữ nguyên.
Notebook sạch `notebooks/Face_PAD_Round6_Cost_E1_E3_E4.ipynb` được tạo bằng
`scripts/build_round6_cost_colab.py`; đóng gói source đã commit bằng
`scripts/package_round6_cost.py`. Dừng sau cell 1.1 để kiểm preflight trước
khi mở cổng đo ở cell 2.1. Không chạy Run all.

E3 và E4 dùng cùng kiến trúc `OfficialCDCNWithDepthHead`; BCE/Focal và lịch
train khác nhau không tự làm thay đổi kiến trúc forward. Không diễn giải một
chênh lệch timing nhỏ giữa chúng là lợi thế của Focal. Không thêm/bớt head hoặc
loại bỏ phép toán trong forward để tạo lợi thế benchmark.

## Input và cách đo

- Hai frame validation thật từ ZIP CASIA đã có trên Drive: sample_id đầu tiên
  khi sort, một frame mỗi nhãn 0/1. Không sử dụng test để chọn input.
- Dùng đúng transform `PadDataset` Official CDCN, không augmentation. Batch 1,
  RGB 256 × 256, float32, contiguous NCHW. Hash file ảnh và tensor được ghi
  trước phép đo; không đưa ảnh vào báo cáo hoặc Git.
- Decode, resize/normalization, chuyển input/weights lên GPU và ghi Drive đều
  nằm ngoài khoảng đo. Cả ba model dùng đúng các tensor GPU đó.
- `eval()` và `inference_mode()`, không autocast/TF32/compile/CUDA Graph.
  cuDNN benchmark=False, deterministic=False, giữ nguyên suốt block.
- Sáu vòng dùng đủ sáu hoán vị thứ tự E1/E3/E4, shuffle theo seed 20261022;
  mỗi model xuất hiện hai lần ở mỗi vị trí. Không chọn vòng nhanh nhất.
- Mỗi lượt model: 50 forward warm-up, 200 forward có đo; luân phiên hai input.
  Tổng 1.200 mẫu đo/model. Ghi raw timing và p50/p95 theo từng lượt và toàn bộ.
- Báo hai phạm vi riêng: CUDA-event elapsed trên stream và wall time của
  forward đã synchronize. Không gọi nghịch đảo latency là FPS webcam.

Lưu params, số byte tensor state, kích thước checkpoint thực tế, hash input/
checkpoint/source, GPU UUID/driver/torch/CUDA/cuDNN/dependencies và các cờ
precision. Checkpoint có config/metadata nên file size không đồng nghĩa RAM.
Nếu dùng phiên A100 mới, ghi là một block đo mới; không sửa registration train.

## Cổng và kết quả

Notebook đo riêng sẽ kiểm source/checkpoint/input và CPU tests trước khi mở
`RUN_BENCHMARK=False`. Chỉ mở sau khi output preflight được kiểm. Có raw log
đang dở hoặc môi trường khác thì dừng, giữ bằng chứng; không ghi đè/chọn lại
lượt nhanh. Không chỉnh sáu checkpoint, threshold, score CSV hay freeze cũ.

Khi nhận kết quả GPU, kiểm lại số mẫu, thứ tự, quantile và hash, rồi cập nhật
bảng chi phí và trạng thái Lượt 6. Phần CPU/synthetic test chỉ chứng minh code
hoạt động; chỉ dùng timing A100 thực tế để kết luận chi phí suy luận.

Kiểm toán saved CSV/JSON bằng `scripts/audit_round6_cost.py` (CPU, không forward).
Script đối chiếu registration đã duyệt, source lock trong ZIP, plan/model/input,
hash raw CSV, toàn bộ thứ tự và p50/p95 tính lại. Giữ mọi mẫu chậm; có failure
receipt hoặc bằng chứng khác hash thì dừng. `tests/test_round6_cost_audit.py`
kiểm đường PASS và các trường hợp thay registration/raw/statistics/profile/
thứ tự/failure, kể cả sửa raw hash nhưng đảo thứ tự. Timing fixture chỉ kiểm
logic auditor, không dùng làm số đo nghiên cứu.
