# Kế hoạch nghiên cứu và báo cáo luân phiên cho nhóm hai người

**Đề tài:** Real Time Face Recognition with Depth Supervised Presentation Attack Detection  
**Quy mô:** 2 thành viên  
**Số lượt chuẩn:** 8 lượt báo cáo  
**Mục tiêu:** Mỗi lượt có tiến bộ nghiên cứu quan sát được và tích lũy trực tiếp cho báo cáo giữa kỳ hoặc paper  
**Đặc tả nghiên cứu:** [DAC_TA_HE_THONG_NHAN_DIEN_KHUON_MAT_PAD_DEPTH_MAP.md](DAC_TA_HE_THONG_NHAN_DIEN_KHUON_MAT_PAD_DEPTH_MAP.md)

---

## 1. Nguyên tắc vận hành

### 1.1 Luân phiên báo cáo

- Thành viên A báo cáo các lượt 1, 3, 5 và 7.
- Thành viên B báo cáo các lượt 2, 4, 6 và 8.
- Cả hai đều phải có mặt ở mọi lượt.
- Người không đứng thuyết trình phụ trách mở demo, theo dõi thời gian, ghi câu hỏi và bổ sung khi được hỏi.
- Cả hai phải hiểu toàn bộ pipeline; việc luân phiên chỉ thay người dẫn dắt phần trình bày.

| Lượt | Người báo cáo chính | Người hỗ trợ |
|---:|---|---|
| 1 | A | B chạy demo và ghi phản hồi |
| 2 | B | A chạy demo và ghi phản hồi |
| 3 | A | B chạy demo và ghi phản hồi |
| 4 | B | A chạy demo và ghi phản hồi |
| 5 | A | B chạy demo và ghi phản hồi |
| 6 | B | A chạy demo và ghi phản hồi |
| 7 | A | B chạy demo và ghi phản hồi |
| 8 | B | A chạy demo và ghi phản hồi |

Nếu số lượt thực tế nhiều hơn tám, tiếp tục xen kẽ A và B. Nếu ít hơn, ghép các lượt nhưng không để một người báo cáo hai lần liên tiếp.

### 1.2 Ưu tiên nghiên cứu

Thứ tự ưu tiên của nhóm:

1. Protocol và metric đúng.
2. Reproduce CDCN baseline.
3. Cải tiến CDCN MT Lite.
4. Ablation và nhiều seed.
5. So sánh với paper.
6. Error analysis.
7. Webcam demo.
8. ArcFace integration.

Không làm web app, mobile app hoặc giao diện cầu kỳ trước khi hoàn thành mục 1 đến 6.

### 1.3 Cấu trúc một lượt báo cáo

Từ lượt tiếp theo, báo cáo nên dài 8 đến 12 phút:

1. **1 phút:** nhắc câu hỏi nghiên cứu và tiến độ trước đó.
2. **2 phút:** literature hoặc kiến thức mới liên quan trực tiếp.
3. **3 phút:** phương pháp hoặc thí nghiệm đã làm.
4. **2 phút:** số liệu, figure và demo.
5. **1 phút:** nhận xét, lỗi và việc tiếp theo.
6. **Phần còn lại:** câu hỏi của giảng viên.

Không dành phần lớn thời gian để đọc code. Chỉ mở code khi cần chứng minh loss, split, metric hoặc modification.

---

## 2. Việc cần làm ngay cho lượt báo cáo tiếp theo

Giảng viên yêu cầu bổ sung ngay ba slide. Ba slide này là phần cố định của lượt 1 và được cập nhật ở các lượt sau.

### Slide 1 Các phương pháp học máy hiện đại cho Face PAD

**Tiêu đề:** Các hướng tiếp cận hiện đại cho RGB Face Presentation Attack Detection

**Nội dung trên slide:**

