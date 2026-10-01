# Kiểm tra backbone và gỡ Lite/Pilot — 01/10/2026

## Kết luận kiểm tra

E2 đã báo cáo không kế thừa backbone Lite/Pilot:

- `configs/casia_e2_official_head_frozen.yaml` chọn `cdcn_official_head`.
- `build_model` tạo `OfficialCDCNWithDepthHead`, có `backbone = OfficialCDCN(theta)`.
- Config nạp `CASIA_E1_CDCN_OFFICIAL_seed42_20260921T114029Z/best.ckpt`.
- Notebook Lượt 4 kiểm tra config/manifest E1, tensor backbone, predicted depth,
  tái tính E1 validation, và backbone bất biến sau train.
- Log người dùng cung cấp báo PASS các kiểm tra này; SHA256 E1 được báo cáo là
  `679810c001e526cafed8685fe731a7d5c539fd3fb9c5a9fb31725b7dbdf57024`.

Mã/config/notebook được kiểm tra trực tiếp trong workspace. Checkpoint và raw
CSV/JSON của run Colab chưa được tải về để kiểm toán độc lập.

Sai sót còn sót trước khi dọn: template E1/E2 chung và E3/E4 vẫn dùng model compact.
Chúng không phải config của E2 CASIA đã chạy, nhưng có thể dẫn đến dùng sai backbone
ở các lượt tiếp theo. Tên phương pháp `CDCN MT Lite` trong plan/đặc tả cũng gây nhầm.

## Đã dọn

- Xóa `src/deepface_pad/models/cdcn.py`: model compact, lớp CDC cũ và wrapper Lite.
- Xóa `configs/casia_e1_cdcn.yaml`, `configs/casia_e1_smoke.yaml` và notebook
  `Face_PAD_Midterm_L1_L2_L3.ipynb` có nhánh train/chọn run Pilot.
- Tách `DepthHead` sang `src/deepface_pad/models/depth_head.py`. Đây là bộ phân loại
  được đề xuất, không phải backbone CDCN. Giữ nguyên cấu trúc, 1.265 tham số,
  tên tensor checkpoint và phép tính.
- Gỡ export/nhánh tạo model Lite; tên model cũ báo lỗi rõ ràng, không tự chuyển
  một checkpoint Lite sang Official CDCN.
- Template E1/E2/E3/E4 dùng Official CDCN, normalization official; E1/E3/E4 dùng
  official depth loss. E2 yêu cầu checkpoint Official E1. E3/E4 vẫn chưa có kết quả
  benchmark; việc đổi template không phải một thí nghiệm đã chạy.
- Cập nhật README, COLAB, đặc tả, plan và runbook Lượt 4.
- Builder E1 sinh `Face_PAD_Official_CDCN_E1_Clean.ipynb`, chỉ so sánh E0/Official E1.
  Notebook E1 đã chạy và đang có thay đổi của người dùng được giữ nguyên.

Kiến trúc Official CDCN, config CASIA E1/E2 đã chạy và notebook Lượt 4 không đổi.
Không cần train lại E1/E2 vì việc tách head không đổi phép tính hoặc checkpoint schema.
ZIP source Lượt 4 đã phát hành trước đây là snapshot cũ, vẫn có Lite; nếu dùng source
đã dọn, cần lấy checkout mới hoặc archive commit mới, không nhầm hai snapshot.

## Lưu bằng chứng

Các báo cáo audit lịch sử giữ tên/số đo Pilot để giải thích nguồn gốc và tránh
nhầm số đó với Official E1. Git history có thể khôi phục mã cũ. Dọn lần này chỉ
thao tác repository local; không xóa run/checkpoint trên Google Drive.

## Kiểm chứng

Test bao gồm:

- Nạp E1 official vào E2, khớp tensor và depth, khóa cả weight lẫn BatchNorm.
- Run E2 synthetic qua train/checkpoint/validation/threshold.
- Từ chối state dict Pilot và tên model đã gỡ.
- Head tách ra nạp đúng schema cũ, cho logit giống hệt và giữ 1.265 tham số.
- Tất cả config depth đang hoạt động chọn model/normalization/loss official.
- Notebook E1 sạch và Lượt 4 là Python hợp lệ, không có output, không chọn run Pilot.

Kết quả sau khi dọn: **55 tests passed**; `git diff --check` không có lỗi.
Đây là kiểm chứng mã local, không phải đánh giá lại model trên CASIA.
