# Lượt 5: full validation E3, E3b và E4

Cập nhật sau thời điểm freeze: test đã hoàn tất và được kiểm toán, xem
`ROUND_5_TEST_RESULTS_2026-10-16.md`. Nội dung bên dưới giữ bối cảnh trước test.

Ngày đối chiếu 16/10/2026. **Cả ba full run hoàn tất 16 epoch; lựa chọn từ
validation là E3. Đã khóa các artifact trước test; chưa có kết quả test của
ba nhánh tại thời điểm khóa.** Source Colab giữ commit `525c80889106c06525f5b758e8725c8ac9cee856`.

## Nguồn và kiểm tra

Đọc trực tiếp `G:/My Drive/face-pad/runs/`, sao chép artifact vào
`artifacts/round5-full-audit-20261016/`. Script có assert
`artifacts/research-audit-20261016/verify_round5_full.py` đã đạt PASS.
Kết quả máy đọc lưu ở `ROUND_5_FULL_VALIDATION_2026-10-16.json`.

- Config khớp đăng ký trước chạy; cùng seed 42, manifest, 12.000 hash depth
  target và hash initializer E1. Mỗi nhánh đủ 16 epoch theo lịch đăng ký.
- Các log/checkpoint hữu hạn. Checkpoint mỗi stage khớp minimum tiêu chí chọn
  của chính stage đó. `best.ckpt` byte-identical best của joint cuối.
- E3b/E4 giữ nguyên cả 73 tensor backbone trong head stage; head được cập nhật,
  sang joint backbone được cập nhật. Các checkpoint vẫn được lưu đầy đủ.
- 960 frame validation khớp ID/nhãn; mean frame → 48 video và metrics/threshold
  tính lại khớp file lưu trong sai số 10^-12. BCE từ score khớp selection value
  trong sai số 10^-6. `validation.csv` khớp ba run và lựa chọn E3.
- Tính lại MAE từ `depth_val_errors.csv` khớp JSON trong sai số 10^-12, gồm
  mẫu số mask. Hash checkpoint và manifest trong JSON khớp file thực tế.
- Không retrain, không chạy inference depth mới và không score test trong
  phiên kiểm tra này. Việc tính lại MAE dùng raw error CSV đã xuất từ Colab.

## Classification validation

| Nhánh | Run ID | Epoch chọn trong joint / toàn lịch | BCE chọn | Threshold |
| --- | --- | --- | ---: | ---: |
| E3 | `CASIA_E3_CDCN_OFFICIAL_JOINT_BCE_seed42_20261015T203645Z` | 10 / 10 | 0,0109019823 | 0,8496189594 |
| E3b | `CASIA_E3B_CDCN_OFFICIAL_STAGED_BCE_seed42_20261015T204943Z` | 2 / 10 | 0,0145661915 | 0,7518128157 |
| E4 | `CASIA_E4_CDCN_OFFICIAL_STAGED_FOCAL_seed42_20261015T210039Z` | 6 / 14 | 0,0873854375 | 0,4186254457 |

APCER, BPCER, ACER và EER của cả ba bằng 0; AUC bằng 1 trên 48 video validation
(36 attack, 12 live). E1/E2 trước đó cũng đạt ACER validation 0. Quy tắc đã đăng
ký phân định ACER → EER → AUC → BCE; vì ba metric đầu hòa nên E3 được chọn
bằng BCE thấp nhất. Chưa chứng minh cải thiện ACER hay ưu thế tổng quát của
joint/staged/Focal. Không dùng test để thay lựa chọn này.

`selected_epoch` là epoch trong joint, không phải tổng số epoch đã train. E3b
chọn joint epoch 2 sau depth 4 + head 4, tương ứng global epoch 10; E4 chọn
joint epoch 6, tương ứng global epoch 14. Cả ba vẫn train đủ 16 epoch.

## Depth validation

MAE không có đơn vị khoảng cách thật. Target là pseudo-depth đã qua cùng
PadDataset normalization; prediction không clamp. Mỗi nhánh dùng 720 attack
frame/36 video, 240 live frame/12 video. Mask live `target > 10^-6` gồm 203.982
pixel. Attack target toàn zero nên masked MAE attack không xác định, lưu null.

| Nhánh | MAE toàn ảnh attack | MAE toàn ảnh live | MAE trên mask live |
| --- | ---: | ---: | ---: |
| E3 | 0,0179445140 | 0,0984287557 | 0,1170618922 |
| E3b | 0,0166461237 | 0,1044202378 | 0,1240893675 |
| E4 | 0,0078091271 | 0,1307596611 | 0,1558457489 |

E3 có sai số live thấp nhất trong ba checkpoint được chọn, cả toàn ảnh lẫn
mask. E4 có sai số attack thấp nhất nhưng sai số live cao nhất. Các số này
mô tả sự đánh đổi ở validation một seed, không chứng minh Focal cải thiện mọi
mặt. Chưa có MAE E1/E2 theo cùng phép đo để kết luận joint giữ depth tốt hơn
đối chứng. MAE là mô tả hỗ trợ, không thay tiêu chí chọn classification.

## Freeze và bước tiếp theo

Đã ghi `face-pad/reports/round5-525c80889106/comparison_freeze.json` trên Drive,
trước khi có test artifact. File lưu source commit, `selection_source:
validation`, `selected_variant: E3`, ba run ID và SHA-256 của config, checkpoint,
threshold, validation metrics và manifest checksum. Script freeze kiểm tra lại
hash hiện tại và không ghi đè freeze khác nội dung.

1. Chạy cell 4.1 để notebook kiểm tra freeze khớp trạng thái hiện tại.
2. Sau khi cell đó pass, cell 4.2 đổi `OPEN_TEST = True` rồi chạy. Notebook
   score cả ba run tại ngưỡng validation đã khóa, không chọn lại ngưỡng test.
3. Gửi bảng `development-test.csv`/output cell 4.2. Giữ E3 là lựa chọn validation
   dù thứ tự test có thể khác. Không sửa hyperparameter từ kết quả test.

Sau đó đối chiếu E0/E1/E2 với ba nhánh mới, phân tích paired errors và chi phí,
chuẩn bị Lượt 6 nhiều seed. CASIA test đã được quan sát từ lượt trước, nên đây
vẫn là kết quả phát triển của nhóm. Báo cáo Word đầy đủ tiếp tục tạm dừng.
