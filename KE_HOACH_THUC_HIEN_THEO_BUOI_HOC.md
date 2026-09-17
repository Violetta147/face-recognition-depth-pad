# Kế hoạch hoàn thành đề tài theo từng buổi học

**Đề tài:** Real time Face Recognition System with Presentation Attack Detection using Depth Map Estimation  
**Mục tiêu kế hoạch:** Mỗi buổi học đều có một kết quả mới, chạy được và có thể demo cho giảng viên  
**Quy mô mặc định:** Nhóm 4 thành viên, 10 buổi học  
**Tài liệu đặc tả liên quan:** [DAC_TA_HE_THONG_NHAN_DIEN_KHUON_MAT_PAD_DEPTH_MAP.md](DAC_TA_HE_THONG_NHAN_DIEN_KHUON_MAT_PAD_DEPTH_MAP.md)

---

## 1. Cách sử dụng kế hoạch

Kế hoạch được tổ chức theo nguyên tắc mỗi buổi phải kết thúc bằng một phiên bản chạy được. Nhóm không chờ đến cuối kỳ mới ghép các mô đun.

Mỗi buổi có năm loại đầu ra:

1. **Demo trực tiếp:** chức năng mới có thể quan sát được.
2. **Artifact:** source code, cấu hình, biểu đồ, bảng kết quả hoặc checkpoint.
3. **Bằng chứng:** ảnh chụp, video ngắn, log hoặc metric chứng minh kết quả.
4. **Kết luận học thuật:** nhóm giải thích được điều đã học và vấn đề còn tồn tại.
5. **Điểm bắt đầu cho buổi sau:** công việc tiếp theo không bị mơ hồ.

### Quy tắc quan trọng

- Mỗi buổi chỉ hứa demo phần đã đạt tiêu chí nghiệm thu.
- Luôn chuẩn bị video dự phòng dài tối đa 2 phút của đúng phiên bản code đã chạy được.
- Không dùng test set để điều chỉnh mô hình trong các buổi giữa kỳ.
- Không làm giao diện đẹp trước khi dữ liệu, metric và pipeline cơ bản đúng.
- Mỗi thành viên phải biết giải thích phần mình làm bằng sơ đồ hoặc ví dụ cụ thể.
- Cuối mỗi buổi, nhóm ghi lại phản hồi của giảng viên và cập nhật backlog trong vòng 24 giờ.

---

## 2. Toàn cảnh mười buổi

| Buổi | Phiên bản đạt được | Nội dung demo chính | Mốc dự án |
|---:|---|---|---|
| 1 | V0.1 | Webcam và phát hiện khuôn mặt thời gian thực | Khởi động kỹ thuật |
| 2 | V0.2 | Đăng ký và nhận diện thành viên bằng ArcFace | Hoàn thành recognition độc lập |
| 3 | V0.3 | Dataset manifest, split và kiểm tra data leakage | Dữ liệu sẵn sàng |
| 4 | V0.4 | Binary PAD baseline phân biệt live và spoof | PAD baseline chạy được |
| 5 | V0.5 | Sinh và trực quan hóa pseudo depth map | Depth supervision sẵn sàng |
| 6 | V0.6 | DepthNet dự đoán depth map | Mô hình depth baseline |
| 7 | V0.7 | CDCN và bảng so sánh ba mô hình | Mô hình chính hoàn thành |
| 8 | V0.8 | Temporal PAD ổn định trên webcam | PAD real time hoàn thành |
| 9 | V0.9 | Pipeline PAD trước Recognition | End to end MVP |
| 10 | V1.0 | Kết quả cuối, error analysis và demo hoàn chỉnh | Nghiệm thu đề tài |

### Critical path

```text
Webcam và detector
    -> ArcFace recognition
    -> Dataset và evaluator
    -> Binary PAD
    -> Pseudo depth
    -> DepthNet
    -> CDCN
    -> Temporal aggregation
    -> End to end pipeline
    -> Đánh giá và báo cáo
```

Nếu một mắt xích trên critical path chưa đạt, nhóm ưu tiên sửa nó trước khi thêm chức năng mới.

---

## 3. Phân công vai trò

Ký hiệu bốn vai trò:

| Vai trò | Phụ trách chính | Trách nhiệm xuyên suốt |
|---|---|---|
| A Dữ liệu | Dataset, manifest, pseudo depth, QA dữ liệu | Đảm bảo không leakage và đúng protocol |
| B Mô hình PAD | Binary model, DepthNet, CDCN, loss | Đảm bảo train và inference tái lập được |
| C Nhận diện | Detector, alignment, ArcFace, gallery | Đảm bảo recognition và unknown threshold |
| D Tích hợp | Controller, temporal, UI, logging, latency | Đảm bảo demo end to end ổn định |

### Quy tắc phối hợp

