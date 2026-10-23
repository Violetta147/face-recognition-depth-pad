# Chốt Lượt 6 ngày 22/10/2026

Phần thực nghiệm và kiểm toán Lượt 6 đã hoàn tất, gồm replication ba seed,
phép đo chi phí và bảng đối chiếu protocol paper. Đã nhận cả hai notebook
executed nguyên byte. Không còn thao tác Colab/GPU cần người dùng làm cho
Lượt 6; có thể ngắt runtime. Các commit mới chỉ ở máy cục bộ, chưa push.

## Kết quả cần trình bày

- CASIA development protocol, video mean 20 frame, split theo người
  16/4/30; đủ seed 43/44/45 và 138 epoch. Sáu model/threshold khóa trước test.
- E1 ACER 4,3210 ± 2,1623%; E3 3,7037 ± 0,6415% (mean/sample SD, ddof=1).
  Paired delta −0,6173 ± 2,6857 điểm phần trăm; E3 tốt hơn seed 43/45,
  kém hơn seed 44. Chưa chứng minh mức cải thiện ổn định.
- Cost E1/E3/E4 trên cùng phiên A100 mới, float32 batch 1, hai input
  validation thật, đủ sáu thứ tự và 1.200 mẫu/model. E3 thêm 1.265 params
  (+0,05635%); CUDA p50 thêm 0,047104 ms (+0,7961%), p95 +0,8282%.
- E3/E4 cùng kiến trúc suy luận. E4 seed 42 chỉ để đo chi phí; không gộp
  vào thống kê ba seed và không chọn lại E4 từ test.
- CDCN/UCDCN/CASO-PAD có bảng nguồn, protocol, split, unit, threshold,
  vị trí bảng/trang và PDF hash. Không lập thứ hạng chung với CASIA của nhóm.

## Điểm đọc

1. `reports/ROUND_6_RESULTS_2026-10-22.md/.json`: sáu run và kiểm toán accuracy.
2. `reports/ROUND_6_COST_RESULTS_2026-10-22.md/.json`: latency thực tế, profile,
   scope, raw hashes, pooled/per-block thống kê và cách audit lại trên CPU.
3. `reports/ROUND_6_PAPER_PROTOCOL_COMPARISON_2026-10-22.md/.json`: paper context.
4. `reports/ROUND_6_EXECUTED_NOTEBOOK_2026-10-22.json` và
   `reports/ROUND_6_COST_EXECUTED_NOTEBOOK_2026-10-22.json`: receipt notebook.

Raw cost đã lưu nguyên hash tại `artifacts/round6-cost-audit-20261022/` và
Drive `face-pad/reports/round6-cost-d316f72ff209/a100-01/`. Không có model
forward mới trong phiên kiểm toán. Code audit mới đạt 17 test liên quan;
bộ test chốt toàn repo 194 passed, 1 skipped, 67 subtests passed.

## Giới hạn và bàn giao tiếp

Đây là development evidence đã quan sát nhiều lượt; không phải blind official
benchmark. Latency chỉ thuộc forward A100 batch 1, không phải FPS webcam,
chi phí preprocess hoặc end-to-end. Hai cấu hình E1/E3 còn khác training
budget và weight decay; không quy toàn bộ thay đổi accuracy cho head.

Hai Word/report/paper lịch sử giữ nội dung đến Lượt 5. Kết quả mới là addendum
Lượt 6; chưa ghép vào Word, chưa upload hay nộp báo cáo. Không tuyên bố A/B
đã trình bày hoặc hoàn tất lịch học từ việc kiểm toán này.

Nếu người dùng tiếp tục Lượt 7, làm error analysis và webcam theo kế hoạch;
chưa triển khai hai việc đó trong Lượt 6. Không train/score lại, chọn threshold
mới, bỏ seed bất lợi hoặc đổi split từ kết quả test đã biết.

Phiên tiếp theo bắt đầu tại [bàn giao Lượt 7](ROUND7_2026-10-22.md), được rà
lại từ score/metadata/notebook đã chốt; CURRENT đã chuyển sang mục tiêu mới.
