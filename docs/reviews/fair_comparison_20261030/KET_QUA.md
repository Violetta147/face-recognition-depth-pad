# Kết quả rà soát phép so sánh BCE–Focal và quy trình lựa chọn

Ngày đối chiếu: 30/10/2026.

Phạm vi hoàn tất: EXP-00 và phần phân tích dữ liệu lưu của EXP-01. Chưa huấn luyện mới, chọn lại mô hình hoặc đo webcam. EXP-02 đã có phương án nhưng chưa được người dùng chốt. Theo dõi từng bước tại [KE_HOACH.md](KE_HOACH.md).

## 1. Kết luận hiện có

**Có thể huấn luyện bằng Focal và tính BCE/log loss để so sánh chất lượng điểm xác suất với mô hình học bằng BCE.** Phép đo này không tự động sai vì khác loss huấn luyện. Tuy nhiên, BCE thấp hơn không tự động có nghĩa ít lỗi PAD hơn. Cần phân biệt tính hợp lệ của phép đo và mức phù hợp của tiêu chí lựa chọn với câu hỏi nghiên cứu.

Trong dự án, mục tiêu ứng dụng là phân biệt live/attack ở cấp video. Khi các chỉ số PAD validation hòa nhau, BCE được dùng để chọn một ứng viên theo quy tắc cũ. Điều đó chưa chứng minh ứng viên có ACER tốt hơn, chưa chứng minh E4 đã được khai thác tốt nhất và cũng chưa chứng minh E4 chắc chắn bị thiệt. Cần phép thử mới nếu muốn xác định ảnh hưởng của tiêu chí.

Chọn checkpoint trong mỗi cấu hình và chọn cấu hình đi tiếp là **hai bước nối tiếp trong cùng quy trình lựa chọn**. Không được chỉ sửa bước cuối rồi coi ảnh hưởng của bước trước đã được giải quyết.

## 2. EXP-00 — Nguồn đã đối chiếu

