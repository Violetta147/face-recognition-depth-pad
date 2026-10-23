# Lời thuyết trình Lượt 1–4

Nguyễn Hữu Minh Quân — Trịnh Minh Đạt

15 slide chính khoảng 13 phút; từ slide 16 là phụ lục. Khi báo cáo ngắn, lướt slide 3–4 và đi thẳng phần E1–E2. Đọc Notes trong PowerPoint để xem nguồn từng slide.

## Slide 1: Chống giả mạo khuôn mặt bằng depth supervision

Thời lượng gợi ý: 25 giây.

Chúng em báo cáo tiến độ bốn lượt đầu. Trọng tâm là Presentation Attack Detection, gọi tắt PAD: phân biệt người thật với ảnh in hoặc video replay trước camera. Câu hỏi chính là liệu một bộ phân loại nhỏ đọc bản đồ depth dự đoán có tốt hơn cách lấy trung bình map hay không. Phần trình bày đi qua dữ liệu, tái lập CDCN, sửa đổi có kiểm soát và kết quả E1–E2. Đây là kết quả phát triển trên CASIA với một seed, chưa phải nghiên cứu đã hoàn tất mọi thí nghiệm.

## Slide 2: Bài toán và câu hỏi nghiên cứu

Thời lượng gợi ý: 50 giây.

PAD trả lời ảnh trước camera là bona fide hay presentation attack. Nhận diện danh tính trả lời người đó là ai; phần này không phải trọng tâm hiện tại. Nhóm chỉ xét live, ảnh in và replay trong dữ liệu đã dùng. Chúng em đặt giả thuyết mean depth có thể bỏ qua pattern không gian và thử một learned head rất nhỏ. Đây là giả thuyết cần kiểm nghiệm, chưa phải hạn chế đã chứng minh của CDCN. Lượt 1 xác định câu hỏi, lượt 2 xây protocol và E0, lượt 3 tái lập Official CDCN E1, lượt 4 thực hiện E2 frozen head.

## Slide 3: Các hướng tiếp cận RGB Face PAD

Thời lượng gợi ý: 40 giây.

Có thể phân loại trực tiếp từ RGB bằng CNN; dùng giám sát cục bộ như pseudo-depth; thay toán tử và cách hợp nhất đặc trưng; hoặc dùng Transformer và học tổng quát qua domain. Các hướng này có thể kết hợp với nhau, không phải các lớp loại trừ nhau hay một bảng xếp hạng hiệu năng. Nhóm chọn depth-supervised CDCN để tạo một thí nghiệm nhỏ, kiểm soát được. Chúng em chưa triển khai tất cả các hướng và chưa so sánh SOTA. Nguồn: survey và công trình Domain Invariant Vision Transformer Learning trong WACV 2023.

## Slide 4: CDCN đối chứng và các công trình liên quan

Thời lượng gợi ý: 65 giây.

CDCN và CDCN++ cùng được giới thiệu trong paper CVPR 2020. E1 hiện là CDCN, không phải CDCN++. DC-CDN 2021 dùng hai hướng cross central difference và tương tác đặc trưng; UCDCN 2024 dùng kiến trúc lồng và có classifier đọc predicted depth cùng huấn luyện theo giai đoạn. Vì vậy ý tưởng learned depth head có tiền lệ. SCA-DS 2025 tiếp tục dùng attention và depth supervision; nhóm chỉ đối chiếu được abstract của công trình này. Các phương pháp mở rộng ở đây là tài liệu liên quan, chưa được nhóm tái lập. Không dùng số CASIA hiện tại để so trực tiếp với số paper ở protocol khác. Bước chọn baseline mạnh hơn cần được nghiên cứu tiếp.

## Slide 5: Dữ liệu và protocol đánh giá

Thời lượng gợi ý: 65 giây.

Nhóm dùng bản CASIA-FASD gồm 600 video và lấy đều 20 frame mỗi video, tổng 12.000 frame. Source có 20 subject train và 30 subject test. Nhóm tách bốn subject 4, 9, 14, 19 từ source train làm validation; còn 16 subject train. Số video và frame trên slide được suy ra từ parser đã kiểm tra 12 video mỗi subject và 20 frame mỗi video. Mọi frame của một video thuộc cùng split; subject không trùng giữa train, validation, test. Đây là CASIA development protocol của nhóm, không phải protocol công bố của CDCN. Mỗi frame có score; score video là trung bình các frame. Chọn checkpoint và ngưỡng bằng validation rồi khóa trước khi xem test. CASIA test đã được xem từ lượt trước nên giờ là dữ liệu đánh giá phát triển, chưa phải xác nhận độc lập mới.