- Mỗi đầu việc có một người chịu trách nhiệm chính và một người review.
- Người chịu trách nhiệm chính không tự duyệt kết quả của mình.
- Mỗi ngày làm việc, thành viên cập nhật ba dòng: đã làm, đang vướng, sẽ làm.
- Các interface giữa mô đun được chốt bằng dữ liệu đầu vào và đầu ra, không truyền miệng.
- Tất cả thành viên dùng chung quy ước `live = 1`, `spoof = 0`, score cao hơn là live.

---

## 4. Buổi 1 Khởi động dự án và phát hiện khuôn mặt

### Mục tiêu

Tạo phiên bản đầu tiên đọc webcam, phát hiện khuôn mặt, vẽ bounding box và landmark theo thời gian thực. Đây là bằng chứng rằng môi trường và camera hoạt động trước khi nhóm làm model phức tạp.

### Công việc phải hoàn thành trước buổi học

**C phụ trách chính**

- Tạo môi trường Python và cài dependency tối thiểu.
- Tích hợp SCRFD hoặc RetinaFace pretrained.
- Viết module mở webcam và module detector tách biệt.
- Trả về bounding box, confidence và 5 landmarks.

**D hỗ trợ**

- Tạo cửa sổ OpenCV.
- Hiển thị FPS, số khuôn mặt và confidence.
- Xử lý phím `q` để thoát an toàn.

**A phụ trách tài liệu dữ liệu**

- Tìm hiểu điều kiện truy cập OULU NPU và Replay Attack.
- Lập bảng so sánh dung lượng, protocol, loại attack và giấy phép.

**B phụ trách nghiên cứu**

- Đọc phần tổng quan PAD, binary supervision và depth supervision.
- Chuẩn bị một slide giải thích vì sao detector không phải PAD.

### Demo cho giảng viên

1. Mở ứng dụng webcam.
2. Một thành viên đi vào và ra khỏi khung hình.
3. Quay mặt nhẹ sang trái và phải để kiểm tra box.
4. Đưa hai người vào khung hình để hiển thị số mặt.
5. Chỉ ra FPS và confidence.

### Nội dung cần giải thích

- Face detection chỉ tìm vị trí khuôn mặt, chưa biết thật hay giả.
- Landmark sẽ được dùng để căn chỉnh ảnh cho recognition.
- PAD crop và recognition crop sau này sẽ khác nhau.

### Artifact phải có

- `src/.../face/detector.py`.
- Script chạy webcam.
- File cấu hình camera và detector.
- Ảnh chụp màn hình một mặt và nhiều mặt.
- Bảng lựa chọn dataset sơ bộ.

### Tiêu chí đạt

- [ ] Chạy liên tục 5 phút không crash.
- [ ] Phát hiện được khuôn mặt của tất cả thành viên trong điều kiện phòng học.
- [ ] FPS và confidence được hiển thị.
- [ ] Không hard code đường dẫn máy cá nhân trong source.
- [ ] Nhóm đã chốt dataset chính hoặc phương án A và B.

### Phương án dự phòng

Nếu webcam hoặc model lỗi trên máy trình bày, dùng một video ngắn trong repo fixtures và chạy cùng detector. Không chuyển sang dùng ảnh chụp tĩnh duy nhất vì không thể hiện được pipeline thời gian thực.

---

## 5. Buổi 2 Nhận diện khuôn mặt bằng ArcFace

### Mục tiêu

Hoàn thiện recognition độc lập trước khi thêm PAD: đăng ký thành viên, sinh embedding, so khớp cosine và trả về `UNKNOWN` cho người chưa đăng ký.

### Công việc phải hoàn thành trước buổi học

**C phụ trách chính**

- Căn chỉnh khuôn mặt bằng 5 landmarks về 112 x 112.
- Tích hợp ArcFace pretrained.
- Xây gallery lưu template embedding cục bộ.
- Viết enrollment lấy nhiều frame và loại frame chất lượng kém.
- Viết cosine matching và unknown threshold.

**D hỗ trợ**

- Thêm state `NO_FACE`, `RECOGNIZED`, `UNKNOWN` lên UI.
- Thêm log similarity và latency recognition.

**A hỗ trợ đánh giá**

- Thu hai phiên khuôn mặt tách biệt của từng thành viên.
- Phiên 1 dùng enrollment, phiên 2 dùng validation nhỏ.
- Không đưa ảnh recognition demo vào Git nếu chưa được phép.

**B review**

- Kiểm tra L2 normalization và cosine similarity.
- Viết test cùng embedding phải có similarity gần 1.

### Demo cho giảng viên

1. Đăng ký một thành viên bằng 15 đến 30 frame.
2. Người đó rời camera rồi quay lại để được nhận diện.
3. Một thành viên chưa đăng ký xuất hiện và nhận kết quả `UNKNOWN`.
4. Hiển thị similarity thay đổi theo pose hoặc khoảng cách.

