# Kế hoạch giải quyết V01–V09 trên CASIA-FASD

Ngày lập: 30/10/2026. Phạm vi cập nhật: 31/10/2026.

## 1. Mục tiêu và phạm vi đã xác định

Hoàn tất kiểm tra phương pháp và các vấn đề V01–V09 trước khi chốt báo cáo và tiếp tục phần còn lại Lượt 7–8. Ưu tiên khả năng phân biệt bona fide/attack; báo riêng attack lọt qua và live bị từ chối.

Theo yêu cầu mới nhất, **không kiểm kê, chuẩn bị hoặc thí nghiệm OULU-NPU lúc này**. Không mở OCIM, thêm dataset hoặc nghiên cứu cross-type trong kế hoạch này. Các thuật ngữ benchmark chỉ được đối chiếu để mô tả đúng phạm vi CASIA hiện tại.

Giữ nguyên E0/E1, kết quả và bản khóa Lượt 1–7. E2 là đối chiếu lịch sử. Nhánh mới dùng output riêng. Giữ nguyên checkpoint E1 làm initializer không có nghĩa khóa bản sao backbone khi huấn luyện E3/E4.

Đây là kế hoạch đã được điều chỉnh theo phạm vi người dùng yêu cầu. Nó chưa là đăng ký thông số full run. Agent được tiếp tục kiểm tra nguồn và chuẩn bị thiết kế; không ghi thí nghiệm chưa chạy là hoàn tất.

Theo dõi kết quả tại [KET_QUA.md](KET_QUA.md), số liệu đã tính lại tại [MINH_CHUNG_VALIDATION.json](MINH_CHUNG_VALIDATION.json) và [MINH_CHUNG_NGUONG_20261031.json](MINH_CHUNG_NGUONG_20261031.json). Vấn đề gốc: [bàn giao V01–V09](../../handoffs/review_20261030/BAN_GIAO_HOP_NHAT_DEEPFACE_PAD_20261030.md).

Nghiên cứu NIST/PAD và kiểm tra chỉ số được lưu riêng tại [nghiên cứu tài liệu](research_pad_metrics_20261031/NGHIEN_CUU_NIST_PAD.md) và [kiểm tra code/CSV](research_pad_metrics_20261031/KIEM_TRA_CODE_VA_CSV.md). Hai báo cáo phân biệt lỗi số học, lỗi kiểm tra đầu vào và khác biệt protocol.

## 2. Hướng nghiên cứu được đề xuất

1. Kiểm tra lại chuỗi lựa chọn và lỗi từ score đã lưu, đặc biệt là sự khác nhau giữa khả năng xếp hạng và ngưỡng vận hành.
2. Làm rõ tỷ lệ 1:3 ở ba nơi: huấn luyện, lựa chọn checkpoint và chấm điểm. Không đổi cả ba cùng lúc.
3. Dùng một tiêu chí PAD chính cho phép thử có đối chứng. AUC/EER và BCE là thông tin hỗ trợ hoặc quy tắc phân định được khóa trước, không mở mỗi metric thành một cuộc thi riêng.
4. Chỉ kiểm tra thêm loss/trọng số lớp sau khi đã tách ảnh hưởng tiêu chí và ngưỡng.
5. Chỉ mở nhiều seed sau khi thiết kế nhỏ chạy đúng và ngân sách đã rõ.
6. Chốt mô hình/giới hạn để hoàn tất CPU, webcam và tài liệu.

**Đề xuất chính:** tiếp tục đánh giá đồng thời hai loại lỗi bằng ACER, kèm APCER/BPCER và số lỗi thực. Chưa chuyển sang tối ưu chỉ chống lọt attack. APCER=0 trên mẫu test cũ không bảo đảm rủi ro thực bằng 0; nhiều lỗi live cũng chưa chứng minh đổi ưu tiên an ninh sẽ giúp ích.

## 3. Tiến trình theo mã EXP

