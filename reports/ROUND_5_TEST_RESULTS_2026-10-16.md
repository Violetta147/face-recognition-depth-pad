# Lượt 5: kết quả test phát triển và kết luận ablation

Ngày đối chiếu 16/10/2026. **E3/E3b/E4 đã hoàn tất train, validation và test
đã khóa. Ở seed 42, các nhánh mới chưa giảm ACER so với E1/E2.** E3 vẫn là
cấu hình được chọn từ validation trước test; E4 có ACER test thấp nhất trong
ba nhánh mới nhưng không được đổi thành lựa chọn validation sau khi xem test.

## Phạm vi xác minh

Đọc trực tiếp `face-pad/runs/` và `reports/round5-525c80889106/` trên Drive.
Freeze hiện tại khớp bản đã lưu trước test. Hash config, checkpoint, threshold,
validation metrics và manifest của ba run đều không đổi. Score test dùng đúng
threshold validation. 7.200 frame/360 video khớp ID và nhãn manifest; mỗi video
20 frame. Mean frame → video và toàn bộ metric tính lại khớp trong sai số 10^-12.
Các CSV/JSON E0/E1/E2 hiện tại khớp byte với bản đã kiểm toán trước đó.

Không train hoặc score checkpoint lại; đây là tính lại từ score CSV đã lưu.
Script có assert `artifacts/research-audit-20261016/verify_round5_test.py` đạt
PASS. Raw score/paired CSV nằm ở `artifacts/round5-test-audit-20261016/`, bị Git
ignore. Số liệu máy đọc ở `ROUND_5_TEST_RESULTS_2026-10-16.json`.

## Kết quả trên cùng 360 video test

Tập test có 270 attack và 90 live. Đơn vị là video, ngưỡng lấy từ validation.

| Model | APCER % | BPCER % | ACER % | EER % | AUC | Live bị từ chối / 90 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| E0 MobileNetV3 | 0 | 11,1111 | 5,5556 | 2,4074 | 0,997984 | 10 |
| Official E1 | 0 | 5,5556 | **2,7778** | 2,2222 | 0,994444 | **5** |
| E2 frozen head | 0 | 5,5556 | **2,7778** | 2,2222 | 0,994321 | **5** |
| E3 joint BCE | 0 | 10,0000 | 5,0000 | 2,2222 | 0,994198 | 9 |
| E3b staged BCE | 0 | 10,0000 | 5,0000 | 3,3333 | 0,992551 | 9 |
| E4 staged Focal | 0 | 8,8889 | 4,4444 | 2,2222 | 0,996626 | 8 |

Tất cả không chấp nhận nhầm attack trong mẫu này. E3/E3b tăng ACER 2,2222 điểm
phần trăm so E1; E4 tăng 1,6667 điểm. E4 có AUC cao hơn E1, nhưng ACER tại
ngưỡng validation cao hơn: khả năng xếp hạng score và lỗi tại một ngưỡng là
hai khía cạnh khác nhau. Không chọn lại threshold trên test để làm bảng tốt hơn.

## So sánh từng video

| So sánh | Sửa lỗi | Tạo lỗi mới | Cùng sai | Cùng đúng |
| --- | ---: | ---: | ---: | ---: |
| E1 → E2 | 0 | 0 | 5 | 355 |
| E1 → E3 | 1 | 5 | 4 | 350 |
| E1 → E3b | 0 | 4 | 5 | 351 |
| E1 → E4 | 1 | 4 | 4 | 351 |
| E3 → E3b | 1 | 1 | 8 | 350 |
| E3b → E4 | 1 | 0 | 8 | 351 |

- E3/E4 sửa `casia_s39_v1` so với E1; E3b vẫn sai video này.
- Cả ba mới cùng tạo lỗi ở `casia_s36_v2`, `casia_s38_v2`, `casia_s39_v2`,
  `casia_s48_v2`. E3 tạo thêm lỗi riêng ở `casia_s32_v2`.
- Bốn lỗi cùng E1 còn lại: `casia_s21_vHR_1`, `casia_s23_v2`, `casia_s30_v2`,
  `casia_s31_v1`.
- E3–E3b giữ ACER 5% nhưng đổi video sai: staged sửa `casia_s32_v2`, làm sai
  thêm `casia_s39_v1`. Cùng ACER không có nghĩa cùng lỗi.
- E3b–E4: Focal sửa đúng một live video `casia_s39_v1`, không tạo lỗi mới,
  giảm ACER 0,5556 điểm phần trăm ở seed này; chưa vượt E1/E2.

## Nhóm quality trong manifest

Mỗi nhóm có 30 live video. Đây là nhãn `quality` của manifest, chưa phải đo
blur/ánh sáng trực tiếp từ ảnh.

| Model | Lỗi live quality=high | Lỗi live quality=low | Lỗi live quality=normal |
| --- | ---: | ---: | ---: |
| E1/E2 | 1/30 | 2/30 | 2/30 |
| E3 | 1/30 | 7/30 | 1/30 |
| E3b | 1/30 | 6/30 | 2/30 |
| E4 | 1/30 | 6/30 | 1/30 |

Lỗi mới tập trung ở nhóm `quality=low`. Đây là mô tả định lượng để chọn case
phân tích Lượt 7, không đủ để xác định nguyên nhân thị giác. Chưa xem RGB/
target/prediction của các video test sai trong phiên này.

## Kết luận đúng phạm vi

- **Head:** E2 chưa giảm lỗi so với mean depth E1 ở seed 42, thêm 1.265 params.
- **Strategy:** joint/staged BCE cùng ACER test 5%, khác danh sách lỗi và các
  metric khác; chưa có bằng chứng staged cải thiện primary metric ở seed này.
- **Loss:** Focal có cải thiện nhỏ so với staged BCE ở run này, nhưng E4 vẫn
  kém E1/E2 về ACER. Không gọi toàn bộ phương pháp cải tiến thành công.
- Validation cả ba mới hoàn hảo trên 4 người/48 video, test có lỗi trên 30
  người/360 video. Đây là khoảng cách validation → test; chưa xác định nguyên
  nhân chỉ từ bảng metric. Không đổi lambda, schedule hoặc model từ test này.

Đây là kết quả một seed trên CASIA development protocol đã được quan sát nhiều
lượt. Âm tính vẫn là kết quả nghiên cứu; giữ mọi run, checkpoint và freeze.
Bản báo cáo Word đầy đủ vẫn tạm dừng. Lượt 5 hoàn tất phần thí nghiệm/ablation;
paper draft và chi phí đầy đủ vẫn là công việc riêng chưa hoàn tất.

## Chuyển sang Lượt 6

Ứng viên lặp lại là E3 theo lựa chọn validation, đối chứng là E1. Không đổi
sang E4 bằng thứ tự test. Đã phát hiện E1 lịch sử dùng torch 2.11.0+cu128 còn
E3/E3b/E4 dùng 2.11.0+cu130. Cần giữ cùng môi trường cho đợt nhiều seed mới;
không diễn giải mọi dao động lịch sử là do seed.

Xem phương án compute tại `ROUND_6_REPLICATION_PLAN.md`. Chưa chạy thêm GPU
hoặc tạo kết quả nhiều seed trong phiên kiểm toán này.