## Slide 6: Pseudo-depth target và predicted depth

Thời lượng gợi ý: 65 giây.

3DDFA V2 chỉ sinh nhãn offline cho bona fide; attack dùng zero map theo thiết kế giám sát của nhóm cho ảnh in và replay. QA được báo cáo đầy đủ cho 3.000 bona fide frame và 9.000 attack frame. Pseudo-depth không phải depth đo bằng cảm biến, và ảnh in cũng có thể chứa khuôn mặt mà thuật toán 3D fit được: nhãn zero là quy ước giám sát, không phải kết quả chạy 3DDFA trên attack. CDCN nhận RGB, học so predicted depth với target qua absolute MSE và contrastive depth MSE. Khi suy luận không chạy 3DDFA. Hình là một frame validation thật từ notebook E1 full: RGB, target depth, target mask, predicted depth và histogram. Target mask trong hình giúp kiểm tra nhãn; scorer hiện tại lấy trung bình toàn map. Đây không phải ảnh của năm video test cùng sai.

## Slide 7: E0 · Baseline phân loại RGB

Thời lượng gợi ý: 40 giây.

E0 dùng torchvision MobileNetV3-Small tiền huấn luyện, thay lớp cuối bằng Linear ra một logit, train bằng BCEWithLogits. Khi chấm điểm lấy sigmoid(logit); không dùng softmax nhiều lớp như phần output trong sơ đồ MobileNetV3 tổng quát được cung cấp. Input E0 là 224 và normalization ImageNet; train 5 epoch, best ở epoch 5. E0 giúp kiểm tra dữ liệu, pipeline và tạo baseline RGB tham khảo. E0 và E1 khác cả kiến trúc, loss, kích thước ảnh và normalization; vì vậy so sánh E0–E1 không cô lập riêng tác dụng của depth.

## Slide 8: E1 · Tái lập Official CDCN

Thời lượng gợi ý: 60 giây.

E1 port topology CDCN từ mã ZitongYu/CDCN, khóa commit fd8370e8f32bdd090a3552f5a1fe4c301fa99f2b. Notebook ghi verifier khớp 73 state tensors và max_abs_error bằng 0 trên input kiểm tra. Model hợp nhất đặc trưng ba tỉ lệ ở 32×32, tạo depth qua ReLU rồi lấy spatial mean làm frame score. Depth dự đoán không bị chặn cứng ở 1. Nhóm giữ architecture và official depth loss, nhưng thay pipeline dữ liệu bằng CASIA development split và pseudo-depth 3DDFA V2, dùng scorer toàn map, schedule riêng. Do đó đây là tái lập kiến trúc/loss trong điều kiện nhóm, chưa tái lập toàn bộ kết quả paper. E1 train 30 epoch, chọn best epoch 25 bằng validation depth loss.

## Slide 9: E2 · Chỉ học cách đọc depth map

Thời lượng gợi ý: 60 giây.

E2 nạp đúng best.ckpt của Official E1, khóa trọng số và BatchNorm running statistics. Bản đồ depth phải giống hệt trước và sau train head. Nhánh mới nhận một kênh depth, Conv 1→8→16 với ReLU, global average pooling, Linear 16→1 và sigmoid; chỉ thêm 1.265 tham số. Train head bằng BCE, Adam lr 0,001, batch 8, tối đa 10 epoch. Best checkpoint chọn bằng validation BCE; mỗi model chọn ngưỡng riêng bằng cùng quy tắc validation vì thang điểm khác nhau. Log notebook báo cùng manifest, khớp tensor backbone, depth giống hệt và tái tính được validation E1. Đây là so sánh chính để cô lập tác động của cách đọc map, không thay backbone.

## Slide 10: E2 chưa giảm ACER so với E1

Thời lượng gợi ý: 65 giây.

Đơn vị đánh giá là video; mọi tỉ lệ lỗi trong bảng hiển thị phần trăm, AUC trong khoảng 0–1. E0 là baseline tham khảo: AUC cao hơn nhưng ACER cao hơn ở ngưỡng validation đã khóa. E0–E1 không chứng minh riêng depth tạo cải thiện. So sánh chính là hai hàng E1 và E2: APCER, BPCER, ACER, EER đều giống nhau, AUC E2 giảm 0,000123 theo số hiển thị. Cả hai từ chối nhầm cùng năm video live. Chưa có nhiều seed hoặc khoảng tin cậy, không gán ý nghĩa thống kê cho chênh lệch AUC nhỏ. Kết quả này không ủng hộ giả thuyết frozen head giảm ACER trong lần chạy hiện tại.