### Nội dung cần giải thích

- ArcFace tạo embedding chứ không trực tiếp tạo tên người.
- Similarity threshold quyết định known hoặc unknown.
- Enrollment và evaluation phải khác phiên.
- Phiên bản này vẫn nhận diện được ảnh in; đó chính là lý do cần PAD.

### Artifact phải có

- Module aligner, recognizer và gallery.
- Script enrollment.
- Biểu đồ nhỏ hoặc bảng genuine và impostor similarity.
- Threshold tạm thời kèm cách chọn.

### Tiêu chí đạt

- [ ] Nhận diện đúng ít nhất các thành viên đã đăng ký trong demo phòng học.
- [ ] Người chưa đăng ký được trả `UNKNOWN` trong phần lớn thử nghiệm.
- [ ] Gallery lưu model version và thời gian enrollment.
- [ ] Không lưu raw frame theo mặc định.
- [ ] Nhóm trình diễn được việc ảnh in có thể đánh lừa recognition thuần túy.

### Phương án dự phòng

Nếu webcam recognition chưa ổn định, demo trên hai video khác phiên: một người trong gallery và một người ngoài gallery. Vẫn phải hiển thị raw similarity, không chỉ nhãn cuối.

---

## 6. Buổi 3 Dataset, protocol và chống data leakage

### Mục tiêu

Chứng minh nhóm chuẩn bị dữ liệu đúng phương pháp nghiên cứu. Buổi này không cần model mới nhưng phải có pipeline dữ liệu chạy được và một demo trực quan về lỗi leakage.

### Công việc phải hoàn thành trước buổi học

**A phụ trách chính**

- Hoàn tất truy cập dataset chính.
- Đọc protocol chính thức.
- Viết script trích frame theo video.
- Tạo `train.csv`, `val.csv`, `test.csv`.
- Viết validator phát hiện trùng subject, video và sample.
- Thống kê số subject, video, frame, live, print và replay theo split.

**B hỗ trợ**

- Viết PyTorch Dataset và DataLoader.
- Hiển thị một batch sau preprocessing.

**C review**

- Kiểm tra crop face được tạo nhất quán.
- Kiểm tra BGR và RGB.

**D hỗ trợ demo**

- Sinh một báo cáo HTML, Markdown hoặc ảnh tổng hợp dataset.

### Demo cho giảng viên

1. Chạy validator trên manifest đúng và cho kết quả pass.
2. Cố tình đưa một video vào cả train và test, chạy lại để validator báo lỗi.
3. Hiển thị một batch live, print và replay có nhãn.
4. Trình bày biểu đồ phân phối dữ liệu.

### Nội dung cần giải thích

- Chia ngẫu nhiên theo frame gây kết quả ảo vì các frame cùng video gần giống nhau.
- Protocol và threshold phải tách biệt.
- Frame accuracy không nên là kết quả chính của video dataset.

### Artifact phải có

- Ba manifest.
- Script trích frame.
- Script validate manifest.
- Biểu đồ phân phối dữ liệu.
- README chỉ dẫn đặt dataset ngoài Git.

### Tiêu chí đạt

- [ ] Không có subject hoặc video leakage.
- [ ] Tất cả đường dẫn trong manifest hợp lệ.
- [ ] Label convention thống nhất.
- [ ] Có ít nhất một test tự động cho leakage.
- [ ] Nhóm biết chính xác đơn vị đánh giá là frame hay video.

### Phương án dự phòng

Nếu chưa được cấp dataset chính, dùng một tập fixture nhỏ được phép để hoàn thiện toàn bộ pipeline và manifest. Không tự đổi sang một bộ dữ liệu không rõ nguồn chỉ để có nhiều ảnh.

---

## 7. Buổi 4 Binary PAD baseline

### Mục tiêu

Train và đánh giá mô hình PAD đơn giản phân loại live hoặc spoof. Đây là baseline để kiểm tra toàn bộ đường đi từ dữ liệu đến metric.

### Công việc phải hoàn thành trước buổi học

**B phụ trách chính**

- Xây ResNet18 hoặc MobileNetV3 binary classifier.
- Dùng `BCEWithLogitsLoss`.
- Viết train, validation, checkpoint và resume.
- Lưu raw score thay vì chỉ lưu nhãn.

**A hỗ trợ**

- Xây sampler cân bằng theo video hoặc lớp.
- Kiểm tra augmentation không tạo shortcut.

**D phụ trách evaluator**

- Cài đặt APCER, BPCER, ACER, EER và ROC AUC.
- Aggregate frame score thành video score.
- Viết unit test metric bằng ví dụ tính tay.

**C hỗ trợ demo webcam**

- Kết nối binary PAD vào webcam ở chế độ thử nghiệm.
- Chưa kết luận đây là pipeline cuối.

