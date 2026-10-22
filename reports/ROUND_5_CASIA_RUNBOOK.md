# Lượt 5: chạy tiếp E3, E3b và E4 trên CASIA đã khóa

Đăng ký trước ngày 16/10/2026, trước khi có score E3/E3b/E4. Đây là phần tiếp
tục thí nghiệm; báo cáo cuối kỳ đang tạm dừng. Đối chiếu Lượt 1–4 tại
`RESEARCH_AUDIT_ROUNDS_1_4_2026-10-16.md`.

## Câu hỏi và cấu hình

**Cập nhật sau smoke 16/10:** preflight và ba GPU smoke đã được đối chiếu trực
tiếp, đạt cổng kỹ thuật. Xem `ROUND_5_SMOKE_AUDIT_2026-10-16.md`. Bước hiện tại
là cell 3.1–3.2 full validation, chưa mở test. Nội dung đăng ký giữ nguyên;
dùng tiếp source commit `525c808`, không cần thay ZIP vì cập nhật tài liệu này.

**Cập nhật sau full validation 16/10:** cả ba nhánh đã train đủ 16 epoch, kiểm
toán CSV/checkpoint/MAE đạt PASS, chọn E3 bằng quy tắc validation và ghi freeze
trước test. Xem `ROUND_5_FULL_VALIDATION_2026-10-16.md`. Bước hiện tại là cell
4.1 kiểm tra freeze, rồi cell 4.2 mở test phát triển tại ngưỡng đã khóa. Giữ
lựa chọn E3 từ validation dù thứ tự test khác. Gói source vẫn là `525c808`.

**Cập nhật sau test 16/10:** cả ba score test đã đối chiếu freeze/CSV/metrics,
không đổi threshold. E3/E3b ACER 5%, E4 4,4444%; chưa giảm so E1/E2 2,7778%.
Giữ E3 là ứng viên validation. Xem `ROUND_5_TEST_RESULTS_2026-10-16.md` và
`ROUND_6_REPLICATION_PLAN.md`. Cell test đã hoàn tất; không cần score lại.

E3 học đồng thời backbone CDCN và head phân loại bằng BCE. E3b học theo ba
giai đoạn: depth (chỉ backbone), head (khóa backbone và BatchNorm), joint
(cùng học backbone và head). E4 giữ lịch đó và đổi classification loss sang
Focal. Cả ba bắt đầu riêng từ **cùng checkpoint E1**, không nối E3 sang E3b/E4.
Head khởi tạo cùng seed 42. E3b là nhánh trung gian đã được cho phép ở Lượt 5
của kế hoạch tám lượt; không mở grid search.

| Nhánh | Lịch epoch | Classification loss | So sánh giải quyết |
| --- | --- | --- | --- |
| E3 | joint 16 | BCE | Mốc joint trong ngân sách mới |
| E3b | depth 4 → head 4 → joint 8 | BCE | E3–E3b: ảnh hưởng của lịch chia giai đoạn |
| E4 | depth 4 → head 4 → joint 8 | Focal α=0,25, γ=2 | E3b–E4: ảnh hưởng của classification loss |

Ngân sách **16 epoch/nhánh** là lựa chọn kỹ thuật ban đầu, chưa chứng minh tối
ưu. Tất cả dùng Adam, LR 10^-4 cố định, weight decay 10^-4, batch 8, cùng
augmentation lật ngang, depth MSE + contrast MSE với trọng số 1 và cls 1.
Mỗi nhánh đi qua 61.440 lượt frame train và 7.680 minibatch. Số lần cập nhật
riêng backbone/head khác nhau theo lịch, là một phần của can thiệp staged.
So sánh strategy cũng bao gồm reset optimizer ở ranh giới stage và khôi phục
best stage; không quy riêng cho một cơ chế freeze. E2 lịch sử có head 10 epoch,
LR 10^-3; E2–E3 không phải ablation chỉ thay freeze dưới cùng ngân sách.

Focal đang có α=0,25 cho nhãn live=1, 0,75 cho attack=0. Train có tỷ lệ
attack/live 3:1; lựa chọn này không phải tự động cân bằng lớp thiểu số. Nhánh
này kiểm tra đúng cấu hình đề xuất ban đầu, không khẳng định Focal sẽ cải thiện.
Không đổi α, γ hoặc lambda dựa vào test sau khi chạy.

## Dữ liệu và quy tắc chọn

Giữ CASIA-FASD 50 người/600 video/12.000 frame, 20 frame/video và validation
subjects 4,9,14,19. Train/val/test: 192/48/360 video. Input 256×256,
`cdcn_official` normalization, depth 32×32, mean score theo video. Không đổi
split, không lấy thêm frame và không chạy lại 3DDFA.

- Manifest source SHA-256: `58fffcc2fb29649af1b8424d78b85067eefbd0321fde6b27fbd0803ef0fd7192`.
- Manifest depth SHA-256: `4c302c9039e48a8ea6baedf426b26e1b0a6663bc295c661bb71fefccdb9b37fd`.
- E1 initializer SHA-256: `679810c001e526cafed8685fe731a7d5c539fd3fb9c5a9fb31725b7dbdf57024`.