| Hướng | Ý tưởng | Điểm mạnh | Hạn chế |
|---|---|---|---|
| Lightweight binary CNN | MobileNet hoặc EfficientNet phân loại live và spoof | Nhanh, dễ train | Dễ học shortcut |
| Pixel wise hoặc depth supervision | Dự đoán depth map, mask hoặc reflection map | Có tín hiệu cục bộ, dễ giải thích hơn | Pseudo label có sai số |
| CDC và descriptive operators | Học gradient, texture và chi tiết cục bộ | Phù hợp dấu hiệu spoof | Cần custom layer |
| Transformer và foundation model | Học quan hệ dài hạn hoặc biểu diễn tiền huấn luyện | Có tiềm năng tổng quát | Tốn compute, dễ vượt phạm vi nhóm |
| Domain generalization và contrastive learning | Học đặc trưng ít phụ thuộc dataset | Hướng nghiên cứu mạnh | Cần nhiều domain và protocol phức tạp |

**Hình nên dùng:** một trục tiến hóa từ binary CNN đến depth CDC rồi adaptive operator hoặc transformer.

**Điều người báo cáo phải nói:**

- Nhóm biết các hướng mới, nhưng không triển khai tất cả.
- Với hai thành viên, depth supervised CDC là điểm cân bằng giữa khả năng nghiên cứu và khả năng hoàn thành.

### Slide 2 Phương pháp nhóm chọn và cải tiến

**Tiêu đề:** Từ CDCN depth only đến CDCN MT Lite

**Nội dung trên slide:**

```text
RGB face
   -> CDCN backbone
   -> predicted depth map
        -> mean depth score                  Baseline
        -> lightweight learned depth head   Nhóm đề xuất thử
```

Thêm ba dòng:

- Baseline: CDCN với absolute và contrastive depth loss.
- Modification: classifier nhỏ đọc predicted depth map.
- Thử nghiệm: BCE so với Focal Loss; end-to-end so với staged training.

**Câu hỏi nghiên cứu đặt cuối slide:**

> Learned depth head có giảm ACER so với fixed mean-depth score mà không tăng đáng kể latency hay không?

**Điều người báo cáo phải nói:**

- Modification nhỏ, cô lập được và có ablation.
- Nhóm chưa gọi đây là phương pháp mới cho đến khi hoàn thành literature review và thí nghiệm.

### Slide 3 Paper gần nhất và bộ tiêu chí đánh giá

**Tiêu đề:** Đối chiếu nghiên cứu và kế hoạch đánh giá

Chia slide thành hai cột.

**Cột trái Paper:**

- CDCN, CVPR 2020: baseline depth supervision.
- UCDCN, 2024: gần nhất về cơ chế depth, classifier, Focal Loss và staged training.
- CASO-PAD, Scientific Reports, 16 tháng 9 năm 2026: paper mới nhất gần bài toán, dùng MobileNetV3 và content-adaptive operator.

**Cột phải Metrics:**

- APCER.
- BPCER.
- ACER.
- EER.
- ROC AUC.
- Params, FLOPs, latency và FPS.

**Dòng cảnh báo cuối slide:**

> Chỉ so trực tiếp khi cùng dataset, protocol, split, đơn vị đánh giá và cách chọn threshold.

**Nguồn đặt ở chân slide:**

- <https://openaccess.thecvf.com/content_CVPR_2020/html/Yu_Searching_Central_Difference_Convolutional_Networks_for_Face_Anti-Spoofing_CVPR_2020_paper.html>
- <https://link.springer.com/article/10.1007/s40747-024-01397-0>
- <https://www.nature.com/articles/s41598-026-67944-6>

### Artifact phải có trước lượt tiếp theo

- [ ] Deck giữa kỳ Lượt 1 đến Lượt 3 chỉ làm sau khi bằng chứng E1 đầy đủ.
- [x] Literature matrix có ít nhất 5 paper.
- [x] Deadline chốt benchmark chính thức là 27 tháng 9 năm 2026; CASIA chỉ dùng giữa kỳ.
- [x] Sơ đồ CDCN MT Lite.
- [x] Bảng metric có công thức APCER, BPCER và ACER.
- [x] Dataset batch visualization đã xuất tại `/content/drive/MyDrive/face-pad/reports/casia-val-batch.png`.
- [x] Lịch A/B luân phiên đã chốt trong kế hoạch; sẽ đưa lên slide sau khi hoàn tất dữ liệu.