### Demo cho giảng viên

1. Mở training curve và validation metric.
2. Chạy evaluator trên validation.
3. Hiển thị ROC curve và confusion cases.
4. Thử live, ảnh in và replay trên webcam.
5. Chỉ ra một trường hợp đúng và một trường hợp sai.

### Nội dung cần giải thích

- Binary baseline có thể học texture, viền màn hình hoặc background.
- Accuracy không đủ; APCER cho biết attack lọt qua, BPCER cho biết người thật bị chặn.
- Threshold được chọn trên validation.

### Artifact phải có

- Config E1.
- Checkpoint binary baseline.
- Training curve.
- `val_scores.csv` và `thresholds.json`.
- Bảng metric validation.
- Thư mục failure cases.

### Tiêu chí đạt

- [ ] Training loss giảm và không có NaN.
- [ ] Evaluator chạy ở mức video.
- [ ] Metric unit test pass.
- [ ] Raw score được lưu.
- [ ] Có thể chạy inference trên webcam hoặc video.

### Phương án dự phòng

Nếu model chưa hội tụ, demo constant baseline, dữ liệu một batch, training curve hiện tại và evaluator hoàn chỉnh. Nhóm phải xác định nguyên nhân cụ thể như nhãn đảo, learning rate, normalization hoặc class imbalance.

---

## 8. Buổi 5 Sinh pseudo depth map

### Mục tiêu

Tạo được depth supervision: depth map tương đối cho mẫu live và zero map cho print hoặc replay. Buổi này tập trung vào dữ liệu hình học, chưa cần CDCN.

### Công việc phải hoàn thành trước buổi học

**A phụ trách chính**

- Tích hợp 3DDFA V2 hoặc công cụ 3D face reconstruction đã chọn.
- Sinh depth map và face mask cho live.
- Sinh zero map cho spoof.
- Chuẩn hóa depth trong vùng mặt.
- Cache kết quả và cập nhật manifest.
- Báo cáo tỷ lệ sinh depth thất bại.

**B hỗ trợ**

- Kiểm tra output shape 32 x 32.
- Kiểm tra map live không rỗng, map spoof gần 0.

**C review alignment**

- Kiểm tra RGB crop và depth map thẳng hàng.

**D phụ trách visualization**

- Tạo grid gồm RGB, mask, depth map và histogram.

### Demo cho giảng viên

1. Chọn một frame live và chạy quy trình sinh depth.
2. Xoay visualization 3D hoặc depth tương đối nếu công cụ hỗ trợ.
3. So sánh depth target live với zero map của print và replay.
4. Hiển thị các trường hợp 3DDFA thất bại.
5. Giải thích vì sao đây là pseudo depth chứ không phải depth cảm biến.

### Nội dung cần giải thích

- Khuôn mặt thật có cấu trúc lồi lõm tương đối.
- Ảnh in và màn hình được đơn giản hóa thành mặt phẳng.
- Pseudo depth là tín hiệu giám sát, không phải bằng chứng tuyệt đối.
- Giả định zero map không phù hợp để tuyên bố chống mask 3D.

### Artifact phải có

- Script sinh depth map.
- Depth cache và metadata generator version.
- QA report.
- Ít nhất 100 cặp RGB và depth đã được xem hoặc toàn bộ nếu dữ liệu nhỏ.
- Danh sách sample thất bại.

### Tiêu chí đạt

- [ ] RGB, mask và depth thẳng hàng.
- [ ] Không có NaN hoặc Inf.
- [ ] Map live có phân phối hợp lý.
- [ ] Map spoof đúng bằng hoặc gần 0 theo quy ước.
- [ ] Failure rate được báo cáo, không âm thầm bỏ sample.

### Phương án dự phòng

Nếu 3DDFA V2 chưa build được trên Windows, demo pipeline trên một subset đã sinh ở môi trường khác hoặc dùng ONNX nếu có. Không thay live depth bằng map toàn 1 như kết quả cuối mà không ghi rõ đó chỉ là fallback để kiểm tra code.

---

## 9. Buổi 6 DepthNet baseline

### Mục tiêu

Train mô hình convolution thông thường để dự đoán depth map. So sánh depth supervision với binary classification.

### Công việc phải hoàn thành trước buổi học

**B phụ trách chính**

- Triển khai DepthNet với output 1 x 32 x 32.
- Triển khai absolute depth loss và contrastive depth loss.
- Viết unit test forward, loss và backward.
- Train E2 với cùng split và budget hợp lý như E1.

**A hỗ trợ**

- Xác nhận transforms hình học áp dụng đồng bộ cho RGB và depth.
- Kiểm tra batch visualization sau augmentation.

**D phụ trách đánh giá**

- Chuyển predicted depth thành liveness score.
- Calibrate threshold trên validation.
- Sinh predicted map và error map.

