# Bàn giao giữa kỳ Lượt 1–3

Ngày chốt trạng thái: 21 tháng 9 năm 2026.

## Trạng thái cuối

Lượt 1, 2 và 3 đã hoàn tất trên protocol CASIA-FASD giữa kỳ. Kết quả, threshold
và locked test đã đóng băng. Slide chưa được thực hiện.

Fresh clone tại commit `1833d68` đã chạy **39 unit test, tất cả đều pass**.
Notebook hoàn chỉnh, không chứa output sinh trắc học, nằm trong repository tại commit `d5a72d9`:
`notebooks/Face_PAD_Midterm_L1_L2_L3.ipynb`.

## Kết quả chính thức

| Model | APCER | BPCER | ACER | EER | AUC |
|---|---:|---:|---:|---:|---:|
| E0 MobileNetV3 | 0,0000% | 11,1111% | **5,5556%** | **2,4074%** | **0,997984** |
| E1 CDCN + pseudo-depth | 19,2593% | **8,8889%** | 14,0741% | 11,1111% | 0,956420 |

E0 là mô hình tốt nhất ở giai đoạn giữa kỳ. E1 giảm nhẹ false reject bona fide
nhưng tăng mạnh false accept attack, đặc biệt với video replay.

## Artifact trên Google Drive

- Batch protocol: `/content/drive/MyDrive/face-pad/reports/casia-val-batch.png`.
- E0 frozen run: `/content/drive/MyDrive/face-pad/runs/CASIA_E0_BCE_5E_seed42_20260920T082941Z`.
- Depth smoke: `/content/drive/MyDrive/face-pad/reports/casia-depth-smoke.png`.
- Depth QA: `/content/drive/MyDrive/face-pad/reports/casia-depth-qa.json`.
- E1 smoke: `/content/drive/MyDrive/face-pad/runs/CASIA_E1_SMOKE_seed42_20260921T023804Z`.
- E1 full: `/content/drive/MyDrive/face-pad/runs/CASIA_E1_CDCN_seed42_20260921T024300Z`.
- E1 cases: `/content/drive/MyDrive/face-pad/reports/CASIA_E1_CDCN_seed42_20260921T024300Z-depth-cases`.
- E0–E1 comparison: `/content/drive/MyDrive/face-pad/reports/E0-vs-CASIA_E1_CDCN_seed42_20260921T024300Z.csv`.
- Face-crop demo: `/content/drive/MyDrive/face-pad/reports/casia-3ddfa-face-crop-demo.png`.
- Training curves: `/content/drive/MyDrive/face-pad/reports/e0-e1-training-curves.png`.
- Test score distributions: `/content/drive/MyDrive/face-pad/reports/e0-e1-test-score-distributions.png`.

Run E1 full chứa đầy đủ `config.yaml`, `environment.txt`,
`manifest_checksum.json`, `train_log.csv`, `best.ckpt`, validation/test frame and
video scores, `threshold.json`, `metrics.json`, `test_metrics.json` và
`depth_input_snapshot.json`.

## Quy tắc đóng băng

- Không thay threshold hoặc chọn checkpoint dựa trên test.
- Không chạy nhiều biến thể rồi chọn bằng CASIA test đã mở.
- Không commit dataset, frame, depth map, checkpoint hoặc dữ liệu sinh trắc học.
- Không thay bản notebook sạch trong Git bằng bản đã chạy trên Drive vì output có ảnh khuôn mặt.
- Thí nghiệm mới phải có ID/config mới và chọn hoàn toàn trên validation.
- Kết quả hiện tại chỉ áp dụng cho protocol CASIA giữa kỳ, chưa phải kết luận
  cross-dataset hoặc production.

## Việc còn lại cần con người thực hiện

1. Commit notebook không có output và toàn bộ tài liệu closeout đã cập nhật.
2. Giữ bản sao Drive và notebook đã chạy; có thể ngắt runtime GPU sau khi xác nhận đồng bộ.
3. Dùng các số đã đóng băng để viết báo cáo giữa kỳ và sau đó mới làm slide.
4. Chờ OULU-NPU/Replay-Attack được duyệt để chốt protocol benchmark cuối.