---

## 3. Gói báo cáo giữa kỳ

Báo cáo giữa kỳ không cần pipeline cuối. Gói tối thiểu phải cho thấy nhóm đã chuyển từ ý tưởng sang nghiên cứu có thể đo được.

### 3.1 Nội dung slide giữa kỳ

1. Bài toán và threat model.
2. Ba slide bắt buộc về phương pháp hiện đại, phương pháp nhóm và paper gần nhất.
3. Dataset và official protocol.
4. CDCN baseline và pseudo depth.
5. Modification CDCN MT Lite.
6. Bộ metric và quy tắc threshold.
7. Kết quả đầu tiên của E0 hoặc E1.
8. Failure cases đầu tiên.
9. Ma trận thí nghiệm E0 đến E4.
10. Tiến độ và rủi ro.

### 3.2 Artifact giữa kỳ

- Manifest train, validation và test.
- Validator không báo leakage.
- Metric script có unit test.
- Ít nhất một model có raw validation score.
- Một bảng metric thật, không dùng số minh họa.
- Pseudo depth visualization hoặc báo cáo rõ blocker.
- Repository có lệnh tái lập run.

### 3.3 Phần mỗi thành viên phải trả lời được

**A**

- Dataset và protocol chia thế nào?
- Vì sao không split theo frame?
- APCER, BPCER và ACER khác gì nhau?
- Số paper có thực sự so trực tiếp được không?

**B**

- CDC khác convolution thường ở đâu?
- Pseudo depth được tạo thế nào?
- Classification head thay đổi baseline ra sao?
- Vì sao cần ablation và staged training?

---

## 4. Lượt 1 Chốt bài toán, literature và protocol

**Người báo cáo:** A  
**Phiên bản:** R0 Research framing

### Mục tiêu

Thuyết phục giảng viên rằng nhóm đã thu hẹp đúng trọng tâm, nắm các hướng hiện đại, có paper gần nhất và có kế hoạch đánh giá giống nghiên cứu.

### Công việc của A

- Đọc CDCN, UCDCN và phần metric của protocol dataset.
- Viết literature matrix.
- Chốt quy tắc direct comparison và contextual comparison.
- Chuẩn bị slide 1 và slide 3.
- Xin hoặc tải dataset theo đúng license.

### Công việc của B

- Vẽ kiến trúc CDCN MT Lite.
- Chuẩn bị slide 2.
- Chạy detector và crop mặt trên webcam hoặc sample dataset.
- Tạo repository skeleton tối thiểu.

### Demo

1. Trình bày ba slide bắt buộc.
2. Mở literature table.
3. Chạy face crop trên webcam hoặc hiển thị một batch dataset.
4. Chốt câu hỏi nghiên cứu và ma trận E0 đến E4.

### Bằng chứng phải nộp

- Slide PDF hoặc PPT.
- Literature matrix.
- Link ba paper cốt lõi.
- Quyết định dataset hoặc deadline chuyển phương án.
- Screenshot demo.

### Tiêu chí đạt

- [x] Câu hỏi nghiên cứu chỉ có một biến chính là learned depth head.
- [x] Nhóm giải thích được tại sao UCDCN gần về kỹ thuật còn CASO-PAD mới nhất về thời gian.
- [x] Không trộn số liệu khác protocol.
- [ ] Dataset chính thức có nguồn và license rõ: yêu cầu truy cập vẫn đang chờ duyệt; CASIA giữa kỳ được ghi riêng.

### Nếu bị chặn

Nếu chưa được cấp OULU-NPU, đặt hạn chốt. Quá hạn chuyển sang Replay-Attack, không để toàn dự án dừng vì chờ dữ liệu.

---

## 5. Lượt 2 Dữ liệu, metric và binary baseline