**C tích hợp thử nghiệm**

- Thay binary model bằng DepthNet trong webcam thông qua cùng interface.

### Demo cho giảng viên

1. Hiển thị input, target depth, predicted depth và absolute error.
2. So sánh live và spoof prediction.
3. Trình bày bảng E1 với E2.
4. Chạy một live và một replay trên webcam bằng DepthNet.
5. Chỉ ra trường hợp prediction đẹp nhưng quyết định vẫn sai nếu có.

### Nội dung cần giải thích

- DepthNet học pixel wise supervision thay vì chỉ một nhãn toàn ảnh.
- Absolute loss học giá trị, contrastive loss học cấu trúc gradient cục bộ.
- Depth energy cần được hiệu chỉnh thành liveness score.

### Artifact phải có

- Config E2.
- Checkpoint DepthNet.
- Unit test loss.
- Bảng E1 so với E2.
- Visualization dự đoán đúng và sai.

### Tiêu chí đạt

- [ ] Output shape và range đúng.
- [ ] Loss backward thành công.
- [ ] Checkpoint được chọn bằng validation.
- [ ] Score ở mức video và threshold được lưu.
- [ ] Có giải thích nếu E2 không tốt hơn E1.

### Phương án dự phòng

Nếu chưa train xong, demo checkpoint giữa chừng, loss curve và pipeline visualization trên validation. Không sử dụng test set để tìm checkpoint tốt hơn.

---

## 10. Buổi 7 CDCN và so sánh mô hình

### Mục tiêu

Hoàn thiện mô hình chính CDCN và so sánh công bằng với binary baseline và DepthNet.

### Công việc phải hoàn thành trước buổi học

**B phụ trách chính**

- Triển khai Central Difference Convolution.
- Xây CDCN hoặc chuyển đổi DepthNet để dùng CDC ở các block quy định.
- Kiểm tra `theta = 0` gần với convolution thông thường trong test phù hợp.
- Train E3 với cùng dữ liệu.
- Chạy ít nhất một ablation: bỏ contrastive loss hoặc đổi theta.

**D phụ trách evaluator**

- Tạo bảng E1, E2 và E3.
- Đo parameter count, latency và FPS nếu công cụ hỗ trợ đúng custom layer.

**A phụ trách error breakdown**

- Phân tích theo live, print, replay, device hoặc lighting.

**C tích hợp**

- Đưa CDCN vào webcam qua interface chung.

### Demo cho giảng viên

1. Minh họa vanilla convolution và central difference bằng sơ đồ nhỏ.
2. Hiển thị predicted depth của DepthNet và CDCN trên cùng sample.
3. Trình bày bảng APCER, BPCER, ACER, EER và AUC.
4. Trình bày latency để cho thấy trade off.
5. Chạy cùng một replay qua hai model nếu có thể.

### Nội dung cần giải thích

- CDC kết hợp thông tin intensity và gradient cục bộ.
- Không kết luận CDCN tốt hơn chỉ từ một seed hoặc một video demo.
- Nếu kết quả không như bài báo, phải xem protocol, preprocessing, depth target và training budget.

### Artifact phải có

- Config E3.
- Checkpoint CDCN.
- Ít nhất một ablation.
- Bảng so sánh ba model.
- Error breakdown.

### Tiêu chí đạt

- [ ] CDC layer có unit test.
- [ ] E1, E2 và E3 dùng cùng split.
- [ ] Threshold của từng model được chọn riêng trên validation.
- [ ] Có raw score và run ID.
- [ ] Có kết luận dựa trên số liệu, kể cả khi CDCN không thắng.

### Phương án dự phòng

Nếu training CDCN chưa ổn, demo unit test CDC, forward pass, depth prediction của checkpoint hiện tại và phân tích nguyên nhân. Không lấy checkpoint không rõ nguồn để thay kết quả nghiên cứu của nhóm.

---

## 11. Buổi 8 PAD nhiều frame và độ ổn định thời gian thực

### Mục tiêu

Giảm hiện tượng nhãn live và spoof nhấp nháy bằng cách tổng hợp score trên nhiều frame và thêm vùng quyết định uncertain.

### Công việc phải hoàn thành trước buổi học

**D phụ trách chính**

- Xây `TemporalAggregator`.
- Hỗ trợ single frame, mean window và median window.
- Thêm `tau_spoof`, `tau_live` và vùng xám.
- Reset buffer khi mất mặt hoặc track thay đổi.
- Thêm thời gian giữ state ngắn để UI ổn định.

**B hỗ trợ**

- Xuất score liên tục từ model PAD tốt nhất.
- Đánh giá E4 và E5 trên video validation.

**C hỗ trợ tracking**

- Dùng IoU hoặc landmark consistency để phát hiện đổi track trong MVP.