| Mã | Công việc | Vấn đề | Trạng thái |
| --- | --- | --- | --- |
| EXP-00 | Chốt ý nghĩa loss, metric, protocol và phạm vi kết luận | V01–V06 | Có kết quả nghiên cứu; cần học cùng người dùng |
| EXP-01 | Phân tích score cũ: threshold, lỗi, nhóm người/chất lượng và trọng số lớp | V01–V03, V06, V08 | Có số liệu validation; mới bổ sung kiểm tra ngưỡng; các phân tích chi tiết còn chờ |
| EXP-02 | Đăng ký thiết kế, chốt nguồn dữ liệu và cách chọn trước full run | V01–V08 | Kế hoạch cụ thể bên dưới; chưa khóa thông số thực thi |
| EXP-03 | Code/notebook/test và chạy thử nhỏ | V01–V03, V08 | Chưa thực hiện |
| EXP-04 | Nhánh 5.1 và 5.2 kiểm tra tiêu chí checkpoint và độ nhạy ngưỡng | V01, V03, V08 | Chưa train mới |
| EXP-05 | Nhánh 5.3 kiểm tra ảnh hưởng trọng số lớp nếu còn cần | V02, V04, V06 | Chưa thực hiện; giới hạn số yếu tố thay đổi |
| EXP-06 | Nhánh 6.x lặp lại thiết kế đã chọn theo seed | V08 | Chưa thực hiện |
| EXP-07 | CPU và webcam | V09 | Giữ giới hạn đã biết; chưa đo mới |
| EXP-08 | Đóng từng V, đồng bộ báo cáo/paper và học tiếp | V01–V09 | Chưa hoàn tất |

Thứ tự: EXP-00 → EXP-01 → EXP-02 → EXP-03 → EXP-04. EXP-05 chỉ chạy nếu câu hỏi trọng số lớp còn cần kiểm tra. EXP-06 chạy theo phạm vi được chốt sau khi có chi phí thử nhỏ; không chọn nhánh dựa vào test. Sau đó EXP-07/08. Không cần làm mọi tổ hợp để được ghi hoàn tất; phần không chạy phải giữ giới hạn tương ứng.

## 4. EXP-00 — Hiểu đúng điều đang đánh giá

**Kết quả cần nắm:**

- BCE/Focal là objective dùng trên train; có thể tính một công thức chung để đánh giá điểm của các mô hình khác loss. BCE thấp hơn không tự động có ACER hoặc calibration tốt hơn.
- Chọn checkpoint, chọn ngưỡng và chọn cấu hình là các bước liên quan, nhưng thay đổi một bước chưa giải quyết ảnh hưởng các bước khác.
- AUC đo xếp hạng qua các ngưỡng; nó không chọn một threshold tối ưu để vận hành.
- Ngưỡng lịch sử tối ưu ACER video validation theo implementation đã khóa. Đây không phải bảo đảm tối ưu test hoặc tối ưu an ninh.
- Tên intra/cross-dataset và intra/cross-type mô tả hai trục khác nhau. OCIM là tập benchmark và thiết kế leave-one-dataset-out trong các công trình cụ thể, không đồng nghĩa bốn ô phân loại trên và không phải yêu cầu mọi đồ án phải thực hiện.
- NIST IR là báo cáo kỹ thuật; không mặc định dataset/protocol nghiên cứu được NIST chứng nhận chỉ vì dùng APCER/BPCER. Tiêu chuẩn, báo cáo đánh giá và protocol của tác giả dataset phải được dẫn riêng.

**Người dùng:** giải thích lại ngắn gọn sự khác nhau giữa tốt về score, tốt về xếp hạng và ít lỗi tại một threshold. Không cần học toàn bộ paper trước khi chuyển bước.

## 5. EXP-01 — Chẩn đoán bằng dữ liệu đã có

Không train hoặc inference toàn tập. Không chọn lại mô hình/ngưỡng lịch sử trên test.

### EXP-01a. Chuỗi lựa chọn và threshold

Nguồn: [train.py](../../../src/deepface_pad/train.py), [metrics.py](../../../src/deepface_pad/metrics.py), [runbook Lượt 5](../../../reports/ROUND_5_CASIA_RUNBOOK.md), [kết quả validation](../../../reports/ROUND_5_FULL_VALIDATION_2026-10-16.md).