**Người báo cáo:** B  
**Phiên bản:** R1 Measurable baseline

### Mục tiêu

Có pipeline dữ liệu đúng và baseline MobileNetV3 E0 tạo được raw score cùng các metric video-level.

### Công việc của A

- Tạo manifest theo official protocol.
- Viết leakage validator.
- Viết APCER, BPCER, ACER, EER và AUC.
- Unit test metric bằng một ví dụ tính tay.
- Vẽ phân phối live, print và replay.

### Công việc của B

- Triển khai E0 MobileNetV3.
- Viết train loop, checkpoint và validation score export.
- Tạo training curve.
- Lưu config và seed.

### Demo

1. Chạy manifest validator.
2. Cố tình thêm một video trùng để validator báo lỗi.
3. Hiển thị batch sau preprocessing.
4. Mở training curve và bảng metric E0.
5. Hiển thị ROC hoặc score distribution.

### Câu hỏi học thuật phải trả lời

- Vì sao accuracy không đủ cho PAD?
- APCER và BPCER đại diện cho hai loại rủi ro nào?
- Threshold lấy ở đâu?
- E0 có thể đang học shortcut nào?

### Tiêu chí đạt

- [x] Không có video leakage trên manifest CASIA giữa kỳ.
- [x] Metric test pass.
- [x] Raw validation score được lưu trong run artifact trên Drive.
- [x] E0 có run ID, config và checkpoint.
- [x] Test chỉ được mở sau khi khóa cấu hình và threshold; kết quả E0 đã đóng băng.

### Nếu bị chặn

Nếu E0 chưa hội tụ, vẫn báo cáo evaluator, dữ liệu và nguyên nhân cụ thể. Không thay bằng accuracy tính trên train set.

---

## 6. Lượt 3 Pseudo depth và tái lập CDCN

**Người báo cáo:** A  
**Phiên bản:** R2 Depth baseline  
**Mốc:** Phù hợp làm báo cáo giữa kỳ nếu lịch môn học rơi vào giai đoạn này

### Mục tiêu

Sinh pseudo depth đúng và có CDCN E1 chạy được. Đây là mốc nhóm thực sự đi vào trọng tâm đề tài.

### Công việc của A

- Tích hợp 3DDFA V2 offline.
- Sinh depth map, mask và failure report.
- Kiểm tra RGB với depth thẳng hàng.
- Tạo figure RGB, target depth và histogram.

### Công việc của B

- Triển khai hoặc tái lập CDCN.
- Triển khai absolute và contrastive depth loss.
- Train E1 depth only.
- Chuyển predicted depth thành mean-depth score.

### Demo

1. Chạy sinh depth cho một frame live.
2. So sánh live pseudo depth và spoof zero map.
3. Hiển thị predicted depth đầu tiên của E1.
4. Báo cáo validation APCER, BPCER, ACER, EER và AUC.
5. So sánh E0 và E1, chưa kết luận quá sớm nếu mới một seed.

### Câu hỏi học thuật phải trả lời

- Tại sao gọi là pseudo depth?
- Vì sao zero map chỉ hợp lý với print và replay phẳng?
- Contrastive depth loss đo gì?
- Nếu E1 kém E0, có thể do data, depth label hay optimization?

### Tiêu chí đạt

- [x] Không có NaN hoặc map live rỗng trong QA cuối.
- [x] Failure rate của 3DDFA được báo cáo: 0 persistent failure trên 3.000 frame bona fide.
- [x] Official-CDCN E1 xuất raw score ở mức frame và video cho validation và locked test; E1-Lite Pilot được lưu riêng.
- [x] Có 12 predicted-depth case validation official-E1 gồm cả đúng và sai để xem.
- [ ] Slide giữa kỳ đã cập nhật bằng số thật.

Trạng thái chốt ngày 21 tháng 9 năm 2026: queue 3DDFA hoàn tất 3.000 frame bona
fide và 9.000 attack zero-map, không có persistent failure. Kiến trúc/loss official
CDCN đã được kiểm chứng số học với upstream, smoke/full 30 epoch đã chạy, best
checkpoint epoch 25 được chọn trên validation và locked test chỉ mở sau khi khóa
threshold. E1 official đạt test ACER 2,7778%; run compact cũ giữ nhãn E1-Lite Pilot.