**A phụ trách test scenario**

- Chuẩn bị live, print và replay với thay đổi khoảng cách và ánh sáng.

### Demo cho giảng viên

1. Hiển thị biểu đồ score theo thời gian.
2. So sánh nhãn single frame với median window.
3. Che mặt hoặc đưa mặt ra ngoài để chứng minh buffer reset.
4. Chuyển từ live sang ảnh in và quan sát time to decision.
5. Minh họa state `UNCERTAIN` thay vì ép quyết định.

### Nội dung cần giải thích

- Nhiều frame giúp giảm nhiễu nhưng làm tăng thời gian quyết định.
- Median chống outlier tốt hơn mean trong một số trường hợp.
- Vùng xám giúp tránh false confidence.
- Aggregation score không thay thế một temporal neural network nhưng phù hợp phạm vi đồ án.

### Artifact phải có

- Module temporal.
- Unit test reset và window.
- Biểu đồ score theo thời gian.
- Bảng single frame, mean và median.
- Time to decision.

### Tiêu chí đạt

- [ ] Không trộn score giữa hai người hoặc hai lượt thử.
- [ ] Buffer reset khi mất mặt.
- [ ] UI bớt nhấp nháy rõ ràng.
- [ ] Có số liệu trade off giữa ổn định và độ trễ.
- [ ] Threshold và window nằm trong config.

### Phương án dự phòng

Nếu webcam khó tái hiện lỗi nhấp nháy, phát một video score đã lưu và mô phỏng ba phương pháp aggregation trên cùng chuỗi.

---

## 12. Buổi 9 Ghép pipeline PAD trước Recognition

### Mục tiêu

Tạo MVP end to end đúng logic an toàn: chỉ công bố danh tính sau khi PAD xác nhận live.

### Công việc phải hoàn thành trước buổi học

**D phụ trách chính**

- Hoàn thiện state machine.
- Ghép camera, detector, quality gate, PAD, temporal, ArcFace và gallery.
- Thêm structured event log.
- Đo latency từng stage.

**C phụ trách recognition integration**

- Chỉ gọi hoặc công bố matching khi state live.
- Cache embedding ngắn hạn cho cùng track.
- Kiểm tra unknown person.

**B phụ trách PAD integration**

- Đảm bảo model ở `eval` và `inference_mode`.
- Kiểm tra normalization online giống offline.

**A phụ trách end to end test**

- Thực hiện ma trận live, print, phone image, replay và unknown.
- Reset hệ thống giữa các lượt.

### Demo cho giảng viên

1. Người đã đăng ký: `COLLECTING -> LIVE -> RECOGNIZED`.
2. Người chưa đăng ký: `COLLECTING -> LIVE -> UNKNOWN`.
3. Ảnh in của người đã đăng ký: `COLLECTING -> SPOOF`, không có accept.
4. Video replay: bị chặn hoặc trình bày failure case trung thực.
5. Mặt quá xa hoặc mờ: `REPOSITION`.
6. Mở event log của một lượt để giải thích quyết định.

### Nội dung cần giải thích

- Recognition đúng danh tính không có nghĩa mẫu là live.
- PAD và recognition có threshold riêng.
- End to end attack success cần cả vượt PAD và match nạn nhân.
- State uncertain và reposition không được coi là accept.

### Artifact phải có

- Controller và state machine.
- Config demo hoàn chỉnh.
- Event log mẫu.
- Bảng latency p50 và p95.
- Kết quả ma trận end to end.

### Tiêu chí đạt

- [ ] Spoof, uncertain, no face và multiple faces không thể tạo accept.
- [ ] Online preprocessing khớp training.
- [ ] Demo chạy liên tục ít nhất 10 phút.
- [ ] Có chế độ CPU dự phòng.
- [ ] Không lưu frame hoặc embedding trong log mặc định.

### Phương án dự phòng

Nếu end to end webcam không ổn định, chạy pipeline trên các video chuẩn bị trước và mở event log theo thời gian. Không ghép các video từ nhiều phiên bản code khác nhau thành một demo giả.

---

## 13. Buổi 10 Đánh giá cuối và bảo vệ

### Mục tiêu

Khóa phiên bản V1.0, trình bày kết quả có bằng chứng, demo hoàn chỉnh và nêu giới hạn trung thực.

### Công việc phải hoàn thành trước buổi học

**Cả nhóm**

- Khóa config, checkpoint và threshold.
- Chạy test cuối sau khi không còn thay đổi lựa chọn.
- Chạy nhiều seed nếu thời gian cho phép.
- Tổng hợp bảng kết quả và biểu đồ từ raw score.
- Hoàn thành error analysis.
- Đo runtime trên máy demo.
- Kiểm tra README từ môi trường sạch.
- Quay video dự phòng.

**A**

- Trình bày dataset, protocol, leakage prevention và limitation.