| Nguồn | Phần liên quan | Điều nguồn hỗ trợ | Giới hạn khi áp dụng |
| --- | --- | --- | --- |
| [Terven và cộng sự, Loss Functions and Metrics in Deep Learning, v3](https://arxiv.org/html/2307.02694v3) | Mục 2; mục BCE; mục Focal | Phân biệt loss tối ưu và thước đo đánh giá; mô tả cơ chế Focal | Bài tổng quan không trực tiếp chứng minh quy tắc chọn của DeepFace-PAD công bằng hoặc sai |
| [Lin và cộng sự, Focal Loss for Dense Object Detection](https://arxiv.org/html/1708.02002) | Mục 3.1–3.2 | Alpha là trọng số lớp; gamma điều chỉnh giảm đóng góp mẫu dễ; gamma=2 là kết quả thực nghiệm trong bài gốc | Kết quả RetinaNet không chứng minh alpha=0,25/gamma=2 tối ưu cho CASIA |
| [Charoenphakdee và cộng sự, On Focal Loss for Class-Posterior Probability Estimation](https://arxiv.org/html/2011.09172) | Mục 3–4 | Focal chuẩn có thể phù hợp cho quyết định phân loại nhưng với gamma dương không phải loss xác suất strictly proper | Không áp dụng nguyên kết luận về ngưỡng tối ưu cho E4 có alpha hai lớp khác nhau và loss độ sâu |
| [Mukhoti và cộng sự, Calibrating Deep Neural Networks using Focal Loss, NeurIPS 2020](https://proceedings.neurips.cc/paper/2020/file/aeb7b30ef1d024a76f21a1d40e30c302-Paper.pdf) | Phân tích NLL, calibration và thực nghiệm | Nghiên cứu có đánh giá mô hình Focal và CE bằng NLL chung; tối ưu CE trên train không bảo đảm điểm xác suất tốt hơn ngoài train | Không chứng minh Focal luôn tốt hơn; các bộ dữ liệu khác CASIA |
| [Trang kết quả của nhóm tác giả Mukhoti](https://torrvision.com/focal_calibration/) | “How does focal loss fare on NLL overfitting?”, hình 3 | Minh họa trực tiếp việc dùng cùng NLL để đánh giá mô hình học bằng CE và Focal | Đây là diễn giải thực nghiệm của tác giả, không là bảo đảm phổ quát |
| [scikit-learn, Metrics and scoring](https://scikit-learn.org/stable/modules/model_evaluation.html) | “Which scoring function should I use?”, “Log loss”, “Brier score loss” | Chọn phép đo theo mục tiêu dự đoán; log loss đánh giá đầu ra xác suất | BCE/Brier không phải phép đo calibration thuần túy hoặc thay thế mặc nhiên cho ACER |
| [scikit-learn, Cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html) | Mục grouped data | Mẫu theo cùng người có phụ thuộc; đánh giá theo nhóm người phù hợp hơn chia ngẫu nhiên frame | Bốn người validation vẫn chỉ có bốn nhóm người; 960 frame không thành 960 quan sát độc lập |

Nguồn được đọc để trả lời câu hỏi cụ thể. Chưa thực hiện một tổng quan hệ thống toàn bộ tài liệu BCE/Focal.

## 3. Bản chất của BCE và Focal

### 3.1. Mục tiêu cùng bài toán; cách phân bổ đóng góp khác nhau

Với y=1 là live, đặt p=sigmoid(logit). Khi y=1, p_t=p; khi y=0, p_t=1-p. p_t là điểm dành cho nhãn đúng của mẫu; nó được tính từ dự đoán, không phải siêu tham số do người dùng đặt.

Trên một mẫu:

\[
L_{BCE}=-\log p_t,\qquad
L_{Focal}=\alpha_t(1-p_t)^\gamma(-\log p_t).
\]

Ở alpha_t dương, cả hai khuyến khích p_t tăng. Focal không nên được gọi đơn giản là “gắt gao hơn”: giá trị loss trên một mẫu có thể nhỏ hơn BCE, và gradient còn có đạo hàm của hệ số phụ thuộc p_t. Đặc điểm chính là giảm đóng góp tương đối của mẫu dễ so với mẫu khó.

Nếu alpha_t trong [0,1], gamma không âm và cùng dự đoán/cùng cách tổng hợp, Focal không lớn hơn BCE. Không dùng bất đẳng thức này để xếp hạng BCE(E3) với Focal(E4). Khi gamma=0, thành phần điều biến bằng 1; nếu alpha hai lớp vẫn khác nhau, kết quả là BCE có trọng số lớp.

### 3.2. Alpha, gamma và lambda

- Alpha là siêu tham số đặt trong config. Code hiện tại gán live=0,25 và attack=0,75. Nó không tăng trọng số live thiểu số.
- Gamma là siêu tham số, hiện bằng 2. Không có kết quả khảo sát gamma trong nguồn Lượt 5 đã kiểm. Chưa có cơ sở nói giá trị này tối ưu cho dự án.
- P_t được suy ra từ sigmoid nên nằm trong khoảng 0–1. Nó không được chọn như alpha/gamma.
- Lambda_cls=1 ở hai nhánh không bảo đảm cùng đóng góp phân loại vào loss tổng hoặc cùng cường độ gradient.

Giả thuyết alpha làm tăng lỗi từ chối live có cơ sở để kiểm tra, nhưng chưa được chứng minh. Thay alpha cần thí nghiệm kiểm soát, vì threshold, score, depth objective và khả năng tổng quát hóa cùng ảnh hưởng quyết định.

### 3.3. Vì sao BCE vẫn là phép đánh giá xác suất hợp lệ?

Phân tích toán học sau đây xét riêng bài toán nhị phân, chưa bao gồm loss độ sâu. Gọi eta là xác suất thật của live tại một đầu vào, q là xác suất mô hình báo. BCE kỳ vọng có dạng:

\[
R(q)=-\eta\log q-(1-\eta)\log(1-q),\qquad
R'(q)=\frac{q-\eta}{q(1-q)}.
\]

Với 0<eta<1, điểm tối ưu là q=eta. Phép đánh giá không cần biết q được tạo bởi mô hình học loss nào. Nó đo chất lượng dự đoán xác suất theo phân bố và trọng số đã dùng.

Điều này khác với việc một mẫu train có nhãn cứng 0/1 được phạt ít hơn khi dự đoán tiến gần đúng nhãn. Tối ưu BCE trên tập train hữu hạn không bảo đảm mô hình ước lượng đúng xác suất cho người chưa thấy.

Alpha cũng làm thay đổi mục tiêu xác suất. Chỉ trong trường hợp gamma=0 và xét riêng phân loại, BCE có trọng số alpha có điểm tối ưu:

\[
q^*=\frac{\alpha\eta}{\alpha\eta+(1-\alpha)(1-\eta)}.
\]

Vì vậy, không mặc định mọi đầu ra sigmoid từ loss có trọng số đều là xác suất live đã được hiệu chỉnh cho phân bố gốc. Không dùng công thức gamma=0 này để suy ra trực tiếp nghiệm của E4 gamma=2.

### 3.4. “Công bằng” phải gắn với mục tiêu

| Câu hỏi | Đánh giá phù hợp | Kết luận không được suy thêm |
| --- | --- | --- |
| Mô hình nào cho điểm xác suất tốt hơn theo phân bố đã xác định? | Cùng BCE/log loss hoặc Brier; cùng trọng số và đơn vị | Không tự suy ra mô hình đó có ACER thấp hơn |
| Mô hình nào phân biệt live/attack tốt hơn trong PAD? | Cùng protocol video, chọn ngưỡng từ dữ liệu lựa chọn, công bố APCER/BPCER/ACER và EER/AUC | Nếu hòa các chỉ số đã chốt, không tạo một chiến thắng về PAD từ BCE thấp hơn |
| Focal có tốt hơn BCE dưới cùng điều kiện? | Cùng lịch, dữ liệu, initializer hợp lệ, seed, ngân sách và quy tắc lựa chọn; báo độ nhạy tiêu chí | Không quy toàn bộ chênh lệch E3–E4 cho loss khi lịch khác nhau |

Không có tiêu chí duy nhất bảo đảm công bằng cho mọi mục tiêu. Với mục tiêu PAD, đề xuất ở EXP-02 là lấy chỉ số PAD làm chính và giữ hòa khi bằng nhau; đề xuất này chưa thay quy tắc lịch sử.

## 4. EXP-01 — Chuỗi lựa chọn thực tế

Nguồn: [train.py](../../../src/deepface_pad/train.py), [thiết kế Lượt 5](../../../reports/ROUND_5_CASIA_RUNBOOK.md), [validation Lượt 5](../../../reports/ROUND_5_FULL_VALIDATION_2026-10-16.md), [bản khóa](../../../artifacts/round5-full-audit-20261016/comparison_freeze.json), [round6.py](../../../src/deepface_pad/round6.py).

1. Trong từng epoch, trọng số được cập nhật trên train bằng objective của stage.
2. Cuối epoch head/joint, tính BCE frame validation. Lưu đè bản best của stage khi BCE giảm. Không có backward trên validation.
3. Epoch tiếp theo chạy từ trạng thái trọng số hiện tại trong bộ nhớ. Không nạp best sau từng epoch. Không thấy code lưu file last.ckpt.
4. Cuối stage, nạp best của stage; stage sau bắt đầu từ đó với optimizer được tạo lại.
5. Sau joint cuối, lấy best joint làm đại diện cho mỗi cấu hình. Chọn threshold và tính chỉ số video validation.
6. Chọn giữa E3/E3b/E4 theo ACER tăng dần, EER tăng dần, AUC giảm dần, BCE tăng dần. E2 không nằm trong ba ứng viên mới này.
7. Lượt 6 chạy E1/E3 ở seed 43/44/45. E3 mỗi seed khởi tạo từ E1 của chính seed đó. Checkpoint E3 seed 42 không được dùng lại làm mô hình của cả ba seed.

Hai cấp lựa chọn có liên hệ: thay tiêu chí checkpoint có thể đổi ứng viên ở bước so cấu hình. Tuy nhiên, chọn cấu hình cho Lượt 6 khác với mang nguyên trọng số seed 42 sang các seed khác.

Việc dùng BCE ở checkpoint không phụ thuộc ACER đang hòa hay không. BCE chỉ đóng vai trò phân định sau khi hòa ACER/EER/AUC ở bước chọn cấu hình. Bản bàn giao cũ đã trộn hai điều kiện này tại mục 4.4.C; bản cập nhật đã sửa.

## 5. EXP-01 — Số liệu validation tính lại

Nguồn trực tiếp: val_frame_scores.csv và val_scores.csv trong ba run thuộc [round5-full-audit-20261016](../../../artifacts/round5-full-audit-20261016/). Hash từng tệp và công thức được lưu tại [MINH_CHUNG_VALIDATION.json](MINH_CHUNG_VALIDATION.json).

Phép tính dùng log tự nhiên, đọc score đã lưu, giới hạn p trong [10^-15, 1-10^-15]. BCE trung bình hai lớp = (BCE live + BCE attack)/2. Brier nhị phân = trung bình (p-y)^2. Focal chung dùng alpha_live=0,25, alpha_attack=0,75, gamma=2 cho cả ba ứng viên. Đây không phải so BCE của một nhánh với Focal của nhánh khác.

### 5.1. Trên 960 frame của checkpoint đã chọn

| Chỉ số | E3 | E3b | E4 |
| --- | ---: | ---: | ---: |
| BCE chung | 0,01090196 | 0,01456618 | 0,08738544 |
| BCE riêng live, 240 frame | 0,02603751 | 0,03669479 | 0,21618661 |
| BCE riêng attack, 720 frame | 0,00585678 | 0,00718998 | 0,04445171 |
| BCE trung bình hai lớp | 0,01594714 | 0,02194238 | 0,13031916 |
| Brier nhị phân | 0,00169877 | 0,00285466 | 0,01785928 |
| Cùng công thức Focal | 0,00023830 | 0,00052346 | 0,00409301 |

### 5.2. Trên 48 video, mỗi video trung bình 20 frame

| Chỉ số | E3 | E3b | E4 |
| --- | ---: | ---: | ---: |
| ACER tại threshold validation đã lưu (%) | 0 | 0 | 0 |
| EER (%) | 0 | 0 | 0 |
| AUC | 1 | 1 | 1 |
| BCE video | 0,01013272 | 0,01343622 | 0,08415400 |
| BCE video trung bình hai lớp | 0,01452629 | 0,02005219 | 0,12390152 |
| Brier video | 0,00078176 | 0,00160040 | 0,01659325 |

**Diễn giải:** Trong đúng ba checkpoint đã được chọn bằng BCE, thứ tự các chỉ số điểm ở trên không đảo khi đổi sang trung bình hai lớp, Brier hoặc cùng Focal. Như vậy, chưa có bằng chứng rằng chỉ cần đổi tên hàm đánh giá cuối là E4 thắng. Cả ba vẫn hòa theo các chỉ số PAD video đã nêu.

**Giới hạn:** Đây là những checkpoint đã qua lựa chọn bằng BCE. Phân tích không loại trừ việc một checkpoint E4 khác tốt hơn theo tiêu chí PAD. Không sử dụng các chỉ số bổ sung vừa tính để lựa chọn lại ứng viên lịch sử. BCE/Brier thấp hơn ở các điểm này không chứng minh calibration tốt hơn một cách riêng biệt.

### 5.3. Khác biệt thời điểm lựa chọn trong E4

| Quy tắc xét từ train_log.csv của E4 | Epoch trong joint | Giá trị |
| --- | ---: | ---: |
| BCE validation thấp nhất | 6 | 0,0873854375 |
| Tổng objective validation thấp nhất: depth + Focal | 3 | 0,0223781547 |

Ở epoch 3, BCE là 0,0881865043. Ở epoch 6, tổng objective là 0,0225270261. Đây là hai đại lượng khác nhau; không so giá trị tuyệt đối giữa chúng. Tổng objective thấp nhất không có nghĩa thành phần Focal riêng thấp nhất, cũng không có nghĩa ACER thấp nhất.

Kiểm kê tên file ở cấp gốc ba run trên G:/My Drive/face-pad/runs cho thấy:

- E3: best_stage_01_joint.ckpt và best.ckpt.
- E3b/E4: best_stage_01_depth.ckpt, best_stage_02_head.ckpt, best_stage_03_joint.ckpt và best.ckpt.
- Chưa tìm thấy file từng epoch hoặc last.ckpt trong phạm vi cấp gốc đã kiểm. Không khẳng định mọi nơi lưu khác đều không có.

Code chỉ lưu best theo criterion nên không thể mặc định phục hồi trọng số epoch 3 từ train_log.csv. Các checkpoint cũng không đủ trạng thái optimizer/scheduler/RNG để coi huấn luyện lại từ một checkpoint là tái lập chính xác quỹ đạo cũ. EXP-04 phải là phép thử mới nếu không tìm được bản lưu đủ.

## 6. EXP-01 — Phân bố train/validation và câu hỏi (*)

Nguồn đếm: [manifest](../../../data/manifests/casia_fasd_debug.csv).

| Tập | Người | Video live | Video attack | Tổng video | Frame |
| --- | ---: | ---: | ---: | ---: | ---: |
| Train | 16 | 48 | 144 | 192 | 3.840 |
| Validation | 4 | 12 | 36 | 48 | 960 |
| Test | 30 | 90 | 270 | 360 | 7.200 |

Train và validation cùng tỷ lệ live:attack là 1:3. Không có căn cứ từ bảng này để nói chênh lệch tỷ lệ lớp giữa hai tập gây BCE của E4 cao hơn. Cùng tỷ lệ không chứng minh cùng độ khó, ánh sáng, diện mạo hoặc phân bố có điều kiện theo nhãn. Bốn người validation có thể chưa phản ánh đầy đủ người mới; cần phân tích hoặc phép thử nhóm người khác để kiểm chứng.

Với tập có tỷ lệ này, BCE trung bình mẫu = 0,25 × BCE live + 0,75 × BCE attack. ACER = 0,5 × BPCER + 0,5 × APCER. Hai phép tổng hợp thể hiện hai cách đặt trọng số khác nhau. Không rò rỉ dữ liệu chưa đủ bảo đảm tiêu chí phù hợp mục tiêu hoặc khả năng đại diện của validation.

“Tối ưu trên train, đo trên validation” có nghĩa: gradient dùng dữ liệu train để thay trọng số; validation dùng người khác để xem quy tắc đã học có áp dụng được không. Việc chọn checkpoint nhiều lần vẫn dùng thông tin validation cho lựa chọn, dù không backward trên nó; điểm validation sau lựa chọn không là đánh giá cuối độc lập.

Ví dụ giả định, không phải kết quả dự án: mô hình BCE có BCE train 0,01 và BCE validation 0,30; mô hình Focal có BCE train tính lại 0,05 và BCE validation 0,20. Điều này có thể xảy ra nếu mô hình BCE khớp train mạnh hơn nhưng áp dụng kém hơn cho người mới. Cả bốn số trong ví dụ đều là BCE; không so raw training BCE với raw training Focal.

Hai tập không có mẫu chung được viết là giao của hai tập rỗng, không phải hợp rỗng. Với video, cần kiểm thêm nhóm người/video và quy trình sinh target/tiền xử lý; không chỉ tên sample khác nhau. Phiên này đếm lại manifest, không chạy lại một kiểm tra trùng ảnh bằng nội dung.

## 7. Những chỗ cần sửa trong diễn giải và bàn giao

| Cách hiểu hoặc diễn đạt trước | Điều chỉnh |
| --- | --- |
| Focal “gắt gao hơn” BCE | Focal giảm đóng góp tương đối của mẫu dễ; không có nghĩa mọi mẫu bị phạt lớn hơn hoặc gradient luôn lớn hơn |
| Alpha 0,25 gây lỗi live đã thấy | Là giả thuyết cần kiểm; chưa là kết luận nhân quả. E4 không phải mô hình webcam đã đo |
| Cùng BCE nên chắc chắn công bằng | Cùng phép đo là điều kiện so sánh; cần thêm mục tiêu, trọng số, đơn vị, dữ liệu và ngân sách phù hợp |
| Dùng BCE cho mô hình Focal chắc chắn sai | Không đúng với đánh giá xác suất; chưa đủ cho kết luận hơn về PAD |
| Checkpoint dùng BCE vì ACER hòa | Checkpoint head/joint luôn dùng BCE trong thiết kế cũ. Điều kiện hòa thuộc bước chọn cấu hình |
| Epoch sau tiếp tục từ file last.ckpt | Tiếp tục từ trọng số hiện tại trong bộ nhớ; code không lưu last.ckpt |
| Hai cấp lựa chọn là hai vấn đề không liên quan | Là hai bước nối tiếp; phải xem ảnh hưởng tổng thể |
| Chọn cấu hình Lượt 6 là mang checkpoint seed 42 sang Lượt 6 | Lượt 6 huấn luyện lại E1/E3 ở các seed mới |
| Lấy joint là đủ để gọi so sánh công bằng nhất | Cần kiểm cả lịch trước joint, số cập nhật, optimizer reset, initializer và loss scale |
| Giữ kết quả cũ và ghi giới hạn là đã giải quyết ảnh hưởng checkpoint | Chỉ giải quyết cách trình bày. Câu hỏi thực nghiệm vẫn mở nếu chưa làm phép thử phù hợp |

Các tham chiếu gốc của bàn giao được giữ. Phương án chưa chốt được ghi là đề xuất, không là quyết định đã duyệt.

## 8. Trạng thái quyết định và kết quả cần bổ sung

| Mã | Kết quả đã có | Phần còn chờ |
| --- | --- | --- |
| EXP-00 | Đã đối chiếu nguồn và kết luận có điều kiện | Người dùng xác định ưu tiên PAD hay xác suất trong EXP-02 |
| EXP-01 | Đã tính lại CSV validation và kiểm kê checkpoint cấp gốc | Không thể chấm epoch chưa có trọng số/score chỉ từ log |
| EXP-02 | Có hai phạm vi và đề xuất protocol | Người dùng chọn có làm phép thử mới và phạm vi dữ liệu |
| EXP-03–06 | Chưa có kết quả mới | Chưa sửa training, chưa có notebook mới, chưa dùng GPU |
| EXP-07 | Kế thừa giới hạn CPU/webcam đã ghi | Chưa đo print/reset mới; chưa chứng minh nguyên nhân lỗi live |
| EXP-08 | Đã sửa tài liệu bàn giao này | Chưa đồng bộ Word, chưa thay kết luận báo cáo cuối kỳ |

Thứ tự đề xuất: đọc EXP-00/01 → quyết định EXP-02 → triển khai từng mã phù hợp. Không chọn lại E4 từ test 4,44% để gọi đó là lựa chọn validation mới.

## 9. Kiểm tra tài liệu và dữ liệu tính lại

Đầu ra MINH_CHUNG_VALIDATION.json ghi công thức, số lượng và SHA-256 của các CSV/JSON nguồn. Số BCE tính lại từ CSV có sai khác nhỏ với BCE từ logits trong log do độ chính xác và cách tính số; không ghi đè giá trị đã khóa.

Đã kiểm: giữ đủ 43 đích tham chiếu cũ; 73 lượt liên kết cục bộ trong ba Markdown hợp lệ; 12 hash nguồn khớp; 144 phép gộp video từ 20 frame khớp; phân bố lớp, BCE theo lớp và các cực tiểu epoch khớp. ACER=0 và AUC=1 được đối chiếu lại từ score video đã lưu. Không dùng kiểm tra tài liệu để tuyên bố huấn luyện hoặc thí nghiệm mới đã đạt.

## 10. Phạm vi và nhánh đề xuất ngày 31/10/2026

- Mục tiêu được làm rõ: ưu tiên khả năng phân biệt bona fide/attack; đo cả attack bị cho qua và người thật bị từ chối. Chưa chốt mức ưu tiên định lượng giữa hai lỗi.
- E0/E1 và kết quả lịch sử là mốc đã khóa. Các nhánh mới không ghi đè chúng. Backbone bản sao từ E1 trong E3/E4 vẫn có thể được huấn luyện theo thiết kế.
- Báo cáo cuối kỳ và paper phải thống nhất sự thật phương pháp, số liệu và phạm vi kết luận. Chưa dựng lại hai tài liệu.
- Kế hoạch đã thêm đề xuất 5.1 theo ACER, 5.2 theo AUC, 5.3 theo ràng buộc APCER; 6.x kiểm tra theo seed với cùng quy tắc tương ứng. Chưa nhánh nào được đăng ký chạy.
- BCE, CE hai lớp và Bernoulli NLL có thể tương đương về giá trị khi cùng dự đoán, nhãn cứng, trọng số và phép tổng hợp. Không tạo ba nhánh chỉ bằng đổi tên các đại lượng tương đương này. API NLLLoss yêu cầu log-probabilities; không thay trực tiếp BCEWithLogitsLoss bằng NLLLoss trên cùng tensor mà không xử lý đầu vào đúng.
- Calibration là câu hỏi riêng với lỗi PAD. Không bổ sung bước hiệu chỉnh xác suất chỉ vì muốn giảm lỗi phân loại; nếu thực hiện phải có thiết kế và dữ liệu phù hợp.
- Ràng buộc giữ E1 làm mốc khiến phương án đổi các người E1 đã học sang fold validation không hợp lệ cho kết luận không trùng người của toàn pipeline. Kế hoạch đã loại phương án đó khỏi phạm vi hiện tại.

Đây là cập nhật thiết kế và phạm vi, không phải kết quả huấn luyện. Cần người dùng chọn nhánh, xử lý head stage và quy tắc dữ liệu trước EXP-03.