### Nếu bị chặn

Nếu 3DDFA chưa chạy toàn bộ dữ liệu, hoàn thành một subset có kiểm tra chất lượng và train smoke test. Không dùng map toàn 1 làm kết quả cuối mà không ghi rõ fallback.

---

## 7. Lượt 4 Learned depth head

**Người báo cáo:** B  
**Phiên bản:** R3 First modification

### Mục tiêu

Kiểm tra thay đổi chính: learned depth head có tốt hơn mean-depth score không.

### Công việc của A

- Khóa manifest, preprocessing và metric.
- Chọn threshold E1 trên validation.
- Tạo bảng failure cases E1.
- Viết phần Related Work cho paper draft.

### Công việc của B

- Thêm depth head hai convolution nhẹ.
- Viết unit test shape và backward.
- Train E2: freeze CDCN, chỉ train head bằng BCE.
- Đo phần tham số và latency tăng thêm.

### Demo

1. Minh họa mean-depth scoring và learned head trên cùng map.
2. Hiển thị các case E2 sửa được lỗi của E1.
3. Hiển thị các case E2 làm tệ hơn.
4. So sánh E1 với E2 về ACER, APCER, BPCER, params và latency.

### Câu hỏi học thuật phải trả lời

- Improvement đến từ architecture hay chỉ từ threshold?
- Depth head có đủ nhỏ để gọi là lightweight không?
- Head đang học pattern depth hay shortcut?
- Kết quả một seed có đáng tin không?

### Tiêu chí đạt

- [ ] E1 và E2 chỉ khác scoring head và training head.
- [ ] Cùng validation threshold procedure.
- [ ] Có delta params và latency.
- [ ] Có error analysis cặp E1 và E2.

### Nếu bị chặn

Nếu E2 không tốt hơn, giữ nguyên kết quả và phân tích. Không lập tức thêm attention, transformer hoặc nhiều loss cùng lúc.

---

## 8. Lượt 5 Training strategy và Focal Loss

**Người báo cáo:** A  
**Phiên bản:** R4 Controlled ablation

### Mục tiêu

Tách tác dụng của end-to-end training, staged training, BCE và Focal Loss.

### Công việc của A

- Chuẩn bị experiment matrix E2, E3 và E4.
- Theo dõi class balance và hard samples.
- Tạo bảng ablation.
- Viết Experimental Setup cho paper draft.

### Công việc của B

- Train E3 end-to-end với BCE.
- Train E4 staged với Focal Loss.
- Giữ augmentation và data budget cố định.
- Xuất depth MAE và classification metrics.

### Demo

1. Trình bày staged training ba bước.
2. Hiển thị depth map của end-to-end và staged training.
3. Trình bày bảng E1 đến E4.
4. Phân tích APCER giảm nhưng BPCER tăng hoặc ngược lại nếu xảy ra.

### Câu hỏi học thuật phải trả lời

- Focal Loss có thực sự cần khi class balance không quá lệch?
- Staged training giúp depth quality hay classification?
- Lambda classification ảnh hưởng thế nào?
- Có đang thay quá một biến giữa E3 và E4 không?

### Thiết kế nếu cần tách biến rõ hơn

Nếu E3 và E4 khác cả training strategy và loss, chạy thêm một cấu hình trung gian:

- E3b staged training với BCE, hoặc
- E4b end-to-end với Focal Loss.

Chỉ cần một cấu hình trung gian để xác định nguồn thay đổi; không mở rộng thành grid search.

### Tiêu chí đạt

- [ ] Có ablation hợp lệ.
- [ ] Có kết luận riêng cho head, training strategy và loss.
- [ ] Không chọn cấu hình chỉ dựa vào accuracy.
- [ ] Paper draft có Method và Experimental Setup bản đầu.