Đã xác minh: head/joint chọn checkpoint bằng BCE frame; cuối stage nạp best. Epoch sau chạy từ trọng số hiện tại trong bộ nhớ, không nạp file last.ckpt. Sau joint, chọn threshold theo thứ tự (ACER, |APCER-BPCER|, threshold) nhỏ nhất trên tập candidate. Các candidate là các score phân biệt và hai điểm ngoài biên.

Cả E3/E3b/E4 đều có khoảng threshold cho 0 lỗi validation: (max score attack, min score live]. Threshold đã chọn bằng min score live. Điều này do candidate và quy tắc xử lý hòa, không do AUC. Chưa chứng minh nguyên nhân lỗi test.

**Phần cần làm tiếp:** vẽ phân bố score và đường APCER/BPCER theo threshold; đánh dấu threshold đã khóa và khoảng tối ưu validation. Phân tích độ nhạy trước hết trên validation. Nếu minh họa test đã xem, ghi mô tả hậu kiểm, không dùng để chọn threshold mới hoặc báo tối thiểu test như kết quả vận hành.

### EXP-01b. Đếm lỗi và đối chiếu nhóm

Nguồn: [kết quả test Lượt 5](../../../reports/ROUND_5_TEST_RESULTS_2026-10-16.md) và các CSV đã lưu. Tại ngưỡng đã khóa: E1/E2 từ chối 5/90 live, E3/E3b 9/90, E4 8/90; APCER=0 trên 270 attack cho các mô hình này. Giữ nguyên bảng.

Đối chiếu lỗi theo người, chất lượng, loại tấn công; tách lỗi frontend webcam với lỗi phân loại. Xem AUC, EER và lỗi tại ngưỡng cùng nhau. Ví dụ E4 có AUC cao hơn E1 nhưng ACER ở threshold validation cao hơn; không suy rằng threshold là nguyên nhân duy nhất.

### EXP-01c. Phân tích 1:3 trước khi train

- Xác minh tỷ lệ theo video, frame và người; train/validation/test đều live:attack=1:3.
- BCE mẫu hiện tại = 0,25 × BCE live + 0,75 × BCE attack; ACER cho APCER/BPCER trọng số 1:1.
- Báo BCE riêng từng lớp, macro BCE, số lỗi và các chỉ số đã có. Không cần lấy bớt video attack để tính ACER.
- Alpha live=0,25/attack=0,75 không ưu tiên live thiểu số. Không suy trực tiếp tỷ lệ gradient hoặc nguyên nhân lỗi test từ alpha.
- So sánh dữ liệu theo nhóm người/chất lượng; cùng tỷ lệ lớp không chứng minh cùng độ khó.

**Đầu ra:** bảng/biểu đồ chẩn đoán mới trong output EXP-01; kết luận được và chưa được ghi trong KET_QUA. Mẫu độc lập chính là người/video, không coi 20 frame/video là 20 lần đánh giá độc lập. Nếu ước lượng bất định bằng lấy mẫu lại, lấy theo người và giữ mọi video cùng người; bốn người validation vẫn giới hạn độ chính xác.

### EXP-01d. Kiểm tra độc lập APCER/BPCER/ACER — phải xong trước nhánh mới

1. Đối chiếu NIST IR 8491 và nguồn PAD: định nghĩa hai lỗi, mẫu số, chiều score, ranh giới bằng threshold, nhóm tấn công và trường hợp không trả quyết định.
2. Tính lại từ số đếm confusion tại threshold đã khóa; đối chiếu CSV, JSON và báo cáo. Kiểm đơn vị tỷ lệ 0–1 so với phần trăm, số video và phép mean frame → video; không trộn mẫu số attack/live.
3. Kiểm pooled APCER so với phân rã theo attack_type. Không tự gọi attack_type của CASIA là đầy đủ PAI species hoặc gọi max ba nhóm là tuân thủ toàn bộ ISO.
4. Kiểm đủ dự đoán trên manifest và ghi rõ cách xử lý nonresponse. Không đem trường hợp no_face webcam gộp vào benchmark như thể có score hợp lệ.
5. Kiểm đầu vào không hợp lệ: threshold NaN/Inf, nhãn không nhị phân trước ép kiểu, score không hữu hạn, thiếu một lớp, shape và trường hợp score bằng threshold.
6. Ghi trạng thái riêng: đúng số học trên dữ liệu đã dùng; không khớp protocol tham chiếu; có lỗi phòng vệ đầu vào; hoặc chưa đủ bằng chứng.