Checkpoint chọn **BCE classification trên validation thấp nhất** trong stage
head/joint, cùng quy tắc cho BCE và Focal. Stage depth chọn depth objective
thấp nhất. Ties giữ epoch đầu. Stage sau bắt đầu từ checkpoint được chọn ở stage
trước; đầu ra cuối chỉ lấy checkpoint của joint cuối. `val_loss` vẫn lưu loss
huấn luyện, `val_selection_loss` lưu tiêu chí chọn; không so trực tiếp BCE với
Focal hoặc với depth loss. Config cũ không khai báo tiêu chí vẫn dùng val_loss.

Threshold chọn từ validation theo evaluator hiện có: minimum ACER trên video,
tie-break theo implementation đã khóa. Xếp cấu hình bằng val ACER, rồi EER,
rồi AUC giảm dần, rồi BCE lựa chọn; tie hoàn toàn giữ thứ tự E3, E3b, E4.
Depth MAE và chi phí là phép mô tả hỗ trợ. Khóa cả ba run/checkpoint/config/
threshold trước khi xem test. Báo đầy đủ cả ba, giữ kết quả không cải thiện.
Test CASIA đã được xem từ lượt trước nên đây vẫn là so sánh phát triển.

## Những gì đã chuẩn bị và chưa chạy

- Config `configs/casia_e3_joint_bce.yaml`, `casia_e3b_staged_bce.yaml`,
  `casia_e4_staged_focal.yaml` giữ cùng data/initializer/budget.
- Notebook sạch `notebooks/Face_PAD_Round5_CASIA_E3_E4.ipynb` có cổng thủ công
  cho smoke, full run và test. Chưa có output train hoặc số kết quả E3/E4.
- Source ZIP chỉ gồm file đã commit, không có notebook người dùng đang sửa,
  weights, dataset hoặc raw score. Không cần push lên GitHub để dùng ZIP.
  Notebook E0 lịch sử đã có output trong Git được loại khỏi gói chạy mới;
  bản gốc không bị sửa hoặc xóa.
- Unit tests dùng dữ liệu nhân tạo để kiểm tra code; chưa phải GPU smoke CASIA.
- Extra cài đặt `.[dev]` gồm pytest và python-docx để chạy cả test tài liệu;
  việc chạy test dựng scaffold trong thư mục tạm không tiếp tục điền báo cáo.

## Việc bạn cần làm trước tiên

1. Mở Colab, chọn **File → Upload notebook**, chọn notebook Lượt 5 vừa cung cấp.
2. Chạy **chỉ các cell 0.1 đến 1.5**. Có thể dùng CPU để khôi phục và kiểm tra
   dữ liệu; cell 0.2 lấy ZIP từ `face-pad/handoffs/round5-20261016/` trên Drive,
   hoặc yêu cầu upload `DeepFace-PAD-Round5-source.zip` nếu không tìm thấy.
   Cho phép mount đúng Drive có thư mục `MyDrive/face-pad`.
3. Dừng tại kết quả **PREFLIGHT PASS**. Gửi output cell 1.5: hash manifest,
   checkpoint, số mẫu và trạng thái depth. Nếu lỗi, gửi nguyên traceback;
   không thay split, bỏ assert hoặc tải dataset khác để vượt kiểm tra.

Sau khi preflight được kiểm tra, chọn GPU (đổi runtime có thể làm mất file
local nên chạy lại setup nếu cần). Chạy tests/GPU ở cell 2.0, đổi
`RUN_SMOKE = True` ở cell 2.1 để smoke từng nhánh. Smoke dùng **toàn bộ tập train
và validation cũ** nhưng chỉ một epoch/stage; không gọi là kết quả chính và
không mở test. Xem log loss hữu hạn, kiểm tra checkpoint joint và ảnh depth.
Gửi ba smoke run ID và output checklist cell 2.2. Không dùng Run all qua cổng.

Chỉ khi smoke đạt, đổi `RUN_FULL = True` ở cell 3.1. Notebook không tự chạy lại
run hoàn tất: run khác config sẽ dừng, run chưa xong được giữ để kiểm tra. Nếu
OOM, không tự đổi batch; báo lỗi để đăng ký lại cùng batch cho cả ba nhánh.
Ngắt runtime không có nghĩa đã resume optimizer: runner chưa có resume từng
minibatch; không ghi đè run cũ. Sau full validation, gửi bảng cell 3.2. Chưa mở
test trước khi khóa kết quả validation và xác nhận cả ba run đầy đủ.

Cell 4.1 khóa hashes trước test. Cell 4.2 cần đổi `OPEN_TEST = True` riêng;
nếu score đã tồn tại sẽ đọc lại thay vì score lại. Artifact ghi trong
`face-pad/runs/` và `face-pad/reports/round5-<SOURCE_COMMIT>/` trên Drive.

## Lượt 6–8 sau đó

- **Lượt 6:** E1 và nhánh được chọn từ validation đủ ba seed (ví dụ 42,43,44)
  nếu compute cho phép; mỗi seed mới có initializer E1 đúng seed. Không dùng
  một E1 seed 42 để giả thành ba seed pipeline. Báo mean/std và đo latency lặp
  cùng GPU, cùng input, đổi thứ tự; paper khác protocol chỉ so bối cảnh.
- **Lượt 7:** paired errors theo video, subgroup có metadata, RGB/target/
  prediction/error map; webcam live/print/replay, FPS và thời gian quyết định.
  Phần webcam cần bạn có camera và vật mẫu, theo hướng dẫn sau khi chọn model.
- **Lượt 8:** khóa phiên bản cuối, artifacts, kết luận đúng phạm vi và hoàn
  thiện slide. Chỉ quay lại báo cáo đầy đủ khi bạn yêu cầu tiếp tục.