## Slide 11: Huấn luyện learned head

Thời lượng gợi ý: 55 giây.

Biểu đồ trích nguyên từ output notebook E2. Train BCE giảm mạnh và gần zero từ epoch 2, trong khi validation BCE thấp nhất ở epoch 1 rồi tăng và dao động. Head đã học hàm score, nhưng học được không đồng nghĩa cải thiện trên video mới so với mean-depth baseline. Best epoch là 1, không phải 10. Mẫu loss phù hợp với quá tự tin trên train hoặc overfitting về BCE; chưa có metric từng epoch để nói validation ACER tăng. Validation ACER E1 và E2 tại checkpoint được chọn đều là zero. Không dùng test để đổi epoch hoặc tìm ngưỡng thắng E1.

## Slide 12: E1 và E2 sai cùng năm video live

Thời lượng gợi ý: 55 giây.

Cả hai đúng cùng 355/360 video: 270 attack và 85 live; sai cùng năm live. E2 sửa được zero video và làm sai thêm zero video tại các ngưỡng tương ứng. BPCER bằng 5/90 và ACER bằng một nửa BPCER vì APCER bằng zero. Có video high, low và normal nên không giải thích toàn bộ lỗi bằng chất lượng thấp. Ví dụ casia_s31_v1, score E1 0,173621 dưới ngưỡng 0,191604; E2 0,311878 dưới ngưỡng 0,411779. Score đã đổi nhưng quyết định vẫn sai. Head frozen chỉ đọc depth và không thể thay bản đồ do backbone sinh. Cần xem RGB và predicted depth thật của năm video này để kết luận nguyên nhân; hình validation ở slide trước không phải bằng chứng về năm lỗi test.

## Slide 13: Chi phí tham số và suy luận

Thời lượng gợi ý: 50 giây.

Head tăng 1.265 tham số, tương đương 0,05635% so với E1. Trong phép đo A100-SXM4-40GB, p50 E1 khoảng 4,519 ms và E2 khoảng 4,243 ms. Đây là số quan sát, không chứng minh head làm model nhanh hơn. Notebook đo E1 trước rồi E2, mỗi model 10 warmup và 50 lượt, input RGB 256, batch 1, có CUDA synchronize. Cần đo lặp và đảo thứ tự để kết luận latency. Forward-only không gồm detector, crop, disk I/O, transfer CPU→GPU hay webcam. FPS là 1000 chia p50, không phải tốc độ camera. Không so latency E0 vì chưa có số đo cùng điều kiện trong bảng này.

## Slide 14: Giới hạn và thí nghiệm tiếp theo

Thời lượng gợi ý: 60 giây.

Giới hạn: một seed, một development protocol CASIA, test đã quan sát, chưa tái lập kết quả trên benchmark của paper, và chưa thử attack ngoài print/replay hay cross-dataset. Ý tưởng classifier đọc predicted depth có tiền lệ UCDCN nên không tuyên bố novelty cho ý tưởng chung. E3 sẽ giữ loại backbone Official CDCN và learned head nhưng train joint bằng depth loss cùng BCE, theo config mới đã đồng bộ; chưa có kết quả thực nghiệm. E4 về staged training và Focal vẫn là hướng trong plan, chưa chốt claim. Tiếp theo cần xem năm lỗi, đánh giá nhiều seed, đo latency lặp và đăng ký benchmark độc lập. CDCN++ hoặc backbone mới hơn là đối chứng cần cân nhắc, không được mô tả như model đã chạy.

## Slide 15: Kết luận sau bốn lượt

Thời lượng gợi ý: 35 giây.

Nhóm đã có câu hỏi nghiên cứu, dữ liệu và metric, baseline E0, tái lập architecture/loss CDCN E1 trong điều kiện của nhóm, rồi thí nghiệm có kiểm soát E2. E2 thay mean score bằng head 1.265 tham số nhưng chưa giảm ACER 2,7778% và không sửa năm lỗi live. Negative result này giúp phân biệt thay cách đọc depth với học lại biểu diễn. Kết luận chỉ áp dụng cho cấu hình frozen head và run seed 42 đã thử. Bước tiếp theo là kiểm tra joint training cùng độ ổn định, thay vì tuyên bố learned head nói chung vô ích hoặc đạt SOTA.

## Slide 16: Phụ lục · Metric và ngưỡng

Phụ lục — mở khi cần trả lời câu hỏi.