Phát hiện lỗi phòng vệ không tự động làm sai mọi kết quả cũ. Nếu phát hiện sai số học thật ở dữ liệu đã báo, giữ bản cũ và xuất bản đính chính có nguồn; không sửa âm thầm file khóa.

## 6. EXP-02 — Khóa thiết kế và đóng các vấn đề dữ liệu

### 6.1. Phần giữ nguyên

CASIA 16/4/30 người, manifest, target depth, tiền xử lý và 20 frame/video. E0/E1, threshold và kết quả lịch sử không bị ghi đè. Không đổi bốn người validation chỉ để tìm kết quả đẹp hơn. Không dùng E1 đã học một người làm initializer rồi chuyển người đó sang validation.

Không bổ sung dataset lúc này. Kết quả mới trên test CASIA đã xem là phân tích bổ sung sau quan sát; không tuyên bố đã có phép xác nhận trên test chưa từng được dùng. Bổ sung protocol chuẩn không tự phục hồi tính độc lập của test cũ.

### 6.2. Bản đăng ký phải có trước EXP-03/full run

1. Câu hỏi chính: ảnh hưởng tiêu chí checkpoint, ảnh hưởng threshold hay ảnh hưởng trọng số lớp.
2. Candidate: E3b–E4 là cặp chính cùng lịch; E3 chỉ thêm nếu cần phân tích lịch. Không tự mở E2 mới.
3. Config/commit/hash, seed, initializer, lịch epoch, số bước cập nhật, optimizer, LR, weight decay, batch và augmentation.
4. Objective và alpha/gamma/lambda; mỗi phép thử chỉ thay yếu tố đã nêu.
5. Tiêu chí chọn ở từng stage, threshold và xử lý hòa. Không chỉ ghi tiêu chí joint rồi bỏ ngỏ head stage.
6. Các nhánh sẽ báo cáo; dữ liệu dùng chọn; số lần xem kết quả; đơn vị phân tích; cách xử lý lỗi/thiếu đầu ra.
7. Quy tắc chọn ứng viên sang nhiều seed dựa trên nguồn lựa chọn đã định trước; không chọn từ test. Nếu các chỉ số chính hòa, báo hòa và giữ đại diện theo quy tắc đã chốt, không gọi là chính xác hơn.
8. Lưu checkpoint và score validation mỗi epoch; lưu riêng thành phần depth và classification; đo ngân sách sau thử nhỏ.

### 6.3. Xử lý V04, V05, V06, V07 ngay trong thiết kế

| Vấn đề | Cách giải quyết trong phạm vi hiện tại | Giới hạn còn lại |
| --- | --- | --- |
| V04: người 4/9/14/19 | Ghi đúng lựa chọn cố định; không có chứng cứ cho lý do đại diện/ngẫu nhiên | Không tuyên bố đã kiểm độ nhạy theo cách chia khác |
| V05: protocol/test | Ghi intra-dataset, intra-type, chia 16/4/30; công bố lịch sử xem test | Không gọi kết quả bổ sung là xác nhận độc lập |
| V06: APCER gộp/1:3 | Công bố mẫu số, pooled APCER và BPCER; thêm phân rã loại tấn công khi phù hợp | Không tự gọi ba attack_type là đầy đủ PAI species theo chuẩn |
| V07: HR_1 | Giữ nhãn theo video; giới hạn tuyên bố ở 1.000 frame/50 video đã dùng | Không khẳng định toàn bộ archive Kaggle đã kiểm |

## 7. EXP-03 — Chuẩn bị notebook và chạy thử nhỏ

1. Tạo mã/output mới; không ghi đè runs/artifacts cũ.
2. Bổ sung logging từng thành phần loss, checkpoint và score validation theo epoch.
3. Tính threshold và metric video nhất quán; thực hiện đúng xử lý hòa đã đăng ký.
4. Test chọn checkpoint, tổng hợp frame/video, chiều live=1, thao tác stage, không trùng người/video và lưu đủ đầu ra.
5. Chạy thử nhỏ; đo thời gian/dung lượng và trình ngân sách trước full run.

