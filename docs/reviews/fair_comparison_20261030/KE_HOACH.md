# Kế hoạch kiểm tra và so sánh công bằng BCE–Focal

Ngày lập: 30/10/2026.

Mục tiêu: xác định tiêu chí phù hợp cho bài toán phân biệt thật/giả; kiểm tra ảnh hưởng của loss, cách chọn checkpoint và tập validation. Hoàn tất phần cần thiết trước khi tiếp tục học Lượt 5–7 và làm phần còn lại của Lượt 7–8.

Mỗi mã EXP là một đơn vị công việc. Không phải mã nào cũng là một lần huấn luyện. Trạng thái “hoàn tất phân tích” không có nghĩa đã hoàn tất thí nghiệm mới.

Kết quả hiện có: [KET_QUA.md](KET_QUA.md). Số liệu tính lại: [MINH_CHUNG_VALIDATION.json](MINH_CHUNG_VALIDATION.json). Danh sách vấn đề gốc: [bàn giao V01–V09](../../handoffs/review_20261030/BAN_GIAO_HOP_NHAT_DEEPFACE_PAD_20261030.md).

## 1. Thứ tự thực hiện

| Mã | Công việc | Vấn đề liên quan | Trạng thái | Có huấn luyện mới? |
| --- | --- | --- | --- | --- |
| EXP-00 | Đối chiếu tài liệu về loss và thước đo đánh giá | V01, V02, V03 | Đã có kết quả, xem KET_QUA | Không |
| EXP-01 | Kiểm tra pipeline và tính lại validation từ CSV đã lưu | V01, V02, V03, V06 | Đã có kết quả; chưa kiểm được checkpoint bị ghi đè | Không |
| EXP-02 | Chốt câu hỏi, dữ liệu và quy tắc so sánh bổ sung | V01–V08 | Đã soạn phương án; chờ người dùng chọn phạm vi | Không |
| EXP-03 | Chuẩn bị code, notebook và chạy thử nhỏ theo phương án đã chọn | V01, V02, V03, V08 | Chưa thực hiện | Chỉ chạy thử nhỏ sau EXP-02 |
| EXP-04 | So sánh có đối chứng E3b–E4 theo protocol mới | V01, V02, V03, V08 | Chưa thực hiện; phụ thuộc EXP-02 | Có |
| EXP-05 | Kiểm tra độ nhạy alpha, gamma hoặc nhóm người validation | V02, V04 | Chưa thực hiện; chỉ chạy phần đã chọn | Có |
| EXP-06 | Đánh giá lặp lại theo seed nếu cần kết luận cấu hình mới | V08 | Chưa thực hiện; không tự mở rộng Lượt 6 cũ | Có |
| EXP-07 | Đối chiếu minh họa CPU và hoàn tất tình huống webcam | V09 | Chưa đo mới; thực hiện sau khi giải quyết lựa chọn mô hình | Không huấn luyện benchmark |
| EXP-08 | Đồng bộ báo cáo, kết luận và tiếp tục học Lượt 5–7 | V01–V09 | Chưa hoàn tất; chờ các bước áp dụng | Không |

Luồng chính: EXP-00 → EXP-01 → EXP-02. Sau đó thực hiện những mã người dùng chọn. EXP-05 và EXP-06 không tự động trở thành công việc bắt buộc. Mọi mã không áp dụng phải ghi rõ lý do, không ghi “đã giải quyết bằng thực nghiệm”.

## 2. Những nguyên tắc cần chốt

1. Phân biệt mục tiêu dự đoán điểm xác suất với mục tiêu giảm lỗi PAD ở cấp video.
2. Chọn checkpoint và chọn cấu hình là hai bước nối tiếp của cùng quy trình lựa chọn. Kiểm tra cả hai.
3. Lượt 6 cũ huấn luyện lại theo seed. Nó không dùng lại nguyên checkpoint E3 seed 42.
4. Giữ nguyên kết quả Lượt 1–7, manifest, ngưỡng và các bản khóa lịch sử. Kết quả mới dùng mã và thư mục mới.
5. Không sử dụng test CASIA đã xem để chọn alpha, gamma, epoch, metric hoặc cấu hình mới. Bất kỳ đánh giá lại nào trên test đó phải được công bố là phân tích bổ sung sau khi đã biết kết quả.
6. Dữ liệu chia theo người. Các frame cùng video không được chia sang những tập khác nhau. Các fold theo người phải giữ toàn bộ video của một người cùng nhóm.
7. Cùng tiêu chí chưa đủ chứng minh công bằng. Cần cùng đầu vào, ngân sách đã xác định, seed ghép cặp, cơ hội điều chỉnh và cách báo cáo.