**B**

- Trình bày E1, E2, E3, loss và ablation.

**C**

- Trình bày detector, alignment, ArcFace, gallery và unknown.

**D**

- Trình bày temporal aggregation, state machine, latency và demo.

### Demo cho giảng viên

1. Mở sơ đồ pipeline.
2. Demo live recognized.
3. Demo live unknown.
4. Demo print attack.
5. Demo replay attack.
6. Demo reposition hoặc uncertain.
7. Trình bày bảng so sánh mô hình.
8. Mở một failure case và giải thích.
9. Chốt giới hạn: RGB only, print và replay, không bảo đảm mask 3D.

### Artifact phải có

- Tag hoặc thư mục release V1.0.
- Báo cáo cuối.
- Slide.
- Bảng metric cuối.
- Biểu đồ và script sinh biểu đồ.
- Checkpoint và config tương ứng.
- README chạy demo.
- Video dự phòng.

### Tiêu chí đạt

- [ ] Mọi số trong slide truy ngược được về run ID.
- [ ] Threshold lấy từ validation.
- [ ] Test chỉ dùng cho kết quả cuối.
- [ ] Có kết quả PAD, recognition và end to end.
- [ ] Có latency và cấu hình máy.
- [ ] Có failure cases và giới hạn.
- [ ] Tất cả thành viên trả lời được luồng dữ liệu end to end.

---

## 14. Nếu chỉ có tám buổi

Ghép theo cách sau:

| Buổi 8 tuần | Nội dung ghép |
|---:|---|
| 1 | Webcam, detector và cấu trúc dự án |
| 2 | ArcFace enrollment và recognition |
| 3 | Dataset, manifest và binary baseline bắt đầu |
| 4 | Binary baseline hoàn chỉnh và pseudo depth demo |
| 5 | DepthNet |
| 6 | CDCN và so sánh mô hình |
| 7 | Temporal aggregation và end to end integration |
| 8 | Đánh giá cuối và bảo vệ |

Trong lịch tám buổi, nhóm phải chuẩn bị dataset ngay từ ngày đầu và không làm cross dataset hoặc ONNX trước khi MVP hoàn chỉnh.

---

## 15. Nếu có nhiều hơn mười buổi

Các buổi mở rộng theo thứ tự ưu tiên:

1. Cross dataset evaluation.
2. Ablation augmentation và crop context.
3. So sánh detector hoặc backbone recognition.
4. ONNX Runtime và benchmark CPU.
5. Explainability bằng feature map hoặc Grad CAM.
6. Temporal neural model nhẹ.

Mỗi buổi mở rộng vẫn phải trả lời một câu hỏi nghiên cứu, không chỉ thêm tính năng giao diện.

---

## 16. Nhịp làm việc giữa hai buổi học

Giả sử hai buổi cách nhau bảy ngày:

| Thời điểm | Hoạt động |
|---|---|
| Ngày 0 sau buổi học | Ghi phản hồi giảng viên, chốt mục tiêu buổi sau |
| Ngày 1 | Tạo issue và chia nhiệm vụ |
| Ngày 2 đến 3 | Làm mô đun độc lập, commit nhỏ |
| Ngày 4 | Ghép lần đầu, phát hiện interface mismatch |
| Ngày 5 | Train hoặc chạy thí nghiệm dài |
| Ngày 6 | Chốt demo, quay video dự phòng, cập nhật slide |
| Ngày 7 trước giờ học | Chỉ sửa lỗi nghiêm trọng, không thêm chức năng mới |

### Cuộc họp nhóm tối thiểu

- 15 phút sau buổi học để ghi phản hồi.
- 20 phút giữa tuần để kiểm tra blocker.
- 30 đến 45 phút trước buổi học một ngày để rehearsal.

---

## 17. Kịch bản demo chuẩn cho mọi buổi

Mỗi lần demo chỉ nên dài 3 đến 5 phút:

1. **15 giây:** Nhắc phiên bản trước làm được gì.
2. **30 giây:** Nêu chức năng hoặc câu hỏi mới của buổi này.
3. **2 phút:** Chạy demo trực tiếp.
4. **1 phút:** Cho xem metric, hình hoặc log.
5. **30 giây:** Nêu một vấn đề còn tồn tại và kế hoạch buổi sau.

Không dành phần lớn thời gian để đọc code. Chỉ mở những đoạn code chứng minh một quyết định quan trọng như loss, split validator hoặc state machine.

### Slide cập nhật mỗi buổi

Chỉ cần bốn slide:

1. Pipeline hiện tại, tô màu phần đã hoàn thành.
2. Điều mới trong tuần.
3. Demo hoặc kết quả.
4. Vấn đề và kế hoạch tiếp theo.

---

## 18. Definition of Demo Ready

Một chức năng chỉ được đem đi demo khi:

