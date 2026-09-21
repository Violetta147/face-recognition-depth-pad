# Rà soát hoàn thành Lượt 1–3

Ngày rà soát cuối: 21 tháng 9 năm 2026. Phạm vi gồm đặc tả nghiên cứu,
kế hoạch theo lượt, protocol CASIA-FASD, mã nguồn, unit test, pseudo-depth,
E0/E1 và toàn bộ bằng chứng runtime trên Google Drive. Slide chưa thuộc phạm vi này.

## Kết luận

| Lượt | Trạng thái | Kết luận |
|---|---|---|
| Lượt 1 | Hoàn tất cho giữa kỳ | Framing, literature, kiến trúc, metric, protocol CASIA và batch visualization thực tế đã có. Benchmark cuối vẫn chờ quyền truy cập. |
| Lượt 2 | Hoàn tất và đóng băng | Manifest sạch, E0 đã chạy, threshold chọn trên validation và locked test đã mở đúng một lần. |
| Lượt 3 | Mở lại một phần | 3DDFA queue/QA đã hoàn tất. Run E1 cũ là compact CDCN-style pilot, không phải official CDCN; cần chạy correction E1 trước khi chốt báo cáo. |

Fresh-clone verification tại commit `1833d68`: **39 passed**. Notebook hoàn chỉnh,
không chứa output sinh trắc học, đã được đưa lên GitHub tại commit `d5a72d9`.

Manifest CASIA: **12.000 frame, 600 video, 50 subject, 0 video leakage,
0 subject leakage, 0 sample ID trùng**.

## Lượt 1 — bài toán, literature và protocol

| Yêu cầu | Trạng thái | Bằng chứng / ghi chú |
|---|---|---|
| Câu hỏi nghiên cứu và biến chính | Hoàn tất | E0 RGB baseline và E1 pseudo-depth/CDCN được so sánh trên cùng protocol. |
| Literature matrix và paper cốt lõi | Hoàn tất | `reports/LITERATURE_MATRIX.md`. |
| Quy tắc direct/contextual comparison | Hoàn tất | Đặc tả và literature matrix. |
| Kiến trúc E0–E4 | Hoàn tất | Đặc tả, mã nguồn và config E0–E4 có trong repository. |
| Lịch A/B hai thành viên | Hoàn tất | Kế hoạch theo lượt. |
| Repository skeleton | Hoàn tất | Package, scripts, configs, reports và tests. |
| Protocol giữa kỳ | Hoàn tất | CASIA-FASD, 20 frame/video; validation tách subject; source test giữ khóa. |
| Batch visualization | Hoàn tất | `/content/drive/MyDrive/face-pad/reports/casia-val-batch.png`. |
| Face-crop demo | Hoàn tất | `/content/drive/MyDrive/face-pad/reports/casia-3ddfa-face-crop-demo.png`; 8 vùng mặt được phát hiện và crop đúng. |
| Benchmark cuối có license | Đang chờ bên ngoài | OULU-NPU và Replay-Attack đang chờ duyệt; không chặn báo cáo CASIA giữa kỳ. |
| Slide | Hoãn chủ động | Chỉ thực hiện sau khi đóng băng dữ kiện Lượt 1–3. |

## Lượt 2 — dữ liệu, metric và E0

| Yêu cầu | Trạng thái | Bằng chứng / ghi chú |
|---|---|---|
| Manifest và leakage checks | Hoàn tất | Validator xác nhận không video/subject leakage. |
| APCER/BPCER/ACER/EER/AUC | Hoàn tất | `src/deepface_pad/metrics.py` và unit tests. |
| E0 MobileNetV3 | Hoàn tất | `CASIA_E0_BCE_5E_seed42_20260920T082941Z`, 5 epoch, A100. |
| Threshold validation | Hoàn tất | `0.9900876432657242`, khóa trước test. |
| Locked test | Hoàn tất | APCER 0%, BPCER 11,1111%, ACER 5,5556%, EER 2,4074%, AUC 0,997984. |
| Error analysis | Hoàn tất | 0/270 attack false accept; 10/90 bona fide false reject. |
| Artifact | Hoàn tất ngoài Git | Config, environment, checksum, checkpoint, logs và raw scores nằm trên Drive. |
| Training curve và score distribution | Hoàn tất | `/content/drive/MyDrive/face-pad/reports/e0-e1-training-curves.png` và `/content/drive/MyDrive/face-pad/reports/e0-e1-test-score-distributions.png`. |

## Lượt 3 — pseudo-depth và CDCN E1

### Pseudo-depth và QA

- Queue/ledger có thể resume và ghi trạng thái atomically.
- 9.000 attack frame dùng zero target theo protocol.
- 3.000 bona fide frame được xử lý bằng 3DDFA V2; smoke 50 frame thành công,
  không có persistent failure được giữ lại.