---

## 9. Lượt 6 Nhiều seed và so sánh với paper

**Người báo cáo:** B  
**Phiên bản:** R5 Evidence strengthening

### Mục tiêu

Kiểm tra improvement có ổn định và đặt kết quả cạnh CDCN, UCDCN, CASO-PAD theo cách trung thực.

### Công việc của A

- Đọc đúng bảng kết quả của các paper.
- Lập bảng dataset, protocol, metric và threshold của từng paper.
- Đánh dấu direct hoặc contextual comparison.
- Viết phần Discussion về comparability.

### Công việc của B

- Chạy tối thiểu 3 seed cho E1 và cấu hình tốt nhất.
- Tính mean và standard deviation.
- Đo params, model size, latency p50 và p95.
- Sinh bảng kết quả tự động.

### Demo

1. Trình bày phân phối kết quả nhiều seed.
2. Cho biết improvement trung bình và độ dao động.
3. Mở bảng paper comparison.
4. Giải thích tại sao một số số liệu không thể so trực tiếp.
5. Trình bày trade-off ACER và latency.

### Câu hỏi học thuật phải trả lời

- Improvement có lớn hơn run-to-run variance không?
- Kết quả nào là reproduction gap so với paper?
- Khác input size, crop hoặc protocol làm thay đổi so sánh ra sao?
- Phương pháp của nhóm thắng ở accuracy, efficiency hay interpretability?

### Tiêu chí đạt

- [ ] E1 và model tốt nhất có ít nhất 3 seed nếu compute cho phép.
- [ ] Báo mean và standard deviation, không chỉ best run.
- [ ] Mọi số paper có nguồn và table reference.
- [ ] Không dùng từ `outperform` cho contextual comparison.

### Nếu bị chặn

Nếu compute không đủ ba seed hoàn chỉnh, báo số run thực tế và coi kết luận là sơ bộ. Ưu tiên thêm seed hơn thêm model mới.

---

## 10. Lượt 7 Error analysis và webcam integration

**Người báo cáo:** A  
**Phiên bản:** R6 Interpretable result

### Mục tiêu

Giải thích model tốt và kém ở đâu, sau đó đưa model tốt nhất vào một demo PAD tối giản.

### Công việc của A

- Nhóm false live và false spoof.
- Phân tích print, replay, ánh sáng và blur nếu metadata có.
- Tạo figure RGB, target depth, predicted depth và error map.
- Viết Results và Discussion.

### Công việc của B

- Tích hợp face detector và model tốt nhất vào webcam.
- Thêm median score window.
- Đo FPS và time to decision.
- Nếu còn thời gian, ghép ArcFace pretrained.

### Demo

1. Live face.
2. Print attack.
3. Replay attack.
4. Một failure case nếu có thể tái hiện.
5. ArcFace chỉ công bố identity khi PAD live, nếu phần này đã hoàn tất.

### Câu hỏi học thuật phải trả lời

- Webcam có cùng domain với benchmark không?
- Vì sao demo không thay cho test protocol?
- Zero-depth assumption thất bại ở trường hợp nào?
- Model có dựa vào nền hoặc viền thiết bị không?

### Tiêu chí đạt

- [ ] Có error analysis định lượng hoặc ít nhất có hệ thống.
- [ ] Demo không được dùng làm số benchmark.
- [ ] Có FPS và time to decision.
- [ ] Có video dự phòng.
- [ ] Paper draft có Results và Discussion.

---

## 11. Lượt 8 Tổng kết và paper style presentation

**Người báo cáo:** B  
**Phiên bản:** R7 Final study

### Mục tiêu

Trình bày dự án như một nghiên cứu nhỏ: vấn đề, khoảng trống, phương pháp, thí nghiệm, kết quả, giới hạn và demo.

### Việc chung của cả hai

- Khóa code, config, checkpoint và threshold.
- Chạy test cuối.
- Sinh lại mọi figure và table từ artifact.
- Hoàn thiện paper draft.
- Kiểm tra claim với bằng chứng.
- Tập báo cáo và Q&A.