- [ ] Chạy lại được từ một lệnh được ghi trong README.
- [ ] Không phụ thuộc đường dẫn tuyệt đối trên máy một thành viên.
- [ ] Có config và checkpoint đúng phiên bản.
- [ ] Đã rehearsal ít nhất hai lần.
- [ ] Có video dự phòng.
- [ ] Có một người thao tác và một người thuyết trình.
- [ ] Nhóm biết cách khôi phục nếu camera hoặc CUDA lỗi.
- [ ] Có ít nhất một kết quả đúng và một giới hạn để giải thích.
- [ ] Không dùng dữ liệu test để tinh chỉnh ngay trước demo.

---

## 19. Backlog chuẩn

Mỗi issue nên có cấu trúc:

```markdown
## Mục tiêu
Kết quả quan sát được sau khi hoàn thành.

## Đầu vào
File, model, manifest hoặc interface cần có.

## Đầu ra
Source code, artifact và bằng chứng.

## Tiêu chí chấp nhận
- [ ] Điều kiện 1
- [ ] Điều kiện 2

## Cách kiểm thử
Lệnh chạy và kết quả kỳ vọng.

## Người phụ trách
Owner và reviewer.
```

### Nhãn issue đề nghị

- `data`
- `model-pad`
- `recognition`
- `pipeline`
- `evaluation`
- `bug`
- `demo-blocker`
- `documentation`
- `optional`

Ưu tiên `demo-blocker` trước mọi công việc giao diện hoặc mở rộng.

---

## 20. Bảng theo dõi tiến độ mỗi buổi

Sao chép bảng này cho từng tuần:

| Hạng mục | Owner | Trạng thái | Bằng chứng | Blocker | Hạn |
|---|---|---|---|---|---|
| Chức năng demo chính | | Chưa làm | | | |
| Unit test | | Chưa làm | | | |
| Integration | | Chưa làm | | | |
| Metric hoặc visualization | | Chưa làm | | | |
| README và lệnh chạy | | Chưa làm | | | |
| Video dự phòng | | Chưa làm | | | |
| Slide cập nhật | | Chưa làm | | | |

Trạng thái chỉ dùng: `Chưa làm`, `Đang làm`, `Đang review`, `Hoàn thành`, `Bị chặn`.

---

## 21. Nhật ký phản hồi giảng viên

Sau mỗi buổi, thêm một mục:

```markdown
### Buổi N Ngày tháng

**Đã demo:**

**Phản hồi của giảng viên:**

**Quyết định của nhóm:**

**Thay đổi phạm vi hoặc kỹ thuật:**

**Công việc bắt buộc trước buổi sau:**
```

Không thay đổi mục tiêu nghiên cứu chỉ vì một gợi ý nhỏ nếu thay đổi đó làm hỏng critical path. Những ý hay nhưng không bắt buộc đưa vào backlog `optional`.

---

## 22. Tiêu chí cảnh báo trễ tiến độ

Dự án đang trễ nếu có một trong các dấu hiệu:

- Đến buổi 3 chưa có manifest hợp lệ.
- Đến buổi 4 chưa có evaluator đúng.
- Đến buổi 5 chưa sinh được pseudo depth cho một subset.
- Đến buổi 7 chưa có ít nhất hai model so sánh được.
- Đến buổi 8 chưa có score PAD online.
- Đến buổi 9 chưa có state machine chặn recognition.

### Cách xử lý khi trễ

1. Dừng toàn bộ phần `optional`.
2. Giảm số augmentation và hyperparameter search.
3. Dùng một protocol chính thay vì nhiều protocol.
4. Chạy một seed để hoàn thiện pipeline, sau đó bổ sung seed nếu còn thời gian.
5. Dùng score aggregation thay vì huấn luyện temporal model.
6. Giữ giao diện OpenCV thay vì làm web app.
7. Không bỏ evaluator, data leakage check hoặc PAD gate.

---

## 23. Bảng nghiệm thu cuối dự án

| Nhóm kết quả | Bắt buộc | Trạng thái |
|---|---:|---|
| Webcam và face detection | Có | |
| ArcFace enrollment và unknown recognition | Có | |
| Dataset manifest không leakage | Có | |
| Binary PAD baseline | Có | |
| Pseudo depth map | Có | |
| DepthNet | Có | |
| CDCN | Có | |
| APCER, BPCER, ACER, EER và AUC | Có | |
| Temporal aggregation | Có | |
| PAD đứng trước Recognition | Có | |
| End to end demo | Có | |
| Latency và FPS | Có | |
| Error analysis | Có | |
| Cross dataset | Không | |
| ONNX | Không | |
| Temporal neural network | Không | |

Khi tất cả mục bắt buộc đã hoàn thành và có bằng chứng, nhóm mới dành thời gian cho phần mở rộng.