Trước khi chạy nhánh mới, sửa và test các lỗi kiểm tra đầu vào được xác nhận trong EXP-01d. Giữ nguyên định nghĩa hợp lệ, threshold và số liệu lịch sử; nếu thay đổi protocol tổng hợp, dùng phiên bản evaluator/nhãn chỉ số mới. Lần rà soát kế hoạch này chưa sửa code evaluator.

Nếu cần người dùng chạy Colab: agent chuẩn bị notebook cụ thể, rồi hướng dẫn theo từng cell: mở → chọn GPU → mount Drive → kiểm nguồn/hash → chạy thử → xem log → chạy full khi thiết kế và ngân sách đã chốt. Hiện chưa có notebook mới để chạy.

## 8. EXP-04 — Các nhánh Lượt 5 về tiêu chí và threshold

Các nhánh dưới đây thay thế danh sách đề xuất 5.x trước đó chưa được thực hiện. Không biến mỗi metric thành một nhánh bắt buộc.

| Nhánh | Thay đổi chính | Giữ nguyên | Kết luận có thể kiểm tra |
| --- | --- | --- | --- |
| 5.0 | Không đổi: BCE chọn head/joint; threshold ACER theo code cũ | Kết quả lịch sử | Mốc đã có |
| 5.1 | Chọn checkpoint head/joint theo chỉ số PAD video: ACER thấp → EER thấp → AUC cao; hòa hoàn toàn giữ epoch sớm nhất | Objective, lịch và đầu vào của từng candidate; depth stage theo depth objective; threshold theo code cũ | Ảnh hưởng của chính sách chọn checkpoint toàn chuỗi head/joint |
| 5.2 | Phân tích quy tắc đặt threshold trong khoảng ACER validation tối ưu | Checkpoint đã chọn của 5.0/5.1; không cập nhật trọng số | Độ nhạy quyết định đối với các threshold cùng tối ưu trên validation |
| D1 | Đối chiếu checkpoint có tổng objective thấp nhất trong từng run | Không so raw tổng loss khác công thức giữa BCE và Focal | Giải thích cực tiểu depth + Focal khác cực tiểu BCE |

**5.1:** Đây là can thiệp vào chính sách lựa chọn cả head/joint, không phải ablation chỉ đổi joint. Nếu head checkpoint khác, cần run joint riêng. Với E3 không có head stage riêng, chỉ joint. Tất cả vẫn chạy đủ lịch epoch đã khóa, không thêm early stopping. Thực hiện cặp E3b/E4 trước; thêm E3 cần được đăng ký rõ.

Để so quy tắc cũ và mới trên dữ liệu lưu đủ, có thể cần chạy lại nhánh BCE chọn checkpoint theo thiết kế cũ vào output mới; không khẳng định tái lập chính xác run cũ bằng seed đơn lẻ. E1 không train lại. Không thể chấm epoch bị ghi đè chỉ từ train_log.csv.

**5.2:** Trước hết làm độ nhạy mô tả bằng dữ liệu đã lưu. Quy tắc thay threshold dùng cho nhánh mới phải khóa trước: đề xuất trung điểm một khoảng hữu hạn có ACER validation tối thiểu; nếu nhiều khoảng, chọn khoảng rộng nhất rồi khoảng có biên trái nhỏ nhất; nếu không có khoảng hữu hạn phù hợp thì dùng quy tắc lịch sử. Cần mô tả endpoint và test trước áp dụng. Đây là kiểm tra quy ước threshold, không phải benchmark được NIST chứng nhận hoặc phương pháp đã chứng minh tốt hơn. Không chọn vị trí trong khoảng dựa trên số live test được sửa.

**D1:** E4 cũ có tổng depth + Focal thấp nhất joint epoch 3, BCE thấp nhất epoch 6. Tìm checkpoint/score đúng epoch trước; nếu thiếu, ghi không phục hồi được và kiểm tra trên run mới. Epoch 3 mới không phải epoch 3 cũ. Lưu riêng loss thành phần để biết yếu tố nào làm tổng loss giảm.