APCER là tỉ lệ attack bị chấp nhận thành live; BPCER là tỉ lệ live bị từ chối thành attack; ACER là trung bình hai tỉ lệ. AUC đo thứ hạng trên đường ROC qua ngưỡng, không chứng minh xác suất được calibration. EER là điểm hai loại lỗi bằng nhau theo quy tắc nội suy trong evaluator. ACER báo cáo dùng threshold chọn từ validation; EER/AUC được tính mô tả từ scores của split đánh giá, không dùng để thay threshold đã khóa. Source: src/deepface_pad/metrics.py và output notebook.

## Slide 17: Phụ lục · Phân bố score E1 và E2

Phụ lục — mở khi cần trả lời câu hỏi.

Đây là histogram gốc từ cell 15 notebook E2. E1 score là mean depth; E2 score là sigmoid learned logit. Hai thang điểm khác nhau nên không so score trực tiếp và không đặt chung một ngưỡng. E2 đẩy phần lớn attack về gần zero và live về gần one nhưng metric không cải thiện. Histogram này chưa chứng minh head chỉ là một biến đổi đơn điệu của mean depth. Source: Face_PAD_Round4_Official_Frozen_Head.ipynb.

## Slide 18: Phụ lục · Huấn luyện E0 và E1

Phụ lục — mở khi cần trả lời câu hỏi.

Biểu đồ gốc cell 31 notebook Official E1. E0 chọn epoch 5 và E1 epoch 25 bằng validation. Hai trục loss có thang đo khác nhau: E0 BCE và E1 depth regression loss; không dùng giá trị loss để xếp hạng trực tiếp hai model. Không lấy train curve của E1-Lite Pilot làm bằng chứng Official E1.

## Slide 19: Phụ lục · Sơ đồ MobileNetV3-Small

Phụ lục — mở khi cần trả lời câu hỏi.

Ảnh gốc người dùng cung cấp trong diagrams. Đây là sơ đồ MobileNetV3-Small tổng quát. Nhánh E0 thực tế thay FC cuối thành một logit và dùng sigmoid lúc scoring; phần softmax/Num Classes trong sơ đồ không mô tả output E0 đang dùng. Stem và 11 bottleneck thuộc backbone torchvision; phần input E0 là 224×224. Nguồn ảnh: diagrams/Sơ đồ kiến trúc MobileNetV3-Small.png. Source implementation: src/deepface_pad/models/mobilenet_baseline.py.

## Slide 20: Phụ lục · Sơ đồ Official CDCN

Phụ lục — mở khi cần trả lời câu hỏi.

Ảnh gốc người dùng cung cấp trong diagrams. Topology phù hợp OfficialCDCN trong repository. Resize bilinear về 32×32 ở hai nhánh đầu là giảm kích thước không gian dù tên module là Upsample. Depth cuối dùng ReLU nên không bị giới hạn cứng ở 1. Mặt và map vẽ trong sơ đồ chỉ minh họa, không phải case CASIA thực. Source: diagrams/Sơ đồ kiến trúc CDCN đa tỉ lệ.png; src/deepface_pad/models/cdcn_official.py; pinned author code.

## Slide 21: Phụ lục · Sơ đồ Official CDCN + head

Phụ lục — mở khi cần trả lời câu hỏi.

Ảnh gốc người dùng cung cấp trong diagrams. E2 dùng backbone OfficialCDCN, không phải Lite/Pilot. DepthHead giữ Conv 1→8→16, ReLU, AdaptiveAvgPool2d(1), Flatten, Linear 16→1 và sigmoid. Khi frozen, wrapper đặt backbone về eval để BatchNorm không cập nhật. Mặt và depth trong sơ đồ là minh họa, không phải dữ liệu thực của run. Source: diagrams/Kiến trúc CDCN cải tiến với Learned Depth Head.png; src/deepface_pad/models/cdcn_depth_head.py; src/deepface_pad/models/depth_head.py.

## Slide 22: Phụ lục · Nguồn và artifact thí nghiệm

Phụ lục — mở khi cần trả lời câu hỏi.

Nguồn kết quả được đọc trực tiếp từ output E0.ipynb, Face_PAD_Official_CDCN_E1_Rerun.ipynb và Face_PAD_Round4_Official_Frozen_Head.ipynb trong workspace ngày 02/10/2026; đối chiếu với báo cáo đã lưu. E2 notebook đang có output mới, khác bản clean trong Git. Chưa tải raw CSV, JSON hoặc checkpoint Drive để kiểm toán độc lập. Giữ bản notebook đã chạy và artifact đầy đủ trên Drive. Tham khảo paper CDCN 2020, DC-CDN 2021, UCDCN 2024, SCA-DS 2025 và survey. Các link nguồn ngoài được ghi ở notes những slide liên quan.