## 3. EXP-00 — Đối chiếu phương pháp

**Câu hỏi:** Có được huấn luyện bằng Focal và đánh giá bằng BCE khi so với mô hình BCE không?

**Đầu vào:** Bài 2307.02694v3 do người dùng cung cấp; bài Focal gốc; nghiên cứu về ước lượng xác suất và hiệu chỉnh độ tin cậy; tài liệu đánh giá mô hình.

**Thao tác:** Phân biệt đánh giá xác suất với đánh giá quyết định. Ghi điều kiện áp dụng và giới hạn của từng nguồn. Không suy từ một bài tổng quan ra kết luận thiết kế cụ thể đã công bằng.

**Kết quả:** Có thể dùng chung BCE/log loss để đánh giá xác suất đầu ra. Điều đó không chứng minh cấu hình có BCE thấp nhất có ACER tốt nhất. Việc dùng BCE làm tiêu chí quyết định cho PAD cần được giải trình theo mục tiêu. Không có căn cứ kết luận mọi phép so đó đều sai, hoặc E4 chắc chắn thua.

**Điều kiện chuyển bước:** Người đọc phân biệt được “phép đo hợp lệ” và “phép đo đủ phù hợp để chọn mô hình cho mục tiêu đang xét”. Nguồn và diễn giải nằm trong KET_QUA.

## 4. EXP-01 — Kiểm tra dữ liệu và chuỗi lựa chọn đã có

**Câu hỏi:** BCE tác động ở đâu? Chênh lệch quan sát được có chỉ do tỷ lệ lớp không?

**Đầu vào:** CSV validation của ba checkpoint đã chọn; train_log.csv; metrics.json; comparison_freeze.json; manifest; train.py và round6.py.

**Thao tác đã làm:**

1. Đọc cơ chế cập nhật, lưu và nạp checkpoint.
2. Đếm lớp theo train/validation/test từ manifest.
3. Tính BCE riêng live/attack, BCE trung bình hai lớp, Brier và cùng một công thức Focal cho cả ba ứng viên.
4. Phân biệt BCE frame với các chỉ số video.
5. Kiểm tra epoch có BCE thấp nhất và epoch có tổng objective thấp nhất trong joint.
6. Liệt kê tên checkpoint ở cấp gốc của đúng ba thư mục run gốc trên G:. Không mở trọng số hoặc quét toàn bộ Drive.

**Kết quả:** Xem KET_QUA mục 4–6. E4 chọn joint epoch 6 theo BCE; tổng objective thấp nhất ở joint epoch 3. Chưa có dự đoán từng epoch để so ACER giữa hai thời điểm. Checkpoint cấp gốc chỉ có best theo stage và best.ckpt; chưa tìm thấy bản lưu từng epoch trong phạm vi đã liệt kê.

**Giới hạn:** Tính lại cùng Focal trên ba checkpoint đã chọn bằng BCE không kiểm tra được checkpoint E4 đã bị bỏ qua. Đây là phân tích mô tả, không phải lựa chọn lại cấu hình.

**Điều kiện chuyển bước:** Người dùng xem kết quả hiện có trước khi quyết định có cần huấn luyện bổ sung.

## 5. EXP-02 — Chốt protocol và phạm vi xử lý

**Trạng thái:** Đề xuất dưới đây chưa được người dùng chọn. Không thay đổi training hay lựa chọn lịch sử chỉ từ việc có kế hoạch này.

### 5.1. Hai phạm vi để người dùng chọn

| Lựa chọn | Thực hiện | Trả lời được | Giới hạn |
| --- | --- | --- | --- |
| 1. Hoàn tất kiểm toán trên dữ liệu đã có | EXP-00, EXP-01; sửa diễn giải và làm các phần EXP-08 tương ứng | Quy trình cũ hoạt động ra sao; dữ liệu hiện có cho phép kết luận gì | Không trả lời được việc chọn checkpoint khác có cải thiện E4 không |
| 2. Thêm phép thử có đối chứng | Chốt protocol, làm EXP-03 và EXP-04; chỉ mở EXP-05/06 khi đã quyết định | Kiểm tra ảnh hưởng của tiêu chí chọn và loss trong thiết kế mới | Cần GPU; kết quả CASIA test cũ không trở lại thành bằng chứng độc lập chưa từng được xem |