### Cấu trúc trình bày cuối

1. Problem và threat model.
2. Modern methods và literature gap.
3. CDCN baseline.
4. CDCN MT Lite.
5. Dataset, protocol và metrics.
6. Main results.
7. Ablation.
8. Efficiency.
9. Error analysis.
10. Webcam demo.
11. Limitations và hướng tiếp theo.

### Tiêu chí đạt

- [ ] Mọi con số truy ngược được về run ID.
- [ ] Có bảng nội bộ và bảng paper comparison riêng.
- [ ] Có mean và standard deviation khi đủ run.
- [ ] Có cả failure case.
- [ ] Không tuyên bố xử lý mask 3D hoặc mọi attack.
- [ ] Cả hai thành viên đều trả lời được câu hỏi về data, model và metric.
- [ ] Paper draft hoặc technical report hoàn chỉnh.

---

## 12. Nhịp làm việc giữa hai lượt

Giả sử hai lượt cách nhau một tuần:

| Ngày | Công việc |
|---|---|
| 0 | Ghi phản hồi của giảng viên, chốt một câu hỏi cần trả lời ở lượt sau |
| 1 | Tạo issue, chốt owner và reviewer |
| 2 đến 3 | Code, chuẩn bị dữ liệu hoặc train smoke test |
| 4 | Review chéo và ghép artifact |
| 5 | Chạy experiment chính |
| 6 | Phân tích số liệu, cập nhật paper và slide |
| 7 | Rehearsal, quay video dự phòng, không thêm feature mới |

### Daily update ba dòng

Mỗi người cập nhật:

```text
Đã hoàn thành:
Đang bị chặn:
Việc tiếp theo:
```

Không cần họp dài nếu ba dòng đủ rõ. Chỉ họp khi có quyết định về protocol, architecture hoặc kết luận thí nghiệm.

---

## 13. Phân công dài hạn cho hai thành viên

| Hạng mục | A chịu trách nhiệm chính | B chịu trách nhiệm chính | Review chéo |
|---|---:|---:|---|
| Literature và citation | Có | Hỗ trợ | B kiểm claim |
| Dataset và protocol | Có | Hỗ trợ | B kiểm manifest |
| Metric và paper table | Có | Hỗ trợ | B test công thức |
| Pseudo depth | Có | Hỗ trợ | B kiểm shape và loss |
| Model implementation | Hỗ trợ | Có | A kiểm experiment isolation |
| Training và checkpoint | Hỗ trợ | Có | A kiểm config và seed |
| Runtime demo | Hỗ trợ | Có | A kiểm kịch bản |
| Paper writing | Introduction, Related Work, Evaluation | Method, Implementation, Results | Cả hai sửa Discussion |

Phân công này không được dùng để từ chối tìm hiểu phần còn lại. Người báo cáo tuần đó phải đọc toàn bộ artifact liên quan.

---

## 14. Definition of report ready

Một lượt chỉ được coi là sẵn sàng khi:

- [ ] Người báo cáo tuần này đúng lịch luân phiên.
- [ ] Cả hai đều có mặt.
- [ ] Slide có ngày, phiên bản và run ID.
- [ ] Có ít nhất một figure, table hoặc demo mới.
- [ ] Số liệu lấy từ artifact.
- [ ] Có một kết luận tạm thời và một limitation.
- [ ] Có video hoặc screenshot dự phòng.
- [ ] Đã rehearsal ít nhất một lần.
- [ ] Có câu trả lời rõ cho việc tuần này đóng góp gì vào paper.

---

## 15. Mẫu slide tiến độ dùng lại mỗi lượt

Sau ba slide bắt buộc, thêm các slide sau:

1. **Research question:** giữ nguyên để không trôi phạm vi.
2. **Previous feedback:** thầy góp ý gì và nhóm xử lý ra sao.
3. **Change this week:** chỉ một hoặc hai thay đổi chính.
4. **Experiment setup:** config, dataset, protocol và seed.
5. **Result:** figure hoặc table.
6. **Interpretation:** dữ liệu ủng hộ điều gì và chưa ủng hộ điều gì.
7. **Next experiment:** biến nào sẽ được thay ở lượt tiếp theo.

