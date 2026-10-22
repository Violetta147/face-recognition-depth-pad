# Kiểm tra smoke E3, E3b và E4 trên CASIA

Ngày 16/10/2026: **cổng smoke kỹ thuật đạt; có thể chạy full validation theo
đăng ký hiện tại. Chưa có kết quả full E3/E3b/E4 và chưa mở test.**

Source Colab: `525c80889106c06525f5b758e8725c8ac9cee856`. Environment.txt ghi
Python 3.13.15, torch 2.11.0+cu130, device CUDA. Người dùng báo GPU NVIDIA
A100-SXM4-40GB; tên GPU chưa được ghi tự động trong environment.txt.

## Run đã đối chiếu trực tiếp trên Drive

| Nhánh | Run ID | Lịch smoke |
| --- | --- | --- |
| E3 | `CASIA_E3_CDCN_OFFICIAL_JOINT_BCE_SMOKE_seed42_20261015T201251Z` | joint 1 |
| E3b | `CASIA_E3B_CDCN_OFFICIAL_STAGED_BCE_SMOKE_seed42_20261015T201352Z` | depth 1 → head 1 → joint 1 |
| E4 | `CASIA_E4_CDCN_OFFICIAL_STAGED_FOCAL_SMOKE_seed42_20261015T201557Z` | depth 1 → head 1 → joint 1 |

Raw artifact được sao chép vào `artifacts/round5-smoke-audit-20261016/`, kiểm
tra bằng script có assert `verify_round5_smoke.py` ở thư mục audit trước.
Kết quả máy đọc ở `ROUND_5_SMOKE_AUDIT_2026-10-16.json`. Raw score, checkpoint
và ảnh người dùng gửi không được commit.

## Các điều kiện đã đạt

- Config khớp JSON đăng ký và đúng source commit; hash manifest, initializer
  E1 và danh sách 12.000 hash depth map khớp E1.
- Các loss và mọi tensor checkpoint hữu hạn; đúng số epoch/stage.
- `best.ckpt` byte-identical checkpoint joint cuối. Metadata và selection
  value khớp log, tiêu chí classification BCE đúng.
- E3b/E4: cả 73 tensor backbone, gồm buffer BatchNorm, giống hệt trước/sau
  stage head; head thay đổi. Sang joint, backbone thay đổi.
- 960 frame validation đúng ID/nhãn của manifest; mean 20 frame/video và metric
  của 48 video tính lại khớp file lưu trong sai số 10^-12.
- BCE tính lại từ frame score khớp selection loss trong sai số 10^-6.
  Threshold từ validation; không có test artifact trong ba run.

## Số đo smoke và giới hạn

| Nhánh | BCE validation joint cuối | Ngưỡng validation | ACER video % | AUC video | Frame sai / 960 |
| --- | ---: | ---: | ---: | ---: | ---: |
| E3 | 0,4893147166 | 0,5008602113 | 0 | 1 | 16 |
| E3b | 0,2290714325 | 0,4941986546 | 0 | 1 | 16 |
| E4 | 0,3296635680 | 0,3917343780 | 0 | 1 | 11 |

APCER/BPCER/EER video của cả ba đều bằng 0. ERROR/CORRECT trên panel ảnh dùng
điểm một frame tại ngưỡng video; video vẫn có thể đúng sau lấy mean dù có frame
ERROR. Frame error là mô tả hỗ trợ, không thay metric video.

E3 smoke một epoch, staged ba epoch; không dùng bảng này để xếp hạng strategy.
Validation E1/E2 trước đó cũng đạt ACER 0, nên smoke chưa chứng minh cải tiến.
Loss Focal khác thang BCE; tiêu chí chọn chung nằm ở `val_selection_loss`.

Ảnh người dùng gửi cho thấy predicted depth còn nhiều mảng khác target ở các
frame live được chọn. Các ảnh được chọn theo lỗi/gần ngưỡng, nhiều frame cùng
video, không phải mẫu ngẫu nhiên toàn validation. Chưa có MAE depth CASIA của
smoke. Không quy nguyên nhân thị giác hoặc loss chỉ từ những panel này; full
run sẽ xuất MAE định lượng. Các ảnh lịch sử được giữ nguyên.

## Bước tiếp theo

1. Trong cùng phiên Colab, cell 3.1 đổi `RUN_FULL = True` rồi chạy.
2. Mỗi full run bắt đầu riêng từ E1, không tiếp tục weights smoke. Giữ E3 joint
   16; E3b/E4 depth 4 → head 4 → joint 8, cùng LR 10^-4 và batch 8.
3. Chạy cell 3.2, gửi bảng validation, run ID và ba `depth_val_metrics.json`.
4. Dừng sau cell 3.2, giữ `OPEN_TEST = False` để kiểm tra validation và freeze.

Giữ gói source commit 525c808 trên Colab; cập nhật tài liệu không đổi code/config
đăng ký. Nếu cell lỗi, giữ run dở và gửi nguyên traceback; không tự đổi config.
Hướng dẫn đầy đủ ở `ROUND_5_CASIA_RUNBOOK.md`.