**AUC/EER:** tiếp tục báo cáo và dùng trong quy tắc đã khóa; không mở nhánh chỉ ưu tiên AUC ngay lúc này vì chưa giải quyết trực tiếp câu hỏi threshold và validation đang hòa.

**Ưu tiên an ninh:** chưa mở nhánh ràng buộc APCER thành nhiệm vụ chính. Nếu sau EXP-01/04 người dùng có yêu cầu vận hành cụ thể, đăng ký riêng mức APCER và tối thiểu hóa BPCER dưới ràng buộc đó trên validation. Không tối ưu APCER đơn lẻ, không suy 0 lỗi = rủi ro thực bằng 0.

## 9. EXP-05 — Nhánh 5.3 về mất cân bằng lớp

Chỉ bắt đầu sau phân tích 1:3 của EXP-01 và khi đã khóa một chính sách checkpoint/threshold. Đó là vị trí phù hợp để thay trọng số huấn luyện, tránh trộn hiệu ứng với metric.

**Phép thử nhỏ đề xuất:** giữ lịch E3b, dùng BCE không trọng số làm đối chứng và thêm BCE với trọng số hai lớp chuẩn hóa có cùng tổng trọng số kỳ vọng trên train. Với live:attack=1:3, một lựa chọn là w_live=2 và w_attack=2/3; trung bình trọng số train bằng 1, mỗi lớp đóng góp tổng trọng số bằng nhau. Đây là thiết kế đối chứng về trọng số, chưa bảo đảm cùng gradient hoặc tối ưu.

Nếu triển khai tương đương bằng pos_weight=3, cần chuẩn hóa scale phù hợp; dùng trực tiếp pos_weight=3 không bảo đảm cùng quy mô classification objective với đối chứng và có thể đổi tương quan với depth loss. Ghi công thức và test trước khi chạy.

Không đồng thời đổi sampler, gamma, alpha và lambda. Chưa mở grid gamma hay bộ lấy mẫu cân bằng. Nếu chọn khảo sát Focal alpha thay vì weighted BCE, lập phép thử riêng và xử lý scale; giữ gamma cố định. Gamma=0 với alpha không đồng đều không phải BCE thuần.

**Đầu ra:** per-class loss, lỗi tại threshold đã định trước, score và chi phí; kết quả không cải thiện vẫn phải giữ. Không chọn cấu hình từ test; không đưa mọi phương án vào 6.x chỉ vì có số đo.

## 10. EXP-06 — Các nhánh Lượt 6.x

- 6.0: sáu run E1/E3 seed 43/44/45 lịch sử, giữ nguyên.
- 6.1: lặp lại chính sách checkpoint của 5.1 trên seed đã chốt.
- 6.2: độ nhạy threshold 5.2 trên checkpoint/score của cùng run 6.0/6.1 khi tương thích; đổi threshold đơn thuần không cần train mới.
- 6.3: chỉ lặp lại nhánh trọng số 5.3 nếu câu hỏi này được chọn cho giai đoạn nhiều seed.

Dùng E1 cùng seed đã khóa sau kiểm hash/protocol; không tự train lại E1. Nếu thiếu initializer hợp lệ cho seed mới, dừng ở quyết định phạm vi, không thay ngẫu nhiên initializer.

So sánh ghép cặp trên cùng video; báo từng seed, mean/SD và số lỗi thực. Không coi các lần chấm cùng 360 video là những test độc lập. Kết quả CASIA bổ sung vẫn giới hạn bởi test đã xem và cỡ mẫu. Không tăng seed liên tục đến khi có kết quả đẹp.

## 11. EXP-07 — CPU, webcam và V09

