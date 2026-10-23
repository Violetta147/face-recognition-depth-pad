# Rà soát cục bộ để bàn giao Lượt 6

## Phạm vi đã đọc

Snapshot sau khi lưu trữ phụ phẩm hooks, tại HEAD `020aa66`: 1.672 tệp,
583.336.120 byte; 217 tệp Git quản lý được rà theo nội dung hoặc cấu trúc.
Không có lỗi đọc. Nhật ký chi tiết:
`artifacts/project-hooks/round6-handoff-review-20261022/file-review.json` và
`authored-document-catalog.json`. Các tài liệu bàn giao được soạn sau snapshot
này được kiểm tra riêng; không cộng ngầm vào số tệp của snapshot.

Hai catalog đã được chuyển nguyên hash từ thư mục audit tạm vào vùng nhật
ký hooks. Vùng này không được scanner coi là nguồn phụ thuộc, tránh việc
chính danh sách kiểm kê chứa mọi tên tệp làm xuất hiện tham chiếu giả.
Biên nhận di chuyển nằm tại `relocation.json` cùng thư mục.

| Phương thức | Số tệp |
| --- | ---: |
| Đọc đầy đủ văn bản UTF-8, có AST/đề mục cho nguồn được Git quản lý | 771 |
| Đọc đầy đủ CSV và đếm dòng | 159 |
| Đọc JSON notebook, cell và output đã lưu; không thực thi | 23 |
| Trích nội dung thân Word/slide từ XML | 33 |
| Trích văn bản của mọi trang PDF | 83 |
| Đọc header ảnh và hash byte; không xem lại từng ảnh | 467 |
| Chỉ hash byte của binary, gồm trọng số và gói lưu | 136 |

Có 24 đường dẫn bị bỏ qua, gồm Git, môi trường/dependency, metadata Obsidian,
reparse point và chính thư mục chứa audit này. Không theo junction/symlink.
Không nạp tensor/unpickle, không chạy notebook, không kiểm lại bằng inference.
Không đọc mới Google Drive hoặc kiểm kê máy khác. Đây là đọc bằng máy theo
nội dung/cấu trúc kết hợp rà các điểm quyết định; không tuyên bố đã đọc thủ
công từng dòng thư viện hay xem lại hình thức mọi trang tài liệu.

## Kết luận về Lượt 5

Lượt 5 đã xong phần thực nghiệm và ablation. Ba biên nhận smoke, full
validation và frozen test đều PASS. Hash 471 tệp và publication vẫn khớp.
Sáu CSV test có đúng 360 dòng video mỗi tệp. Kết quả seed 42:

| Mô hình | ACER test phát triển |
| --- | ---: |
| E0 | 5,5556% |
| Official E1 / E2 | 2,7778% / 2,7778% |
| E3 / E3b | 5,0000% / 5,0000% |
| E4 | 4,4444% |

E3 vẫn được chọn bằng validation trước khi mở test. Không dùng E4 thay E3
theo thứ hạng test. Không gọi nhiều seed, benchmark mới hoặc webcam là kết
quả đã đo. Final report và paper đã có bản biên tập đến Lượt 5; giữ hai bản
Word nguyên byte, không quay lại trạng thái “chưa có báo cáo”. Các câu “tạm
dừng Word” trong audit ngày 16/10 mô tả thời điểm cũ, không phủ nhận bản 19/10.

## Bản đồ nguồn cần cho Lượt 6

| Nhóm | Điểm đọc và vai trò |
| --- | --- |
| Quyết định hiện hành | `reports/ROUND_6_REPLICATION_PLAN.md`, `docs/handoffs/ROUND6_2026-10-22.md`. |
| Lựa chọn E3 và kết quả âm tính | Hai báo cáo `ROUND_5_FULL_VALIDATION_2026-10-16` và `ROUND_5_TEST_RESULTS_2026-10-16`, cả JSON lẫn Markdown. |
| Protocol/data | `data/README.md`; `src/deepface_pad/data.py`, `casia_fasd.py`, `depth_jobs.py`, `depth_qa.py`, `preflight.py`. |
| Mô hình/loss | `models/cdcn_official.py`, `models/cdcn_depth_head.py`, `models/depth_head.py`, `losses.py` dưới `src/deepface_pad/`. |
| Train/selection | `src/deepface_pad/train.py`; `configs/casia_e1_cdcn_official.yaml`, `configs/casia_e3_joint_bce.yaml`. |
| Score/metrics | `scripts/score_checkpoint.py`; `metrics.py`, `evaluate.py`, `depth_evaluation.py` dưới package. |
| Mẫu Colab | `scripts/build_round5_colab.py`, notebook clean Official E1 và notebook Lượt 5. Chỉ dùng làm mẫu, không chạy lại nguyên gói. |
| Kiểm tra | `tests/test_preflight.py`, `test_training_stages.py`, `test_official_depth_head.py`, `test_round5_notebook.py`, `test_metrics.py`, `test_manifest.py`. |
| Số liệu và bản xuất | `docs/HOOK_EVIDENCE_MAP.md`, `.codex/publication_baseline.json` và các test Word/paper/slide. |

## Những điểm cần giải quyết trước khi chạy Lượt 6

1. Chưa có notebook, builder hoặc sáu config Lượt 6 trong checkout. Không
   mô tả chúng là đã sẵn sàng chạy chỉ vì đã có kế hoạch và ngân sách.
2. Notebook/builder Lượt 5 hard-code E1 seed 42. Phải tạo gói mới, nạp best E1
   đúng seed 43/44/45 cho E3 và kiểm tra SHA-256 liên kết initializer.
3. `train.run` chỉ tạo loader train/val và score validation cuối run, phù hợp
   đóng test. `score_checkpoint.py` mặc định split test; threshold có source
   validation chưa đủ thay cổng freeze toàn bộ sáu run của notebook mới.
4. Runner lưu model/config/epoch và log, nhưng chưa lưu/khôi phục đủ optimizer,
   scheduler và RNG để gọi là resume training đầy đủ. Không nhầm warm-start
   bằng `init_checkpoint` với tiếp tục run bị ngắt.
5. `environment.txt` hiện có Python/platform/torch/device, chưa là bản kiểm
   kê đầy đủ GPU/driver/cuDNN/dependency. Gói Lượt 6 phải lưu bổ sung trước run.
6. Nguồn chọn threshold hiện là minimum validation ACER, rồi độ lệch tuyệt đối
   APCER–BPCER, rồi threshold nhỏ hơn. Không đổi quy tắc theo kết quả test.
7. Ghi chú ngày 19/10 còn ví dụ 42/43/44; quyết định hiện hành là seed mới
   43/44/45. Kết quả seed 42 khác môi trường chỉ là lịch sử.

Đây là các điều kiện cho gói chạy tiếp theo, không phải lỗi được phép sửa
âm thầm trong phiên dọn hooks. Phiên này không thay code nghiên cứu.