- Attack không-zero, live all-zero, file hỏng và NaN/Inf đều bị QA từ chối.
- Provenance khóa implementation/config/checksum và worker script.
- Smoke image: `/content/drive/MyDrive/face-pad/reports/casia-depth-smoke.png`.
- QA report: `/content/drive/MyDrive/face-pad/reports/casia-depth-qa.json`.

### E1-Lite smoke (pilot lịch sử)

- Run: `CASIA_E1_SMOKE_seed42_20260921T023804Z`.
- Một epoch hoàn tất; loss hữu hạn, checkpoint và depth snapshot tồn tại.
- Validation smoke: APCER 52,7778%, BPCER 8,3333%, ACER 30,5556%,
  EER 33,3333%, AUC 0,689815.
- Smoke chỉ là kiểm tra pipeline, không phải kết quả mô hình cuối.

### E1-Lite full (pilot lịch sử, không phải official CDCN)

- Run: `CASIA_E1_CDCN_seed42_20260921T024300Z`.
- 30 epoch; train loss giảm từ `0.383147` xuống `0.085622`, validation loss
  giảm từ `0.335765` xuống mức tốt nhất `0.084825` tại epoch 30.
- Threshold validation khóa: `0.0412299589253962`.
- Validation: APCER 5,5556%, BPCER 8,3333%, ACER 6,9444%,
  EER 8,3333%, AUC 0,981481.
- Locked test: APCER 19,2593%, BPCER 8,8889%, ACER 14,0741%,
  EER 11,1111%, AUC 0,956420.
- Locked test tương ứng 52/270 attack false accept và 8/90 bona fide false reject.
- Failure chính: `video_replay/low` 12/30, `video_replay/high` 10/30,
  `warped_photo/high` 9/30; bona fide `live/low` 6/30.
- Depth cases: `/content/drive/MyDrive/face-pad/reports/CASIA_E1_CDCN_seed42_20260921T024300Z-depth-cases`.
- Face-crop demo: `/content/drive/MyDrive/face-pad/reports/casia-3ddfa-face-crop-demo.png`.
- Training curves: `/content/drive/MyDrive/face-pad/reports/e0-e1-training-curves.png`.
- Test score distributions: `/content/drive/MyDrive/face-pad/reports/e0-e1-test-score-distributions.png`.

## So sánh lịch sử E0–E1-Lite pilot

| Model | APCER | BPCER | ACER | EER | AUC |
|---|---:|---:|---:|---:|---:|
| E0 MobileNetV3 | 0,0000% | 11,1111% | **5,5556%** | **2,4074%** | **0,997984** |
| E1-Lite compact CDCN-style + pseudo-depth | 19,2593% | **8,8889%** | 14,0741% | 11,1111% | 0,956420 |

E1-Lite cải thiện BPCER 2,2222 điểm phần trăm nhưng làm APCER tăng 19,2593 điểm
phần trăm và ACER tăng **8,5185 điểm phần trăm**. Trên protocol CASIA giữa kỳ,
E0 là mô hình tốt nhất. Pseudo-depth E1 học được tín hiệu hình học nhưng chưa tổng
quát hóa tốt với replay attack và live chất lượng thấp.

Comparison CSV:
`/content/drive/MyDrive/face-pad/reports/E0-vs-CASIA_E1_CDCN_seed42_20260921T024300Z.csv`.

## Tính hợp lệ và giới hạn diễn giải

- E0 và E1 dùng cùng manifest, sampling, input convention và video aggregation.
- Mỗi threshold được chọn trên validation rồi khóa trước test.
- Test E1 chỉ được score sau khi threshold validation đã được ghi nhận.
- Không dùng test để retune E1 hoặc chọn epoch.
- CASIA-FASD là dataset tạm thời cho giữa kỳ; kết quả chưa chứng minh khả năng
  tổng quát hóa cross-dataset hoặc hiệu năng production.
- Một E1-50 trong tương lai phải được xem là thí nghiệm mới và chọn hoàn toàn bằng
  validation; test hiện tại không còn là holdout chưa quan sát cho việc phát triển đó.

## Việc còn lại để đóng lại Lượt 3

1. Chạy `Face_PAD_Official_CDCN_E1_Rerun.ipynb`, qua smoke gate và chọn checkpoint chỉ bằng validation.
2. Chỉ sau khi config/checkpoint/threshold đã khóa mới score CASIA test đúng một lần.
3. Thay bảng E1-Lite pilot bằng official-E1 trong kết luận giữa kỳ; vẫn giữ pilot như lịch sử kỹ thuật.
4. Commit notebook **không có output** và tài liệu closeout đã đồng bộ lên GitHub.
5. Giữ notebook đã chạy, raw data, depth, checkpoint và biometric artifacts trên Drive; không đưa bản notebook có ảnh khuôn mặt lên Git.
6. Sau đó mới viết báo cáo/slide và chờ benchmark cuối được duyệt.