1. Giữ hình CPU là minh họa khi chưa đạt dung sai CUDA. Không đổi tolerance để ghi đạt.
2. Đối chiếu score/log/crop hiện có; tách mất detection, reset cửa sổ và lỗi PAD. Alpha của E4 không giải thích trực tiếp webcam E3.
3. Chốt model/threshold/frontend trước đo mới. Không sửa threshold benchmark để demo nhận live.
4. Khi có người vận hành và ảnh giấy, hướng dẫn một cảnh print theo [WEBCAM_GUIDE](../../../reports/round7/WEBCAM_GUIDE.md), output mới.
5. Hướng dẫn reset: đủ 5/5 → rời đến 0/5 → quay lại đủ 5/5 và có quyết định.
6. Lưu video riêng, frames.csv, summary.json; báo FPS vòng, frame PAD/s và TTD hoặc lý do thiếu.

Không tự bật camera. Chưa chứng minh nguyên nhân thì giữ là giả thuyết. V09 có thể đóng bằng mô tả giới hạn nếu không đo thêm, nhưng không ghi các cảnh thiếu là đã đạt.

## 12. EXP-08 — Đóng V01–V09 và đồng bộ tài liệu

| Vấn đề | Bằng chứng để ghi trạng thái kết thúc |
| --- | --- |
| V01 | Có kết quả ảnh hưởng checkpoint hoặc ghi rõ chưa kiểm; không chỉ sửa văn bản rồi nói đã giải quyết thực nghiệm |
| V02 | Công thức/alpha/gamma/scale được mô tả đúng; kết luận chỉ cho cấu hình đã thử |
| V03 | Người đọc phân biệt train → checkpoint → threshold → cấu hình → test; Lượt 6 train theo seed |
| V04 | Nêu rõ mã người cố định và lý do chưa tìm thấy; không bịa đại diện/ngẫu nhiên |
| V05 | Ghi protocol và lịch sử xem test riêng; không đồng nhất CASIA hiện tại với OCIM hay protocol gốc đầy đủ |
| V06 | Có mẫu số, pooled APCER, BPCER và cách tính ACER; tách đánh giá với trọng số training |
| V07 | Phạm vi HR_1 khớp dữ liệu đã kiểm; không cần kiểm archive mới để đóng giới hạn phát biểu |
| V08 | Giữ seed bất lợi, khác biệt budget/weight decay; không quy nhân quả riêng head hoặc loss khi có yếu tố khác |
| V09 | Có bằng chứng cảnh đã đo hoặc ghi rõ thiếu; CPU không được gọi tái lập chính xác CUDA |

Đồng bộ nguồn báo cáo và paper sau khi chốt kết luận; giữ sửa đổi có sẵn của người dùng. Nếu dựng Word mới, làm builder/render/test và kiểm bố cục vào output mới. Không tự đánh dấu luyện trình bày/nộp bài hoàn tất.

Học song song từng EXP: giải thích một câu hỏi → xem đúng bằng chứng → người dùng diễn giải lại → thực hiện phần đã chốt → cập nhật kết quả. Sau phần phương pháp, tiếp tục Lượt 5–7 rồi việc còn lại Lượt 7–8.

## 13. Cách lưu kết quả và các điểm cần chốt

KET_QUA ghi theo mã EXP: câu hỏi, config/commit/hash, việc thực sự đã làm, bảng kết quả có mẫu số, kết luận và giới hạn, bước tiếp theo. Output thô ở thư mục riêng gắn mã nhánh; kết quả Markdown dẫn tới đó. Không chép nhật ký hội thoại vào Git hoặc báo cáo.

Trước full run cần chốt: candidate và số seed sau đo chi phí; tiêu chí/threshold chính xác; quy tắc chọn ứng viên khi hòa; nhánh trọng số có cần chạy hay giữ giới hạn. Không yêu cầu quyết định tất cả ngay trước khi người dùng hiểu EXP-01.

## 14. Nguồn phương pháp

- [Focal Loss gốc](https://arxiv.org/html/1708.02002).
- [Loss Functions and Metrics in Deep Learning](https://arxiv.org/html/2307.02694v3).
- [NIST IR 8491 về đánh giá PAD](https://doi.org/10.6028/NIST.IR.8491): phân biệt APCER/BPCER; không là bằng chứng CASIA của nhóm được chứng nhận.
- [scikit-learn về ngưỡng quyết định](https://scikit-learn.org/stable/modules/classification_threshold.html).

Không mở rộng nguồn dữ liệu ngoài phạm vi V01–V09 trong phiên này.