**Đề xuất chuyên môn:** Chọn phạm vi 2 nếu cần giải quyết bằng thực nghiệm câu hỏi checkpoint. Phạm vi 1 đủ cho một báo cáo trung thực về thiết kế cũ, nhưng chưa đủ để kết luận ảnh hưởng của cách chọn đã được giải quyết.

### 5.2. Mục tiêu đánh giá đề xuất

- Mục tiêu chính: giảm lỗi PAD ở cấp video. Công bố APCER, BPCER và ACER; kèm EER/AUC và số lỗi thực.
- BCE/log loss, BCE trung bình hai lớp và Brier: chỉ số bổ sung về điểm dự đoán. Không dùng chúng để tuyên bố hơn về ACER khi ACER đang hòa.
- Khi các chỉ số PAD đã chốt hòa nhau: báo hòa. Nếu cần chọn một cấu hình để triển khai, dùng quy tắc vận hành định trước, chẳng hạn chi phí hoặc cấu hình mốc; không diễn giải thành mô hình đó chính xác hơn.
- Nếu mục tiêu thay thành dự đoán xác suất, việc chọn bằng BCE có thể phù hợp. Khi đó phải chốt trọng số lớp, đơn vị frame/video và dữ liệu hiệu chỉnh xác suất trước.

### 5.3. Phương án dữ liệu phải được quyết định trước khi viết notebook full run

**Phương án nhỏ:** Giữ 16/4/30 để so sánh bổ sung trực tiếp với lịch sử. Kết quả chỉ là thí nghiệm phát triển với bốn người validation cố định. Không tuyên bố đã giải quyết độ nhạy cách chọn người.

**Phương án mạnh hơn:** Dùng các fold theo người trong 20 người train gốc; chỉ fit từng fold bằng người thuộc phần train của fold. Có thể dùng 5 fold, mỗi fold giữ 4 người. Nếu dùng các fold này để chọn siêu tham số, không gọi chính các điểm đó là ước lượng độc lập không thiên lệch; cần vòng ngoài tách biệt hoặc dữ liệu đánh giá mới cho kết luận xác nhận. Lưu danh sách người và quy tắc phân nhóm trước khi chạy. Không dùng checkpoint E1 cũ đã học các người hiện nằm trong fold validation làm initializer.

Chi phí phương án mạnh hơn chưa được đo. Không ước tính giờ GPU như một cam kết trước EXP-03.

### 5.4. Nội dung phải khóa trước full run

1. Danh sách ứng viên: tối thiểu E3b–E4 để so BCE–Focal dưới cùng lịch. E3 là nhánh kiểm tra lịch riêng nếu người dùng muốn bao gồm.
2. Manifest, nhóm người, initializer hợp lệ và hash nguồn.
3. Seed, lịch depth/head/joint, batch size, optimizer, weight decay, số bước cập nhật và số epoch.
4. Alpha, gamma, lambda_cls và ngân sách tìm siêu tham số bằng nhau giữa các họ cấu hình. Nếu giữ alpha/gamma cũ, gọi đúng là cấu hình cố định chưa tối ưu.
5. Tiêu chí chọn checkpoint, cách chọn ngưỡng, xử lý hòa và đơn vị tổng hợp.
6. Phân biệt hai phép hỏi: so loss dưới cùng tiêu chí chọn; và kiểm tra độ nhạy tiêu chí trên cùng quỹ đạo huấn luyện.
7. Dữ liệu nào dùng chọn; dữ liệu nào chỉ đánh giá; điều kiện dừng và nội dung được phép xem.
8. Nơi lưu mỗi epoch, dung lượng và đầu ra tối thiểu. Không ghi đè file lịch sử.

**Điều kiện chuyển EXP-03:** Có lựa chọn của người dùng và một bản đăng ký thiết kế cụ thể. Các đề xuất ở mục này chưa thay thế bản đăng ký đó.

## 6. EXP-03 — Chuẩn bị code và notebook chạy thử nhỏ