Không dùng một biểu đồ mà thiếu trục, đơn vị, số mẫu hoặc định nghĩa metric.

---

## 16. Mẫu bảng theo dõi experiment

| Run ID | Giả thuyết | Thay đổi duy nhất | Seed | Trạng thái | Artifact | Kết luận |
|---|---|---|---:|---|---|---|
| E0 S42 | Binary baseline chạy được | MobileNetV3 BCE | 42 | | | |
| E1 S42 | Depth supervision tốt hơn E0 | CDCN depth only | 42 | | | |
| E2 S42 | Learned head tốt hơn mean depth | Frozen head BCE | 42 | | | |
| E3 S42 | Joint training tốt hơn frozen | End-to-end BCE | 42 | | | |
| E4 S42 | Staged Focal cải thiện hard cases | Staged Focal | 42 | | | |

Mỗi run phải trả lời một giả thuyết. Không train chỉ vì có model mới muốn thử.

---

## 17. Mẫu ghi phản hồi của giảng viên

```markdown
## Lượt báo cáo N

Người báo cáo:

Đã trình bày:

Giảng viên yêu cầu:

Nhóm đồng ý thay đổi:

Nhóm giữ nguyên vì:

Experiment cần chạy trước lượt sau:

Người chịu trách nhiệm:
```

Phân biệt yêu cầu bắt buộc với gợi ý mở rộng. Gợi ý mở rộng không được chen vào critical path nếu baseline và ablation chưa hoàn tất.

---

## 18. Cảnh báo trễ tiến độ

| Dấu hiệu | Hành động ngay |
|---|---|
| Hết lượt 1 chưa chốt dataset | Chuyển sang phương án thay thế |
| Hết lượt 2 chưa có metric đúng | Dừng model mới, sửa evaluator |
| Hết lượt 3 chưa có CDCN score | Giảm dữ liệu debug, hoàn thành E1 trước |
| Hết lượt 4 chưa có E2 | Bỏ UI và recognition, tập trung depth head |
| Hết lượt 5 chưa có ablation | Không thêm augmentation hoặc model mới |
| Hết lượt 6 chưa có nhiều seed | Dừng mọi phần mở rộng |
| Hết lượt 7 chưa có paper table | Chia một người viết, một người khóa artifact |

### Những thứ được cắt trước

1. Cross-dataset.
2. ONNX.
3. ArcFace demo.
4. MobileNetV3 E0 nếu CDCN đã tái lập tốt.
5. Focal Loss nếu không còn thời gian tách biến.

### Những thứ không được cắt

- Official protocol.
- Validation threshold.
- CDCN baseline.
- Learned depth head.
- Ít nhất một ablation hợp lệ.
- APCER, BPCER và ACER.
- Paper comparison có chú thích.
- Luân phiên báo cáo.

---

## 19. Definition of done cuối dự án

- [ ] A và B đã luân phiên báo cáo đúng lịch và đều tham dự.
- [ ] Ba slide bắt buộc được cập nhật xuyên suốt.
- [ ] Dataset và protocol được ghi rõ.
- [ ] E1 CDCN baseline tái lập được.
- [ ] CDCN MT Lite được triển khai và kiểm thử.
- [ ] Có ablation learned head và training strategy.
- [ ] Baseline cùng model tốt nhất có nhiều seed nếu tài nguyên cho phép.
- [ ] Có APCER, BPCER, ACER, EER và AUC ở mức video.
- [ ] Có params và latency.
- [ ] Có error analysis.
- [ ] Có bảng so sánh CDCN, UCDCN, CASO-PAD và kết quả nhóm.
- [ ] Có demo PAD; ArcFace là phần cộng thêm.
- [ ] Có technical report hoặc paper draft.
- [ ] Claim cuối không vượt quá protocol và attack đã thử.

