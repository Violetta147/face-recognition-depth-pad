# Bàn giao giữa kỳ Lượt 1–3

Ngày chốt trạng thái: 21 tháng 9 năm 2026.

## Trạng thái cuối

Lượt 1, Lượt 2 và Lượt 3 đã hoàn tất. Run compact cũ giữ nhãn **E1-Lite Pilot**;
kết quả E1 chính thức dùng kiến trúc/loss official CDCN đã kiểm chứng với upstream.
Checkpoint và threshold được chọn trên validation trước khi locked test mở một lần.

Unit-test gate đã pass trong correction workflow trên Colab. Port official CDCN
được kiểm chứng số học với upstream: 73 state tensors khớp, `max_abs_error=0.0`.
Hai notebook trong Git đều sạch output: notebook lịch sử L1–L3 và notebook
correction `notebooks/Face_PAD_Official_CDCN_E1_Rerun.ipynb`.

## Kết quả đóng băng

| Model | APCER | BPCER | ACER | EER | AUC |
|---|---:|---:|---:|---:|---:|
| E0 MobileNetV3 | 0,0000% | 11,1111% | **5,5556%** | **2,4074%** | **0,997984** |
| E1-Lite Pilot | 19,2593% | 8,8889% | 14,0741% | 11,1111% | 0,956420 |
| Official CDCN E1 | 0,0000% | **5,5556%** | **2,7778%** | **2,2222%** | 0,994444 |

Official CDCN E1 giảm ACER 2,7778 điểm phần trăm so với E0, không false-accept
attack và giảm false-reject bona fide từ 10 xuống 5 video. Đây là một seed trên
CASIA development protocol, chưa phải kết luận cross-dataset.

## Artifact lịch sử/pilot trên Google Drive

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

## Artifact official-E1 dùng cho báo cáo

- Official E1 smoke: `/content/drive/MyDrive/face-pad/runs/CASIA_E1_CDCN_OFFICIAL_SMOKE_seed42_20260921T113339Z`.
- Official E1 full: `/content/drive/MyDrive/face-pad/runs/CASIA_E1_CDCN_OFFICIAL_seed42_20260921T114029Z`.
- Official E1 cases: `/content/drive/MyDrive/face-pad/reports/CASIA_E1_CDCN_OFFICIAL_seed42_20260921T114029Z-depth-cases`.
- Official comparison: `/content/drive/MyDrive/face-pad/reports/E0-vs-CASIA_E1_CDCN_OFFICIAL_seed42_20260921T114029Z.csv`.
- Official training curves: `/content/drive/MyDrive/face-pad/reports/e0-official-e1-training-curves.png`.
- Official test score distributions: `/content/drive/MyDrive/face-pad/reports/e0-official-e1-test-score-distributions.png`.

Run official E1 full chứa đầy đủ `config.yaml`, `environment.txt`,
`manifest_checksum.json`, `model_provenance.json`, `train_log.csv`, `best.ckpt`,
validation/test frame and video scores, `threshold.json`, `metrics.json`,
`test_metrics.json` và `depth_input_snapshot.json`.

## Quy tắc đóng băng

- Không thay threshold hoặc chọn checkpoint dựa trên test.
- Không chạy nhiều biến thể rồi chọn bằng CASIA test đã mở.
- Không commit dataset, frame, depth map, checkpoint hoặc dữ liệu sinh trắc học.
- Không thay bản notebook sạch trong Git bằng bản đã chạy trên Drive vì output có ảnh khuôn mặt.
- Thí nghiệm mới phải có ID/config mới và chọn hoàn toàn trên validation.
- Kết quả hiện tại chỉ áp dụng cho protocol CASIA giữa kỳ, chưa phải kết luận
  cross-dataset hoặc production.

## Việc còn lại cần con người thực hiện

1. Viết báo cáo giữa kỳ rồi mới dựng slide.
2. Chờ OULU-NPU/Replay-Attack được duyệt để chốt protocol benchmark cuối.
3. E2–E4 tiếp tục ở các lượt sau, không thuộc điều kiện hoàn tất Lượt 1–3.