**Chỉ bắt đầu sau EXP-02.**

1. Tạo cấu hình và output mới theo mã EXP.
2. Thêm cách tính chỉ số validation video ở từng epoch; giữ nguyên pipeline lịch sử.
3. Lưu trọng số mỗi epoch hoặc đủ bản lưu để so các tiêu chí đã chốt. Lưu validation scores theo epoch, loss thành phần, config và hash.
4. Trong head stage, ghi rõ checkpoint nào được nạp sang joint. Nếu muốn kiểm tra cả ảnh hưởng của tiêu chí ở head stage, cần nhánh huấn luyện riêng; chỉ chọn lại joint cuối không giải quyết được ảnh hưởng này.
5. Viết test cho việc chọn checkpoint, xử lý hòa, tổng hợp video, chống trùng người/video và lưu đủ đầu ra.
6. Chạy thử trên dữ liệu nhỏ, không dùng test để sửa lựa chọn.
7. Đo thời gian và dung lượng để lập ngân sách cho EXP-04.

**Nếu cần người dùng chạy Colab:** Agent chuẩn bị notebook cụ thể trước. Sau đó hướng dẫn từng bước: mở đúng notebook → chọn GPU → mount Drive → kiểm đầu vào/hash → chạy cell thử nhỏ → gửi log thử nhỏ → mới chạy full. Không yêu cầu người dùng tự đoán cell cần chạy. Hiện chưa có notebook mới để chạy.

**Điều kiện chuyển bước:** Test đạt; log, trọng số và score từng epoch đủ; người dùng đã biết ngân sách full run.

## 7. EXP-04 — So sánh có đối chứng và ảnh hưởng của tiêu chí chọn

**Giả thuyết cần kiểm tra:** Cách chọn bằng BCE và cách chọn theo mục tiêu PAD có thể lấy các checkpoint khác nhau. Mức ảnh hưởng tới lỗi trên dữ liệu không tham gia lựa chọn cần được đo.

**Đối chứng chính:** E3b BCE và E4 Focal, cùng lịch và điều kiện đã khóa. Không quy chênh lệch E3–E4 hoàn toàn cho loss vì lịch khác nhau.

**Thao tác:**

1. Huấn luyện theo thiết kế EXP-02, lưu đầu ra mỗi epoch.
2. Trên cùng quỹ đạo joint, áp dụng các quy tắc chọn đã đăng ký. Không lựa chọn quy tắc sau khi thấy kết quả đánh giá.
3. So sánh checkpoint theo lỗi PAD, chỉ số điểm, nhóm lớp và loại tấn công.
4. Ghi trường hợp hòa; không tự thêm một metric mới để buộc có người thắng.
5. Đánh giá trên phần dữ liệu dành cho đánh giá theo thiết kế. Nếu xem lại test CASIA cũ, gắn nhãn phân tích bổ sung sau quan sát test, không gọi là xác nhận độc lập.

**Kết quả phải lưu:** Epoch được chọn theo từng quy tắc; score frame/video; ngưỡng và nguồn chọn; số lỗi live/attack; chỉ số từng nhóm; chi phí; tất cả kết quả bất lợi.

**Điều kiện hoàn tất:** Có bảng ảnh hưởng của cả loss và tiêu chí. Nếu không thấy khác biệt, ghi không thấy khác biệt trong thiết kế này. Nếu thiếu checkpoint/dữ liệu, ghi chưa trả lời được.

## 8. EXP-05 — Kiểm tra alpha, gamma hoặc cách chia người

**Chỉ thực hiện sau khi người dùng chọn câu hỏi còn cần kiểm tra.**

- Alpha: kiểm tra giả thuyết tăng trọng số live có làm thay đổi BPCER không. Giữ gamma và các yếu tố khác cố định. Không mặc định alpha=0,75 tối ưu chỉ vì cân bằng tổng trọng số theo tỷ lệ lớp.
- Gamma: khảo sát hữu hạn các giá trị đã chốt, ví dụ 0, 1, 2. Gamma=0 với alpha không đồng đều là BCE có trọng số lớp, không phải BCE không trọng số. Muốn đối chứng BCE thuần cần ghi đúng alpha và hệ số scale.
- Lambda_cls: cùng lambda không có nghĩa cùng đóng góp loss hoặc gradient. Nếu điều chỉnh, dành ngân sách tương đương và không trộn kết quả đó với phép thử chỉ đổi gamma.
- Cách chia người: dùng fold theo người với initializer không học người của fold validation. Không đổi đúng bốn người vì tìm được kết quả đẹp hơn.

**Đầu ra:** Bảng độ nhạy theo thiết kế định trước. Không chọn phương án dựa trên test cũ.

## 9. EXP-06 — Lặp lại theo seed

Nếu cấu hình mới cần được đem so với E1, đăng ký một batch mới. Mỗi seed huấn luyện E1 và ứng viên tương ứng theo cùng protocol đã chốt; so sánh ghép cặp. Không dùng chỉ seed thuận lợi và không gộp các lần chấm trên cùng video thành các test độc lập.

Kết quả Lượt 6 cũ được giữ như bằng chứng của E3 theo quy tắc cũ. Thay đổi cách chọn cấu hình không tự động cập nhật sáu run lịch sử. Nếu muốn kết luận riêng tác dụng head, phải kiểm soát ngân sách/weight decay hoặc công bố giới hạn.

**Đầu ra:** Kết quả từng seed, trung bình, độ lệch chuẩn, chênh lệch ghép cặp và chi phí. Số seed chưa được chốt.

## 10. EXP-07 — CPU và webcam

1. Giữ hình CPU là minh họa nếu chưa đạt đối chiếu CUDA. Không đổi tolerance để ghi đạt.
2. Dùng log/crop/detection đã có để phân biệt lỗi tìm mặt và lỗi PAD. Alpha là giả thuyết có thể ảnh hưởng, chưa phải nguyên nhân đã chứng minh của lỗi live.
3. Chốt mô hình và cấu hình frontend trước đo mới. Không chỉnh ngưỡng benchmark theo cảnh webcam cho tới khi nhận live.
4. Khi người dùng có ảnh giấy, hướng dẫn một cảnh print riêng theo [WEBCAM_GUIDE](../../../reports/round7/WEBCAM_GUIDE.md).
5. Hướng dẫn cảnh reset: đợi đủ 5/5 → rời khung đến 0/5 → quay lại và đợi đủ 5/5.
6. Mỗi cảnh lưu video riêng, frames.csv và summary.json. Ghi FPS vòng, frame PAD/s và TTD hoặc lý do thiếu.

**Điều kiện hoàn tất:** Có bằng chứng mỗi cảnh; giữ lỗi nếu còn lỗi. Chưa tự bật camera hoặc chạy đo trong đợt lập kế hoạch này.

## 11. EXP-08 — Kết thúc xử lý và trở lại học/báo cáo

1. Đối chiếu V01–V09 với kết quả và đánh dấu từng vấn đề: đã sửa diễn giải; đã kiểm thực nghiệm; hoặc còn giới hạn.
2. Đồng bộ nguồn báo cáo và paper sau khi chốt kết luận. Giữ sửa đổi đang có của người dùng, không dựng đè Word lịch sử.
3. Nếu dựng tài liệu mới, thực hiện builder/render/kiểm nội dung/kiểm bố cục/test theo quy trình repository và tạo output mới.
4. Học tiếp Lượt 5: loss → cập nhật → checkpoint → ngưỡng → cấu hình → test. Sau đó học Lượt 6: seed và giới hạn; Lượt 7: phân tích lỗi và webcam.
5. Chỉ tiếp tục phần còn lại Lượt 7–8 khi đã xác định mô hình dùng và giới hạn cần trình bày. Không đánh dấu phần luyện báo cáo hoặc nộp bài hoàn tất từ việc có tài liệu.

## 12. Mẫu ghi kết quả cho mỗi mã

Khi có kết quả mới, bổ sung vào KET_QUA với mã EXP tương ứng:

- Câu hỏi và giả thuyết đã khóa.
- Lựa chọn của người dùng; ngày chốt; config/commit/hash.
- Thao tác thực tế và phần chưa chạy.
- Bảng kết quả, mẫu số, đơn vị frame/video/người và nguồn.
- Đối chiếu với điều kiện hoàn tất.
- Kết luận được phép đưa ra và giới hạn.
- Bước tiếp theo; hỗ trợ người dùng cần làm.

Không ghi nhật ký trao đổi hoặc quy ước văn phong vào báo cáo kết quả.
