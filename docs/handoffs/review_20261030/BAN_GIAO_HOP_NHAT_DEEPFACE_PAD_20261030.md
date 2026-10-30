# BÀN GIAO TỔNG HỢP PHƯƠNG PHÁP, MINH CHỨNG VÀ VẤN ĐỀ CẦN XỬ LÝ — DEEPFACE-PAD

Ngày cập nhật: 30/10/2026.

Tài liệu tổng hợp cơ sở kỹ thuật và các vấn đề cần xử lý trước khi chốt báo cáo.
Các minh chứng hiện có chưa tạo căn cứ để hủy toàn bộ kết quả Lượt 1–7.
Kết luận này chỉ áp dụng cho phạm vi đã được kiểm tra.
Các giới hạn về lựa chọn mô hình, dữ liệu và webcam vẫn cần được trình bày rõ.

Kế hoạch xử lý theo mã EXP và kết quả đối chiếu mới nằm tại
[kế hoạch so sánh công bằng](../../reviews/fair_comparison_20261030/KE_HOACH.md) và
[kết quả nghiên cứu BCE–Focal](../../reviews/fair_comparison_20261030/KET_QUA.md).
Phép thử mới và tiêu chí mới trong kế hoạch còn chờ người dùng quyết định.

## 1. Thuật ngữ


| Thuật ngữ | Nghĩa trong tệp này |
| --- | --- |
| Tập huấn luyện, train | Dữ liệu dùng để cập nhật trọng số. |
| Tập kiểm định, validation | Dữ liệu dùng để chọn trọng số, ngưỡng và cấu hình. |
| Tập kiểm tra, test | Dữ liệu dùng để đánh giá sau khi cố định lựa chọn. |
| Checkpoint | Trọng số được lưu tại một thời điểm huấn luyện. |
| Backbone | Mạng sinh bản đồ độ sâu. |
| Head | Bộ phân loại nhận bản đồ độ sâu. |
| Joint | Giai đoạn cập nhật đồng thời backbone và head. |
| Seed | Giá trị khởi tạo bộ sinh số ngẫu nhiên. |
| APCER | Tỷ lệ tấn công bị nhận thành người thật. |
| BPCER | Tỷ lệ người thật bị từ chối. |
| ACER | Trung bình APCER và BPCER theo phép tổng hợp được công bố. |
| EER | Tỷ lệ lỗi tại điểm hai loại lỗi gần cân bằng. |
| AUC | Chỉ số đánh giá khả năng xếp hạng phân biệt hai lớp. |


## 2. Tổng quan các vấn đề kỹ thuật

| Mã vấn đề | Nội dung cần xử lý | Điều đã biết và phần còn thiếu | Mã công việc |
| --- | --- | --- | --- |
| V01 | Chọn checkpoint rồi chọn cấu hình theo mục tiêu phù hợp | BCE ảnh hưởng hai bước nối tiếp. Chưa đo ảnh hưởng của quy tắc chọn khác. | EXP-00–04 |
| V02 | Focal, alpha, gamma và trọng số loss | Alpha hiện tại không ưu tiên live; chưa chứng minh nó gây lỗi live hoặc đã tối ưu gamma. | EXP-00, EXP-01, EXP-05 |
| V03 | Diễn giải đúng chuỗi huấn luyện và lựa chọn | Phải phân biệt cập nhật, lưu/nạp checkpoint, ngưỡng và cấu hình; Lượt 6 train lại theo seed. | EXP-01–04 |
| V04 | Bốn người validation | Chưa có lý do được ghi nhận cho đúng bốn mã; chưa kiểm độ nhạy theo nhóm người. | EXP-02, EXP-05 |
| V05 | Protocol và lịch sử xem test | Intra-dataset/intra-type và cách chia 16/4/30 là hai mô tả riêng; test đã xem không trở lại thành dữ liệu chưa từng được dùng. | EXP-02, EXP-08 |
| V06 | APCER gộp, ACER và tỷ lệ lớp | BCE mẫu cho hai lớp trọng số 1:3; ACER cho hai tỷ lệ lỗi trọng số 1:1. Phạm vi ISO cần được giới hạn. | EXP-01, EXP-02, EXP-08 |
| V07 | Phạm vi xác minh HR_1 | Đã kiểm 1.000 frame HR_1 trong manifest; chưa kiểm toàn bộ archive Kaggle. | EXP-02, EXP-08 |
| V08 | Tác dụng head, lịch huấn luyện và seed | Chưa cô lập mọi yếu tố và chưa chứng minh cải thiện ổn định. | EXP-02, EXP-04–06 |
| V09 | CPU và webcam | CPU chỉ minh họa; còn thiếu print, reset đủ cửa sổ và kiểm nguyên nhân lỗi live. | EXP-07, EXP-08 |

### 2.1. Các chủ đề và nguồn đã đối chiếu

Các mã AUD dưới đây chỉ nhóm nội dung kỹ thuật. Chúng không thay thế trạng thái V01–V09.

| Mã kiểm toán | Vấn đề kỹ thuật | Trạng thái xác minh | Cơ chế xử lý trong hệ thống | Minh chứng mã nguồn và dữ liệu thực nghiệm |
| :---: | :--- | :---: | :--- | :--- |
| **AUD-01** | **Các frame `HR_1` dưới thư mục `spoof/` trong dữ liệu đã dùng** | **Nhãn manifest đã kiểm; phạm vi V07 còn giới hạn** | Hàm `parse_frame_path` cho phép ngoại lệ đường dẫn với mã `HR_1`. Hàm `build_manifest` gán nhãn trực tiếp từ từ điển `VIDEO_METADATA["HR_1"] = (1, "live", "high")`, không đọc nhãn theo tên thư mục. | `src/deepface_pad/casia_fasd.py` (dòng 14, 40–58, 110); `data/manifests/casia_fasd_debug.csv` (1.000 khung hình `HR_1` thuộc 50 video đều mang `label=1`). |
| **AUD-02** | **Giao thức chia tập 16/4/30 so với bài báo gốc CASIA-FASD (20/30)** | **Đã kiểm cách chia; V04/V05 còn mở** | Dự án tách 4 đối tượng `{4, 9, 14, 19}` từ nhánh Train làm tập Validation. Nhánh Test giữ 30 đối tượng gốc. Kịch bản là **Intra-dataset, Intra-type**; chưa giải thích lý do chọn đúng bốn mã hoặc độ nhạy cách chia. | `src/deepface_pad/casia_fasd.py` (dòng 78, 87–108); `data/manifests/casia_fasd_debug.csv` (Train: 3.840, Val: 960, Test: 7.200 khung hình; tổng 12.000 khung hình). |
| **AUD-03** | **Chuẩn hóa giả độ sâu, cách tính điểm suy luận** | **Đã xác minh** | Lớp `PadDataset` chuẩn hóa độ sâu về đoạn $[0, 1]$ qua phép chia cực đại. Mô hình E1 lấy trung bình bản đồ độ sâu; mô hình E2–E4 dùng xác suất $\sigma(\text{logit})$. | `src/deepface_pad/data.py` (dòng 120–125); `src/deepface_pad/train.py` (dòng 117); `src/deepface_pad/metrics.py` (dòng 36); `ANALYSIS_01_ROUNDS1_3_BASELINE_VA_PSEUDO_DEPTH_SUPERVISION.md` (dòng 63). |
| **AUD-04** | **Khác biệt toán học giữa DepthNet (2018), FAS-TD (2019) và CDCN (2020)** | **Đã phân định rõ** | DepthNet dùng tích chập 2D chuẩn. FAS-TD thêm mô-đun truyền thông tin không-thời gian giữa các khung hình. CDCN thay tích chập chuẩn bằng tích chập sai phân tâm (CDC, $\theta=0.7$) trên từng khung hình độc lập. | `src/deepface_pad/models/` (`OfficialCDCN`, `OfficialCDCNWithDepthHead`); `src/deepface_pad/losses.py` (dòng 41–66, 88–98). |
| **AUD-05** | **BCE, Focal và chuỗi chọn checkpoint/cấu hình** | **Đã kiểm quy tắc; chưa đo ảnh hưởng của tiêu chí khác** | Head/joint luôn chọn checkpoint bằng BCE frame validation. Sau đó chọn cấu hình bằng ACER → EER → AUC → BCE; ba chỉ số đầu hòa nên BCE quyết định. BCE là phép đo điểm xác suất hợp lệ nhưng chưa đủ để tuyên bố ưu thế PAD khi các chỉ số PAD hòa. Alpha live=0,25 không ưu tiên live; chưa chứng minh nguyên nhân lỗi. | `src/deepface_pad/losses.py` (dòng 69–80); `src/deepface_pad/train.py` (dòng 97–110, 227–241); `configs/casia_e4_staged_focal.yaml`. |
| **AUD-06** | **Cơ chế "Step" trong mã huấn luyện và yếu tố gây nhiễu E1 – E3** | **Đã xác minh mã nguồn** | Hệ thống cập nhật trọng số theo từng batch (`optimizer.step()`), ghi log theo `epoch` và không lưu `global_step`. Lệnh `scheduler.step()` gọi theo epoch nên `step_size: 500` ở E1 không bao giờ kích hoạt trong 30 epochs. | `src/deepface_pad/train.py` (dòng 210–259); `configs/casia_e1_cdcn_official.yaml` (dòng 19, 24); `configs/casia_e3_joint_bce.yaml` (dòng 26–30). |
| **AUD-07** | **Chỉ số APCER gộp, lặp lại đa hạt giống (Seeds 43–45) và sai số CPU vs CUDA** | **Đã xác minh số học** | Hàm `error_rates` tính APCER gộp trung bình trên 270 video giả mạo thay vì lấy kịch bản xấu nhất theo ISO/IEC 30107-3. Ba seed 43, 44, 45 đo biến thiên theo khởi tạo trên cùng 360 video Test; chưa chứng minh cải thiện ổn định. Suy luận CPU lệch tối đa $0.000684$ so với CUDA. | `src/deepface_pad/metrics.py` (dòng 46–58); `reports/ROUND_6_RESULTS_2026-10-22.md`; `docs/handoffs/CURRENT.md` (dòng 33–57). |
| **AUD-08** | **Đường ống Webcam thời gian thực, Median Gate và lỗi từ chối người thật** | **Đã đo thực nghiệm** | Hệ thống dùng bộ phát hiện YuNet, cửa sổ trung vị 5 khung hình, khoảng chờ tối đa $5.0\text{ s}$ và $\text{IoU} \ge 0.4$. Webcam chặn đúng tấn công phát lại (`replay-02`) nhưng từ chối nhầm người thật (`live-03`) với nguyên nhân chưa được xác định đầy đủ. | `src/deepface_pad/webcam.py` (dòng 35–86); `reports/round7/WEBCAM_RESULTS.json`; `docs/handoffs/CURRENT.md` (dòng 60–89). |

---


## 3. Các vấn đề cần giải quyết

Các mục “Việc cần làm” là đề xuất xử lý, không phải phương án đã được người dùng duyệt.
Sửa diễn giải không đồng nghĩa đã kiểm chứng ảnh hưởng bằng thực nghiệm.
Theo dõi quyết định và kết quả theo mã EXP trong kế hoạch liên kết ở đầu tệp.

### V01. Kiểm tra chuỗi chọn checkpoint và cấu hình BCE–Focal

**Vấn đề:** Cần xác định tiêu chí phù hợp với mục tiêu PAD ở cả hai bước nối tiếp:
chọn checkpoint đại diện từng cấu hình, rồi chọn cấu hình đi tiếp.
BCE chung đo chất lượng điểm xác suất, nhưng BCE thấp hơn không chứng minh ACER tốt hơn.
Chưa đủ bằng chứng gọi quy trình hiện tại là sai chỉ vì E4 học bằng Focal.
Chưa kiểm ảnh hưởng của một quy tắc lựa chọn khác theo mục tiêu PAD.

**Minh chứng:**

- E4 huấn luyện bằng Focal với alpha bằng 0,25 và gamma bằng 2.
- Cấu hình đặt `selection_metric: classification_bce`.
- Hàm `_selection_loss` trả BCE cho giai đoạn head và joint.
- `val_loss` và `val_selection_loss` lưu hai đại lượng khác nhau.
- Ở joint, `val_loss` gồm loss độ sâu và Focal.
- Ở joint, `val_selection_loss` là BCE phân loại trên frame validation.
- Chọn checkpoint bằng BCE diễn ra ngay cả khi chưa xét ACER.
- Chọn giữa E3/E3b/E4 dùng ACER → EER → AUC → BCE trên validation.
- Ba chỉ số PAD đầu hòa; BCE quyết định E3 đi tiếp theo quy tắc cũ.
- E4 có BCE joint thấp nhất ở epoch 6; tổng objective thấp nhất ở epoch 3.
- Tổng objective gồm depth + Focal, không phải Focal riêng hoặc ACER.
- Chưa có score từng epoch để kết luận checkpoint epoch 3 tốt hơn về PAD.

Nguồn: [cấu hình E4](../../../configs/casia_e4_staged_focal.yaml); [code huấn luyện và chọn checkpoint](../../../src/deepface_pad/train.py); [thiết kế Lượt 5](../../../reports/ROUND_5_CASIA_RUNBOOK.md).

**Phương án đề xuất, chưa chốt:**

1. Đọc kết quả EXP-00/01 để xác định điều dữ liệu hiện có trả lời được.
2. Chọn trong EXP-02: chỉ hoàn tất kiểm toán hay làm phép thử có đối chứng.
3. Nếu làm phép thử mới, chốt dữ liệu, ngân sách, tiêu chí checkpoint và cấu hình trước khi chạy.
4. So BCE–Focal dưới cùng lịch bằng E3b–E4; kiểm cả ảnh hưởng head stage nếu đổi tiêu chí ở đó.
5. Giữ các kết quả lịch sử; không chọn lại từ test rồi gọi là lựa chọn validation.

**Điều kiện hoàn tất:** Có kết luận theo đúng phạm vi đã chọn.
Nếu chỉ sửa báo cáo, câu hỏi thực nghiệm về ảnh hưởng checkpoint vẫn còn mở.
Xem [EXP-00–04 và kết quả](../../reviews/fair_comparison_20261030/KET_QUA.md).

### V02. Sửa diễn giải về Focal, lớp thiểu số và thang đo loss

**Vấn đề:** Focal không tự động ưu tiên lớp live thiểu số.
Giá trị Focal nhỏ hơn không chứng minh mô hình tốt hơn.

**Minh chứng:**

- Code tính `Focal = alpha_t * (1 - p_t)^gamma * BCE`.
- `p_t` là xác suất dành cho nhãn đúng.
- Live có trọng số alpha bằng 0,25.
- Attack có trọng số alpha bằng 0,75.
- Train có 48 video live và 144 video attack.
- Tại cùng `p_t`, hệ số lớp của attack gấp ba hệ số của live.
- Với cùng dự đoán, hệ số nhân nằm trong [0, 1] theo điều kiện đã nêu.
- Điều kiện đó yêu cầu alpha trong [0, 1] và gamma không âm.
- Quan hệ Focal không lớn hơn BCE không dùng để xếp hạng hai mô hình khác nhau.
- Cùng `lambda_cls=1` chưa bảo đảm cùng đóng góp phân loại trong loss tổng.
- Alpha/gamma là siêu tham số; p_t được tính từ dự đoán và nhãn, không phải siêu tham số.
- Gamma=2 là cấu hình đã thử; chưa có khảo sát chứng minh tối ưu cho CASIA.
- Alpha có thể ảnh hưởng lỗi live, nhưng chưa được xác định là nguyên nhân.

Nguồn: [code các hàm mất mát](../../../src/deepface_pad/losses.py); [cấu hình E4](../../../configs/casia_e4_staged_focal.yaml); [manifest CASIA](../../../data/manifests/casia_fasd_debug.csv).
Nguồn phương pháp: [Focal Loss gốc](https://arxiv.org/abs/1708.02002).

**Việc cần làm:**

1. Bỏ nhận định rằng alpha hiện tại cân bằng lớp live.
2. Bỏ phép so trực tiếp giá trị BCE và Focal của hai mô hình.
3. Ghi giới hạn về trọng số phân loại trong loss tổng.
4. Nếu thử alpha khác, lập thí nghiệm mới trước khi chạy.

**Điều kiện hoàn tất:** Kết luận chỉ áp dụng cho cấu hình alpha và gamma đã thử.

### V03. Làm rõ bốn thao tác lựa chọn mô hình

**Vấn đề:** Các thao tác đã bị nhầm lẫn trong quá trình giải thích.
Thứ hạng trên test đã bị dùng nhầm như thứ hạng trên validation.

**Minh chứng:**

| Thao tác | Quy tắc đã thực hiện |
| --- | --- |
| Cập nhật trọng số | Dùng loss trên train theo giai đoạn. |
| Chọn checkpoint joint | Chọn BCE frame validation thấp nhất. |
| Chọn ngưỡng | Chọn ACER video validation thấp nhất. |
| Chọn cấu hình | Xét lần lượt ACER, EER, AUC, rồi BCE trên validation. |

Epoch sau tiếp tục từ trọng số hiện tại trong bộ nhớ; code không lưu file last.ckpt.
Cuối stage mới nạp best của stage để chuyển tiếp.
Hai bước chọn checkpoint và cấu hình thuộc cùng chuỗi lựa chọn.
Lượt 6 huấn luyện lại E1/E3 ở seed 43/44/45, không dùng lại nguyên checkpoint seed 42.

ACER, EER và BCE được ưu tiên theo giá trị thấp hơn.
AUC được ưu tiên theo giá trị cao hơn.
Chỉ xét tiêu chí tiếp theo khi tiêu chí trước bằng nhau.
Quy tắc không đếm số tiêu chí mà mỗi cấu hình thắng.

| Chỉ số, seed 42 | E3 | E3b | E4 |
| --- | ---: | ---: | ---: |
| ACER validation (%) | 0 | 0 | 0 |
| EER validation (%) | 0 | 0 | 0 |
| AUC validation | 1 | 1 | 1 |
| BCE frame validation | 0,010902 | 0,014566 | 0,087385 |
| ACER test (%) | 5,0000 | 5,0000 | 4,4444 |

E3 được chọn bằng validation.
E4 có ACER test thấp hơn E3.
Hai nhận định này không mâu thuẫn.

Nguồn: [kết quả validation Lượt 5](../../../reports/ROUND_5_FULL_VALIDATION_2026-10-16.md); [kết quả test Lượt 5](../../../reports/ROUND_5_TEST_RESULTS_2026-10-16.md); [notebook Lượt 5](../../../notebooks/Face_PAD_Round5_CASIA_E3_E4.ipynb); [bản khóa lựa chọn Lượt 5](../../../artifacts/round5-full-audit-20261016/comparison_freeze.json).

**Việc cần làm:**

1. Gắn tên tập dữ liệu vào mỗi chỉ số.
2. Phân biệt chỉ số frame với chỉ số video.
3. Giải thích quy tắc phân định khi các chỉ số bằng nhau.
4. Ghi rằng ngưỡng tốt nhất trên validation chưa chắc tốt nhất trên test.

**Điều kiện hoàn tất:** Người đọc xác định được dữ liệu và tiêu chí của từng quyết định.

### V04. Giải trình cách chọn bốn người validation

**Vấn đề:** Chưa tìm thấy lý do chọn đúng người 4, 9, 14 và 19.
Chưa đánh giá độ nhạy với các cách chọn người khác.

**Minh chứng:**

- Code đặt cố định bốn mã này từ commit `fdaad5f` ngày 20/09/2026.
- Bốn người chiếm 20% số người trong train gốc.
- Các mã cách nhau năm đơn vị.
- Đặc điểm dãy số chưa chứng minh động cơ lựa chọn.
- Hồ sơ chưa chứng minh đây là lựa chọn ngẫu nhiên hoặc đại diện.
- Bốn người cung cấp 48 video validation.
- Ba ứng viên cùng đạt ACER validation bằng 0.

Nguồn: [code tạo manifest](../../../src/deepface_pad/casia_fasd.py); [tài liệu dữ liệu](../../../data/README.md); [kết quả validation Lượt 5](../../../reports/ROUND_5_FULL_VALIDATION_2026-10-16.md).

**Việc cần làm:**

1. Mô tả đây là lựa chọn cố định của dự án.
2. Nêu giới hạn do chỉ có bốn người validation.
3. Bỏ lý do đại diện nếu không có bằng chứng.
4. Nếu cần đánh giá độ nhạy, đề xuất cách chia khác trong nghiên cứu tiếp theo.

**Điều kiện hoàn tất:** Báo cáo không gán lý do chưa được ghi nhận cho bốn mã người.

### V05. Chuẩn hóa tên protocol và lịch sử sử dụng test

**Vấn đề:** Cụm “phân chia phát triển” làm lẫn cách chia dữ liệu với lịch sử nghiên cứu.

**Minh chứng:**

- Train, validation và test đều thuộc CASIA-FASD.
- Các tập đều có warped photo, cut photo và replay.
- Cách đánh giá hiện tại là intra-dataset, intra-type.
- Train gốc cung cấp 16 người train và 4 người validation.
- Nhánh test của nguồn vẫn cung cấp 30 người test.
- CASIA gốc quy định train/test theo tỷ lệ 20/30 người.
- Nhóm dùng bản frame Kaggle và 20 frame cho mỗi video.
- Hồ sơ cho biết kết quả test đã được xem ở những lượt trước.
- Bản khóa Lượt 5 ghi E3 là ứng viên được chọn bằng validation.

Nguồn: [manifest CASIA](../../../data/manifests/casia_fasd_debug.csv); [tài liệu dữ liệu](../../../data/README.md); [bản khóa lựa chọn Lượt 5](../../../artifacts/round5-full-audit-20261016/comparison_freeze.json); [bàn giao repository](../../../docs/handoffs/CURRENT.md).
Nguồn gốc: [CASIA 2012, mục 4](https://nlpr.ia.ac.cn/2012papers/gjhy/gh69.pdf).

**Việc cần làm:**

1. Dùng tên “intra-dataset, intra-type” để mô tả hai trục protocol.
2. Ghi riêng cách chia người 16/4/30.
3. Ghi riêng việc test đã được quan sát.
4. Phân biệt việc mở lại kết quả với việc dùng kết quả để lựa chọn mô hình.
5. Nếu chọn E4 từ test, ghi rõ nguồn quyết định đó.
6. Nếu cần kết luận xác nhận mới, đề xuất dữ liệu đánh giá độc lập.

**Điều kiện hoàn tất:** Báo cáo không nhận là tái lập nguyên vẹn protocol gốc.
Báo cáo không gọi lựa chọn dựa trên test là lựa chọn bằng validation.

### V06. Làm rõ ACER gộp và mất cân bằng lớp

**Vấn đề:** Công thức ACER chưa đủ để tuyên bố toàn bộ đánh giá tuân thủ ISO.
ACER cũng không cân bằng quá trình huấn luyện.

**Minh chứng:**

- Test có 90 video live và 270 video attack.
- Code tính APCER gộp trên toàn bộ video attack.
- Code tính BPCER riêng trên video live.
- ACER cho hai tỷ lệ đóng góp bằng nhau.
- BCE frame trung bình vẫn phản ánh phân bố lớp 1:3.
- Một số protocol PAD lấy APCER riêng theo công cụ tấn công rồi chọn trường hợp xấu nhất.
- Phép APCER gộp hiện tại chưa tương đương phép tổng hợp đó.

Nguồn: [code chỉ số đánh giá](../../../src/deepface_pad/metrics.py); [manifest CASIA](../../../data/manifests/casia_fasd_debug.csv).
Nguồn đối chiếu: [Tài liệu chuẩn hóa PAD tại NIST](https://www.nist.gov/system/files/documents/2020/09/15/12_buschthieme-ibpc-pad-160504.pdf).

**Việc cần làm:**

1. Ghi rõ APCER được gộp theo các video attack.
2. Trình bày riêng APCER và BPCER bên cạnh ACER.
3. Phân biệt trọng số khi đánh giá với trọng số khi huấn luyện.
4. Bỏ tuyên bố tuân thủ đầy đủ ISO nếu chưa có đánh giá tương ứng.
5. Nếu bổ sung chỉ số theo loại tấn công, giữ nguyên bảng chỉ số đã khóa.

**Điều kiện hoàn tất:** Công thức và phạm vi tổng hợp được mô tả rõ.
Các bảng khác protocol không được xếp hạng trực tiếp.

### V07. Giới hạn tuyên bố về toàn bộ bản phân phối Kaggle

**Vấn đề:** Chưa kiểm lại mọi frame trong toàn bộ archive Kaggle.
Ngoại lệ thư mục HR_1 đã được kiểm trên dữ liệu dự án sử dụng.

**Minh chứng:**

- Manifest dùng 1.000 frame HR_1 thuộc 50 video.
- Cả 1.000 frame đều nằm dưới đường dẫn spoof.
- Cả 1.000 frame đều có label bằng 1 trong manifest.
- Ảnh mẫu có mã `casia_s21_vHR_1_f000069`.
- Mã truy cập Bob/Idiap xác định HR_1 là người thật chất lượng cao.
- Phiên trao đổi chưa kiểm toàn bộ frame ngoài 20 frame được chọn cho mỗi video.

Nguồn: [manifest CASIA](../../../data/manifests/casia_fasd_debug.csv); [code tạo manifest](../../../src/deepface_pad/casia_fasd.py); [ảnh HR_1 đã kiểm](../../../artifacts/round7/figures-attempt03/inputs/test/spoof/s1vHR_1f69.png).
Nguồn độc lập: [Ánh xạ CASIA của Bob/Idiap](https://idiap.ch/software/bob/docs/bob/bob.db.casia_fasd/v2.0.5/_modules/bob/db/casia_fasd.html).

**Việc cần làm:**

1. Giới hạn phát biểu theo bản dữ liệu đã sử dụng.
2. Nếu cần khẳng định toàn bộ archive, kiểm kê archive đúng phiên bản.
3. Giữ nhãn theo mã video trong manifest.

**Điều kiện hoàn tất:** Phạm vi tuyên bố khớp phạm vi đã kiểm.
Không cần hủy kết quả vì tên thư mục đã được pipeline xử lý.

### V08. Giới hạn kết luận về tác dụng của head và chiến lược huấn luyện

**Vấn đề:** Thiết kế hiện tại chưa cô lập mọi yếu tố ảnh hưởng.

**Minh chứng:**

- E3 và E3b cùng có ACER test bằng 5% ở seed 42.
- Chỉ số bằng nhau chưa chứng minh mô hình hoặc nguyên nhân giống nhau.
- Huấn luyện theo giai đoạn gồm đóng băng trọng số, nạp checkpoint và đặt lại bộ tối ưu.
- E1 và E3 còn khác ngân sách huấn luyện và weight decay.
- E3 tốt hơn E1 ở seed 43 và 45.
- E3 kém hơn E1 ở seed 44.
- Ba seed đánh giá trên cùng 360 video.

Nguồn: [thiết kế Lượt 5](../../../reports/ROUND_5_CASIA_RUNBOOK.md); [kết quả test Lượt 5](../../../reports/ROUND_5_TEST_RESULTS_2026-10-16.md); [kết quả Lượt 6](../../../reports/ROUND_6_RESULTS_2026-10-22.md).

**Việc cần làm:**

1. Bỏ kết luận nhân quả chưa được kiểm chứng.
2. Giữ seed 42 riêng khỏi thống kê ba seed mới.
3. Giữ kết quả bất lợi của seed 44.
4. Ghi rằng cải thiện trung bình chưa chứng minh cải thiện ổn định.
5. Nếu cần tách riêng tác dụng head, lập thí nghiệm có đối chứng phù hợp.

**Điều kiện hoàn tất:** Kết luận mô tả đúng cấu hình đã so sánh.
Báo cáo không coi ba seed là ba tập test độc lập.

### V09. Hoàn tất phạm vi minh họa CPU và đánh giá webcam

**Vấn đề:** Hình CPU chưa tái lập chính xác điểm CUDA.
Demo webcam chưa có đủ tình huống đánh giá.

**Minh chứng:**

- 20 trong 40 điểm frame CPU không đạt dung sai so với CUDA.
- Sai khác lớn nhất khoảng 0,000684.
- Các cửa sổ đủ dữ liệu trong cảnh live trả attack.
- Chưa có cảnh print bằng giấy thật.
- Lượt reset kết thúc ở 2/5 frame sau khi quay lại.
- Chưa hoàn tất quyết định thứ hai sau chu trình quay lại.

Nguồn: [giới hạn và kết quả Lượt 7](../../../reports/round7/ADDENDUM_RESULTS_DISCUSSION_2026-10-22.md); [kết quả webcam](../../../reports/round7/WEBCAM_RESULTS.json); [bàn giao repository](../../../docs/handoffs/CURRENT.md).

**Việc cần làm:**

1. Ghi hình CPU là minh họa.
2. Giữ quyết định video từ điểm CUDA đã khóa.
3. Tách lỗi tìm mặt khỏi lỗi phân loại PAD.
4. Tách FPS vòng lặp khỏi số frame PAD mỗi giây.
5. Nếu được giao đo tiếp, bổ sung cảnh print thật.
6. Nếu được giao đo tiếp, kiểm chu trình 5/5 → 0/5 → 5/5.

**Điều kiện hoàn tất:** Mỗi tình huống bổ sung có video và log tương ứng.
Nếu chưa đo tiếp, báo cáo giữ trạng thái chưa hoàn tất.


## 4. Cơ sở phân tích và minh chứng


### 4.1. Kiểm toán Tập dữ liệu CASIA-FASD, Bản phân phối Kaggle và Nhãn `HR_1` (AUD-01)

#### A. Hiện tượng trong dữ liệu nguồn
1. Bộ dữ liệu gốc **CASIA-MFSD / CASIA-FASD** (Zhang et al., ICB 2012) gồm 50 đối tượng (20 đối tượng Train, 30 đối tượng Test). Mỗi đối tượng có 12 video `.avi` (3 video người thật và 9 video tấn công).
2. Trong 1.000 frame HR_1 thuộc manifest của bản Kaggle đã dùng, đường dẫn đều nằm dưới `spoof/`. Chưa kiểm toàn bộ archive ngoài phần lấy mẫu.
3. Mẫu kiểm chứng cục bộ tại kho lưu trữ:
   * **Đường dẫn tệp mẫu:** [`s1vHR_1f69.png`](../../../artifacts/round7/figures-attempt03/inputs/test/spoof/s1vHR_1f69.png)
   * **Đường dẫn tương đối trong manifest:** `test/spoof/s1vHR_1f69.png`
   * **Định danh video:** `casia_s21_vHR_1` (`split=test`, `label=1`, `attack_type=live`, `quality=high`).

#### B. Minh chứng xử lý trong mã nguồn
1. Từ điển ánh xạ chuẩn tại [`casia_fasd.py`](../../../src/deepface_pad/casia_fasd.py#L11-L24) định nghĩa:
   * `"1": (1, "live", "normal")`
   * `"2": (1, "live", "low")`
   * `"HR_1": (1, "live", "high")`
   * Các mã `"3"`, `"4"`, `"HR_2"` thuộc `warped_photo`; `"5"`, `"6"`, `"HR_3"` thuộc `cut_photo`; `"7"`, `"8"`, `"HR_4"` thuộc `video_replay`.
   * Ánh xạ HR_1 thành live chất lượng cao đã được đối chiếu với mã truy cập `bob.db.casia_fasd` của Viện Idiap; đây không phải xác minh toàn bộ archive Kaggle.
2. Tại dòng 55–57 của [`casia_fasd.py`](../../../src/deepface_pad/casia_fasd.py#L55-L57), hàm `parse_frame_path` xử lý tường minh lỗi thư mục của Kaggle:
   ```python
   # The Kaggle copy places HR_1 (high-quality bona fide) under spoof.
   if folder_label != protocol_label and video_token != "HR_1":
       raise ValueError(f"folder label contradicts protocol mapping: {relative}")
   ```
3. Khi huấn luyện và đánh giá, lớp [`PadDataset`](../../../src/deepface_pad/data.py#L113-L129) đọc nhãn từ cột `row.label` trong tệp [`casia_fasd_debug.csv`](../../../data/manifests/casia_fasd_debug.csv), hoàn toàn không suy diễn nhãn từ tên thư mục vật lý.

#### C. Kết quả đối chiếu trên 12.000 khung hình
| Hạng mục kiểm tra | Số lượng thực tế | Kết quả xác minh |
| :--- | :---: | :--- |
| Tổng số video có mã `HR_1` trên toàn bộ 50 đối tượng | 50 video | Đủ 100% (16 Train, 4 Val, 30 Test) |
| Tổng số khung hình `HR_1` lấy mẫu đều (20 khung hình/video) | 1.000 khung hình | Toàn bộ có đường dẫn chứa `spoof/` |
| Số khung hình `HR_1` được gán `label=1`, `attack_type=live` | 1.000 khung hình | Chính xác 100%, không có mẫu bị gán nhầm nhãn |
| Số khung hình thuộc các mã khác có mâu thuẫn thư mục – nhãn | 0 khung hình | Không phát sinh lỗi |

---

### 4.2. Giao thức Chia Tập 16/4/30 và Phân loại Intra-Dataset / Intra-Type (AUD-02)

#### A. Lý do kỹ thuật của việc chia 16 Train / 4 Validation / 30 Test
1. Bài báo gốc CASIA-FASD (2012) chỉ chia 20 đối tượng Train và 30 đối tượng Test và trình bày baseline DoG/SVM. Bài gốc không quy định chọn checkpoint theo epoch như quy trình hiện tại.
2. Mạng học sâu (Deep CNN) huấn luyện qua nhiều chu kỳ (epochs). Nếu không tách tập Validation riêng biệt mà dùng tập Test để chọn trọng số tốt nhất (`best.ckpt`) và chọn ngưỡng quyết định $\tau^*$, quá trình thực nghiệm sẽ vi phạm lỗi **Data Snooping** (rò rỉ thông tin tập kiểm thử).
3. Hàm [`build_manifest`](../../../src/deepface_pad/casia_fasd.py#L75-L108) tách cố định 4 đối tượng `val_subjects = {4, 9, 14, 19}` từ 20 đối tượng Train gốc để lập tập Validation, đồng thời giữ nguyên vẹn 30 đối tượng của nhánh Test gốc (`casia_s21` đến `casia_s50`).

#### B. Cấu trúc phân bố dữ liệu (Intra-Dataset, Intra-Type)
| Tập dữ liệu (Split) | Số đối tượng | Số video Live | Số video Warped Photo | Số video Cut Photo | Số video Replay | Tổng số video | Tổng số khung hình |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Train** | 16 | 48 | 48 | 48 | 48 | 192 | 3.840 |
| **Validation** | 4 | 12 | 12 | 12 | 12 | 48 | 960 |
| **Test** | 30 | 90 | 90 | 90 | 90 | 360 | 7.200 |
| **Tổng cộng** | **50** | **150** | **150** | **150** | **150** | **600** | **12.000** |

* **Phân loại bài toán:** Toàn bộ 3 phương thức tấn công (`warped_photo`, `cut_photo`, `video_replay`) và 3 cấp chất lượng camera (`low`, `normal`, `high`) đều xuất hiện cân bằng trong cả tập Train và tập Test. Do đó, giao thức thực nghiệm của đồ án thuộc nhóm **Đánh giá nội tập dữ liệu, cùng loại tấn công (Intra-dataset, Intra-type evaluation)**.
* **Xử lý mất cân bằng lớp 1 Live : 3 Spoof:** Chỉ số đánh giá chính thức $\text{ACER} = \frac{\text{APCER} + \text{BPCER}}{2}$ lấy trung bình cộng trọng số $50:50$ giữa tỷ lệ lỗi trên lớp tấn công và tỷ lệ lỗi trên lớp người thật (`src/deepface_pad/metrics.py`, dòng 56–58), cho hai lớp đóng góp bằng nhau khi chấm điểm. Phép tính không cân bằng dữ liệu huấn luyện.
* **Giới hạn của tập Validation 4 đối tượng:** Do tập Validation chỉ có 48 video (12 video live, 36 video spoof), ba ứng viên E3, E3b và E4 đều đạt kết quả tuyệt đối trên tập Validation ($\text{ACER} = 0\%$, $\text{EER} = 0\%$, $\text{AUC} = 1.0$). Các chỉ số video này không phân định được ba cấu hình đã chọn. Checkpoint head/joint vẫn được chọn bằng BCE frame theo quy tắc riêng.

---

### 4.3. Chuẩn hóa Giả Độ Sâu, Điểm Suy Luận và Khác Biệt Toán Học CDCN / DepthNet / FAS-TD (AUD-03 & AUD-04)

#### A. Chuẩn hóa bản đồ giả độ sâu trong `PadDataset`
Tại [`data.py`](../../../src/deepface_pad/data.py#L116-L125), quy trình nạp nhãn độ sâu cho từng khung hình diễn ra như sau:
1. Với mẫu người thật (`row.depth_path` khác rỗng): Nạp mảng `.npy` sinh từ 3DDFA V2, nội suy song tuyến (Bilinear Interpolation) về kích thước $32 \times 32$, sau đó chuẩn hóa về đoạn $[0, 1]$ bằng lệnh:
   ```python
   maximum = depth.max()
   if maximum > 1:
       depth = depth / maximum
   ```
2. Với mẫu tấn công (`row.depth_path` rỗng): Gán trực tiếp tensor toàn giá trị không `torch.zeros(1, 32, 32)`.

#### B. Công thức tính điểm suy luận (Inference Scoring)
1. **Mô hình một nhánh E1 (`OfficialCDCN`):** Điểm số của một khung hình là trung bình cộng 1.024 phần tử trên bản đồ độ sâu dự đoán $\hat{D} \in \mathbb{R}^{32 \times 32}$:
   $$s_{\text{frame}}^{(E1)} = \frac{1}{32 \times 32} \sum_{u=1}^{32} \sum_{v=1}^{32} \hat{D}(u, v)$$
2. **Mô hình hai nhánh E2, E3, E3b, E4 (`OfficialCDCNWithDepthHead`):** Bản đồ độ sâu đi qua nhánh phân loại `DepthHead` (`Conv 1->8->16` $\to$ `AdaptiveAvgPool2d(1)` $\to$ `Linear 16->1`) để xuất giá trị $\text{logit}$ (`train.py`, dòng 117, 151):
   $$s_{\text{frame}}^{(E2..E4)} = \sigma(\text{logit}) = \frac{1}{1 + e^{-\text{logit}}}$$
3. **Gộp điểm mức video (`aggregate_video_scores` tại [`metrics.py`](../../../src/deepface_pad/metrics.py#L22-L43)):** Điểm số cuối cùng của một video là trung bình cộng điểm của $N=20$ khung hình thuộc video đó:
   $$S_{\text{video}} = \frac{1}{20} \sum_{k=1}^{20} s_{\text{frame}, k}$$

#### C. Phân biệt toán học giữa 3 thế hệ kiến trúc độ sâu
| Tiêu chí đối sánh | DepthNet (Liu et al., CVPR 2018) | FAS-TD (Wang et al., CVPR 2019) | CDCN (Yu et al., CVPR 2020 - Đồ án sử dụng) |
| :--- | :--- | :--- | :--- |
| **Toán tử trích xuất đặc trưng** | Tích chập 2D tiêu chuẩn (Vanilla 2D Convolution) lấy tổng có trọng số cường độ điểm ảnh $x(p_0 + p_n)$. | Tích chập 2D kết hợp mô-đun Gradients và truyền trạng thái qua các khung hình. | **Tích chập Sai phân Tâm (CDC):** Kết hợp cường độ điểm ảnh và sai phân trung tâm $x(p_0 + p_n) - x(p_0)$ theo hệ số $\theta = 0.7$. |
| **Miền thông tin khai thác** | Không gian 1 khung hình + tín hiệu nhịp tim từ xa (rPPG). | Không-thời gian đa khung hình (Optical Flow / ConvGRU). | Vi kết cấu đạo hàm bậc nhất trên từng khung hình tĩnh độc lập. |
| **Hàm mất mát độ sâu** | Sai số bình phương trung bình (MSE / Euclidean Loss). | MSE kết hợp ràng buộc dòng chảy độ sâu theo thời gian. | $\mathcal{L}_{\text{depth}} = \lambda_{\text{abs}}\mathcal{L}_{\text{MSE}} + \lambda_{\text{contrast}}\mathcal{L}_{\text{CDL}}$ với 8 bộ lọc hướng lân cận (`losses.py`, dòng 41–66). |


---

### 4.4. Phân tích BCE, Focal Loss và giới hạn chọn checkpoint (AUD-05)

#### A. Quan hệ bất đẳng thức giữa Focal Loss và BCE Loss
Tại [`losses.py`](../../../src/deepface_pad/losses.py#L69-L80), lớp `FocalLoss` định nghĩa hàm mất mát trên từng mẫu:
$$\mathcal{L}_{\text{Focal}} = \alpha_t (1 - p_t)^\gamma \mathcal{L}_{\text{BCE}}$$
Trong đó:
* $p = \sigma(\text{logit})$ là xác suất dự đoán lớp người thật (`label = 1`).
* $p_t = p$ nếu $y = 1$ (người thật) và $p_t = 1 - p$ nếu $y = 0$ (tấn công).
* $\alpha_t = \alpha$ nếu $y = 1$ và $\alpha_t = 1 - \alpha$ nếu $y = 0$.

Vì $0 \le \alpha_t \le 1$, $0 \le p_t \le 1$ và $\gamma = 2.0 > 0$, nên hệ số điều biến thỏa mãn $0 \le \alpha_t (1 - p_t)^\gamma \le 1$. Do đó, **khi tính trên cùng một tập dự đoán**, giá trị Focal Loss luôn nhỏ hơn hoặc bằng BCE Loss. Tuy nhiên, do E3 và E4 sinh ra hai bộ trọng số và dự đoán khác nhau, người nghiên cứu tuyệt đối không được so sánh trực tiếp con số tuyệt đối của hai hàm mất mát này để kết luận mô hình nào tốt hơn.

#### B. Nghịch lý hệ số trọng số $\alpha = 0.25$ trong cấu hình E4
1. Trong tập dữ liệu CASIA-FASD, tỷ lệ mẫu giữa lớp người thật (`label = 1`) và lớp tấn công (`label = 0`) là **1 : 3** (lớp người thật là lớp thiểu số).
2. Trong cấu hình [`casia_e4_staged_focal.yaml`](../../../configs/casia_e4_staged_focal.yaml) và dòng 79 của [`losses.py`](../../../src/deepface_pad/losses.py#L79):
   ```python
   alpha_t = torch.where(targets == 1, self.alpha, 1 - self.alpha)
   ```
   Với `self.alpha = 0.25`, mẫu người thật nhận trọng số $\alpha_1 = 0.25$, trong khi mẫu tấn công nhận trọng số $\alpha_0 = 0.75$.
3. Tại cùng xác suất dành cho nhãn đúng, hệ số alpha của live bằng một phần ba của attack. Điều này không bảo đảm gradient thực tế giữa hai lớp có tỷ lệ cố định. Alpha hiện tại không ưu tiên lớp live thiểu số.

#### C. Giới hạn của tiêu chí chọn checkpoint `classification_bce`
1. Tại hàm [`_selection_loss`](../../../src/deepface_pad/train.py#L97-L110), head/joint luôn dùng BCE frame validation để chọn checkpoint; không chờ ACER hòa mới dùng BCE.
2. Sau khi có checkpoint joint đại diện từng cấu hình, hệ thống chọn ngưỡng và tính chỉ số video. Bước chọn giữa E3/E3b/E4 mới xét ACER → EER → AUC → BCE. Ba chỉ số đầu hòa nên BCE quyết định E3 theo quy tắc đã đăng ký.
3. Hai bước thuộc cùng chuỗi lựa chọn. Đổi phép đo cuối không kiểm tra được checkpoint đã bị loại ở bước trước. Ở staged training, best head còn quyết định điểm khởi đầu joint.
4. Có thể tính chung BCE cho mô hình học BCE và Focal để đo chất lượng điểm xác suất. Điều đó không chứng minh ưu thế PAD khi ACER/EER/AUC hòa, cũng không bảo đảm tiêu chí đã phù hợp mọi mục tiêu.
5. Không có căn cứ khẳng định E4 tất nhiên có BCE validation tệ hơn. Tối ưu train không bảo đảm xếp hạng trên validation. Các tập cùng tỷ lệ lớp vẫn có thể khác người và độ khó.
6. Alpha/gamma và lambda cần được xem xét. Với E4, BCE joint thấp nhất ở epoch 6, tổng depth + Focal thấp nhất ở epoch 3. Log không đủ để kết luận epoch 3 ít lỗi PAD hơn.
7. Phương án đề xuất là lấy chỉ số PAD làm chính trong phép thử mới, báo hòa khi chỉ số đã chốt hòa, và giữ BCE/Brier làm thông tin bổ sung. Người dùng chưa chốt thay đổi; kết quả và ngưỡng lịch sử được giữ nguyên.

Nguồn phương pháp và số liệu tính lại: [kết quả EXP-00/01](../../reviews/fair_comparison_20261030/KET_QUA.md).
Nguồn học thuật bổ sung: [Loss Functions and Metrics in Deep Learning v3](https://arxiv.org/html/2307.02694v3), [nghiên cứu Focal và ước lượng xác suất](https://arxiv.org/html/2011.09172), [đánh giá NLL của mô hình Focal và CE](https://torrvision.com/focal_calibration/).

---

### 4.5. Cơ Chế "Step" Trong Mã Nguồn Huấn Luyện và Yếu Tố Gây Nhiễu E1 – E3 (AUD-06)

#### A. Bốn khía cạnh của "Step" trong [`train.py`](../../../src/deepface_pad/train.py)
1. **Bước cập nhật trọng số theo Batch (`optimizer.step()`):**
   * Thực hiện tại dòng 220 của [`train.py`](../../../src/deepface_pad/train.py#L220) sau mỗi mini-batch.
   * Với tập Train có $3.840$ khung hình và `batch_size = 8`, mỗi epoch thực hiện chính xác:
     $$\text{Steps per epoch} = \frac{3.840}{8} = 480 \text{ bước cập nhật}$$
2. **Bước giảm tốc độ học (`StepLR` và `scheduler.step()`):**
   * Dòng 210–215 khởi tạo `torch.optim.lr_scheduler.StepLR(optimizer, step_size=..., gamma=0.5)` và dòng 243 gọi `scheduler.step()` ở **cuối mỗi epoch**.
   * Trong tệp [`casia_e1_cdcn_official.yaml`](../../../configs/casia_e1_cdcn_official.yaml#L19-L25), cấu hình đặt `epochs: 30` nhưng `step_size: 500`. Vì `scheduler.step()` chỉ được gọi 30 lần (nhỏ hơn 500), tốc độ học của E1 giữ nguyên ở mức $\text{LR} = 10^{-4}$ trong suốt 30 epochs.
   * Trong các cấu hình E3, E3b và E4, trường `step_size` không được khai báo nên biến `scheduler` nhận giá trị `None`.
3. **Bộ đếm bước toàn cục (`global_step`):**
   * Mã nguồn **không** lưu biến `global_step`. Tệp `train_log.csv` ghi nhận kết quả theo từng `epoch` (dòng 229–249) và lưu chỉ số `"global_epoch": len(history)` trong checkpoint (dòng 241).
4. **Các giai đoạn huấn luyện đa chặng (`stages`):**
   * Hàm `_set_stage` (dòng 87–95) hỗ trợ 3 chế độ: `depth` (đóng băng `head`, chỉ học nhánh độ sâu), `head` (đóng băng `backbone`, chỉ học nhánh phân loại) và `joint` (mở khóa toàn bộ mạng).

#### B. Yếu tố gây nhiễu (Confounding Factors) khi so sánh E1 và E3
Khi đối sánh E1 và E3, sự thay đổi không chỉ nằm ở kiến trúc đầu ra mà bao gồm 3 yếu tố đi kèm:
1. **Kiến trúc:** E1 dùng phép lấy trung bình không tham số (`Mean Depth`); E3 gắn thêm nhánh `DepthHead` ($1.265$ tham số).
2. **Ngân sách huấn luyện (Training Budget):** E1 huấn luyện 30 epochs từ đầu; E3 nạp trọng số tốt nhất của E1 và huấn luyện thêm 16 epochs ở chế độ `joint`. Chi phí hai run gồm 30 + 16 epoch; không có nghĩa quỹ đạo E3 nối từ trọng số cuối epoch 30 của E1.
3. **Hệ số suy giảm trọng số (`weight_decay`):** E1 dùng `weight_decay = 0.00005` (`5e-5`), trong khi E3 dùng `weight_decay = 0.0001` (`1e-4`).

> Phép so sánh E1–E3 phản ánh tác động tổng hợp của nhánh phân loại và quá trình tinh chỉnh bổ sung.

---

### 4.6. Đo Lường ISO/IEC 30107-3, Lặp Lại Đa Hạt Giống và Sai Số CPU vs CUDA (AUD-07)

#### A. Sự khác biệt giữa Pooled APCER và Worst-Case APCER theo ISO/IEC 30107-3
1. **Phạm vi đối chiếu:** Nhiều protocol PAD báo APCER theo nhóm công cụ tấn công rồi tổng hợp trường hợp xấu nhất. Có thể tính bổ sung $\max_c \text{APCER}_c$ trên ba nhóm warped/cut/replay của dự án, nhưng không tự gọi đó là APCER theo đầy đủ ISO. Ba nhãn attack_type này chưa được chứng minh tương đương cách định nghĩa PAI species của một đánh giá theo chuẩn. Công thức ACER riêng lẻ không xác nhận tuân thủ toàn bộ tiêu chuẩn.
2. **Trong mã nguồn [`metrics.py`](../../../src/deepface_pad/metrics.py#L56-L58):** Hàm `error_rates` tính $\text{APCER}$ gộp (Pooled APCER) bằng trung bình cộng trên toàn bộ 270 video tấn công. Để đảm bảo tính chặt chẽ, Lượt 7 đã trích xuất bảng phân rã lỗi theo từng nhóm tấn công và chất lượng camera tại `reports/round7/analysis/`.

#### B. Kết quả tái lập đa hạt giống (Seeds 43, 44, 45 - Lượt 6)
| Hạt giống (Seed) | ACER E1 (%) | ACER E3 (%) | Chênh lệch $\Delta = \text{E3} - \text{E1}$ (%) | Số video E3 sửa được / gây lỗi mới |
| :---: | :---: | :---: | :---: | :---: |
| **Seed 43** | 6.6667 | 3.3333 | -3.3333 | Sửa 6 video / Thêm 0 lỗi |
| **Seed 44** | 2.4074 | 4.4444 | +2.0370 | Sửa 1 video / Thêm 4 lỗi (từ chối người thật) |
| **Seed 45** | 3.8889 | 3.3333 | -0.5556 | Sửa 2 video / Thêm 1 lỗi |
| **Trung bình $\pm$ SD** | **4.3210 $\pm$ 2.1623** | **3.7037 $\pm$ 0.6415** | **-0.6173 $\pm$ 2.6857** | **SD quan sát của E3 nhỏ hơn; hiệu quả đảo chiều ở seed 44** |

* **Hiệu ứng lượng tử hóa cỡ mẫu:** Tập Test có 90 video người thật. Mỗi một video người thật bị phân loại sai làm $\text{BPCER}$ tăng thêm $\frac{1}{90} \approx 1.1111\%$, kéo theo $\text{ACER}$ tăng $0.5556\%$.
* **Giới hạn của kiểm chứng đa hạt giống:** Cả 3 seed đều chấm điểm trên cùng 360 video Test của CASIA-FASD. Phép thử này khảo sát độ biến thiên khi thay đổi khởi tạo ngẫu nhiên, nhưng không chứng minh khả năng tổng quát hóa sang tập dữ liệu khác (Cross-dataset Generalization).

#### C. Sai số số học giữa CPU và GPU CUDA

Trong 40 forward CPU dùng để dựng hình, 20 điểm frame vượt dung sai so với CUDA đã lưu.
Sai khác điểm frame lớn nhất khoảng 0,000684.
Nguyên nhân chưa được xác định đầy đủ.
Trạng thái TF32 lịch sử chưa được ghi đủ.
Quyết định video dùng điểm CUDA đã cố định.
Hình CPU chỉ phục vụ minh họa.
Nguồn: [Addendum Lượt 7](../../../reports/round7/ADDENDUM_RESULTS_DISCUSSION_2026-10-22.md).

---

### 4.7. Thực Nghiệm Webcam Thời Gian Thực, Median Gate và Phân Tích Lỗi Từ Chối Người Thật (AUD-08)

#### A. Cơ chế hoạt động của `MedianGate` tại [`webcam.py`](../../../src/deepface_pad/webcam.py#L35-L86)
1. **Bộ phát hiện khuôn mặt:** Thay thế Haar Cascade bằng mạng CNN **YuNet** (`face_detection_yunet_2023mar.onnx`, ngưỡng tin cậy $0.5$) để khắc phục lỗi mất dấu khuôn mặt.
2. **Điều kiện duy trì cửa sổ trượt (`window = 5`):**
   * Khung hình phải chứa đúng 1 khuôn mặt (`face_count == 1`).
   * Khoảng cách thời gian giữa hai khung hình hợp lệ liên tiếp không vượt quá `maximum_gap = 5.0` giây (thích nghi với tốc độ suy luận $1.7 - 2.2\text{ s/frame}$ trên CPU Intel Core i5-7200U).
   * Độ chồng lấp hình học giữa hai khung giới hạn liên tiếp đạt `minimum_iou >= 0.4`.
   * Nếu vi phạm bất kỳ điều kiện nào, hàm `self.reset()` xóa toàn bộ bộ đệm về `0/5` (cơ chế Fail-closed).
3. **Cách tính thời gian ra quyết định đầu tiên (TTD - Time-To-Decision):**
   * Biến `self.started_at` ghi nhận thời điểm bắt đầu đọc khung hình hợp lệ thứ nhất của chu kỳ (`captured_at`).
   * Khi thu thập đủ 5 khung hình hợp lệ (`len(self.scores) == 5`), hệ thống tính trung vị `value = median(self.scores)`, so sánh với ngưỡng $\tau^* = 0.3983212910592556$ và xuất $\text{TTD} = \text{finished\_at} - \text{self.started\_at}$.

#### B. Bảng kết quả đo thực tế trên phần cứng CPU
| Mã lượt đo | Kịch bản kiểm thử | Thời lượng (s) | Khung đọc / Khung PAD | Tốc độ PAD (frame/s) | TTD (giây) | Kết quả quyết định |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| `live-02` | Người thật (Haar pilot) | 30.399 | 450 / 2 | 0.066 | Thiếu cửa sổ | Không đủ 5 khung hình do Haar bỏ sót mặt |
| `live-03` | Người thật (YuNet) | 45.224 | 738 / 12 | 0.265 | **10.378** | **Attack (Từ chối nhầm người thật)** |
| `replay-01` | Phát lại điện thoại (rung tay) | 46.338 | 108 / 26 | 0.561 | Thiếu (tối đa 4/5) | Bộ đệm tự xóa về 0/5 khi lệch IoU |
| `replay-02` | Phát lại điện thoại (cố định) | 45.594 | 34 / 28 | 0.614 | **7.407; 8.606** | **Attack (Chặn đúng tấn công phát lại)** |
| `live-reset-01` | Kiểm tra rời / quay lại khung | 45.750 | 166 / 25 | 0.546 | **7.174** | Xác nhận xóa bộ đệm về 0/5 khi rời khung |

#### C. Lỗi từ chối người thật và nguyên nhân chưa xác định

Các cửa sổ đủ dữ liệu của live-03 trả attack.
Đây là quan sát thực nghiệm về lỗi từ chối người thật.
Ánh sáng, cảm biến, crop hoặc khác biệt miền dữ liệu là những giả thuyết cần kiểm tra.
Chưa có thí nghiệm đối chứng để xác định nguyên nhân riêng.
Nguồn: [Kết quả webcam](../../../reports/round7/WEBCAM_RESULTS.json).

---


## 5. Tài liệu phân tích liên quan


| STT | Tài liệu phân tích | Phạm vi nội dung |
| :---: | :--- | :--- |
| 01 | [`ANALYSIS_01_ROUNDS1_3_BASELINE_VA_PSEUDO_DEPTH_SUPERVISION.md`](</C:/Users/LAPTOP T&T/Downloads/ANALYSIS_01_ROUNDS1_3_BASELINE_VA_PSEUDO_DEPTH_SUPERVISION.md>) | Đối chuẩn Baseline E0 (MobileNetV3), quy trình sinh nhãn giả độ sâu 3DDFA V2 và kiểm toán dữ liệu Lượt 1–3. |
| 02 | [`ANALYSIS_02_ROUND4_HEAD_ABLATION_E1_VS_E2_BOTTLENECK.md`](</C:/Users/LAPTOP T&T/Downloads/ANALYSIS_02_ROUND4_HEAD_ABLATION_E1_VS_E2_BOTTLENECK.md>) | Phân tích thực nghiệm Lượt 4: Đối sánh E1 (Mean Depth) và E2 (Frozen Backbone + DepthHead), khảo sát giới hạn của biểu diễn độ sâu. |
| 03 | [`ANALYSIS_03_ROUND5_TRAINING_STRATEGIES_E0_E4_SEED42.md`](</C:/Users/LAPTOP T&T/Downloads/ANALYSIS_03_ROUND5_TRAINING_STRATEGIES_E0_E4_SEED42.md>) | Phân tích thực nghiệm Lượt 5: Đối sánh toàn diện 6 mô hình E0–E4 tại seed 42 (Joint BCE, Staged BCE, Staged Focal Loss). |
| 04 | [`ANALYSIS_04_ROUND6_MULTI_SEED_REPLICATION_SEEDS_43_44_45.md`](</C:/Users/LAPTOP T&T/Downloads/ANALYSIS_04_ROUND6_MULTI_SEED_REPLICATION_SEEDS_43_44_45.md>) | Phân tích thực nghiệm Lượt 6: Tái lập đa hạt giống (Seeds 43, 44, 45) giữa E1 và E3, phân tích phương sai và đảo chiều tại Seed 44. |
| 05 | [`ANALYSIS_05_ROUND6_A100_LATENCY_AND_COMPUTATIONAL_COST.md`](</C:/Users/LAPTOP T&T/Downloads/ANALYSIS_05_ROUND6_A100_LATENCY_AND_COMPUTATIONAL_COST.md>) | Đo lường chi phí tính toán (Tham số, FLOPs, độ trễ suy luận p50/p95 trên GPU A100) giữa E1 và E3. |
| 06 | [`ANALYSIS_06_ROUND6_PAPER_PROTOCOL_COMPARISON.md`](</C:/Users/LAPTOP T&T/Downloads/ANALYSIS_06_ROUND6_PAPER_PROTOCOL_COMPARISON.md>) | Đối chiếu giao thức thực nghiệm của đồ án với bài báo gốc CASIA-FASD (2012) và CDCN (CVPR 2020). |
| 07 | [`ANALYSIS_07_ROUND7_PAIRED_ERROR_AND_SUBGROUP_ANALYSIS.md`](</C:/Users/LAPTOP T&T/Downloads/ANALYSIS_07_ROUND7_PAIRED_ERROR_AND_SUBGROUP_ANALYSIS.md>) | Phân tích lỗi bắt cặp (Paired Error) và phân rã hiệu năng theo từng nhóm tấn công / chất lượng video ở Lượt 7. |
| 08 | [`ANALYSIS_08_ROUND7_NUMERICAL_DISCREPANCY_CPU_VS_CUDA.md`](</C:/Users/LAPTOP T&T/Downloads/ANALYSIS_08_ROUND7_NUMERICAL_DISCREPANCY_CPU_VS_CUDA.md>) | Phân tích sai lệch số học dấu phẩy động giữa môi trường suy luận CPU và GPU CUDA trong quá trình xuất hình minh họa Lượt 7. |
| 09 | [`ANALYSIS_09_ROUND7_REALTIME_WEBCAM_MEDIAN_GATE_AND_TTD.md`](</C:/Users/LAPTOP T&T/Downloads/ANALYSIS_09_ROUND7_REALTIME_WEBCAM_MEDIAN_GATE_AND_TTD.md>) | Đánh giá đường ống suy luận Webcam thời gian thực, bộ lọc trung vị 5 khung hình (`MedianGate`), chỉ số TTD và phân tích lỗi từ chối người thật. |

---


## 6. Nội dung đề xuất cho báo cáo

### 6.1. Dữ liệu và giao thức

Nghiên cứu dùng bản frame CASIA-FASD trên Kaggle.
Nhãn được xác định từ mã video thay vì tên thư mục.
Các frame HR_1 được dùng trong dự án có nhãn người thật.
Nhóm dành bốn người từ train gốc để lập validation.
Các mã được chọn là 4, 9, 14 và 19.
Hồ sơ chưa giải thích lý do chọn đúng bốn mã này.
Nhánh test của nguồn được giữ nguyên.
Đánh giá thuộc loại intra-dataset, intra-type và không trùng chủ thể giữa các tập.
Nghiên cứu chưa tái lập nguyên vẹn quy trình của CASIA gốc.

### 6.2. Lựa chọn mô hình và Focal Loss

E4 được huấn luyện bằng Focal nhưng chọn checkpoint theo BCE validation.
Ba ứng viên có ACER và EER validation bằng 0, với AUC bằng 1.
BCE được dùng để phân định sau các chỉ số này.
Kết quả lựa chọn là E3.
Chọn checkpoint và chọn cấu hình là hai bước nối tiếp của cùng quy trình.
BCE là phép đo điểm xác suất, chưa chứng minh ưu thế PAD khi các chỉ số PAD hòa.
E4 có ACER test thấp hơn E3 ở seed 42.
Quan sát đó không thay đổi lựa chọn đã xác lập từ validation.
Thí nghiệm chưa xác định checkpoint E4 tối ưu theo Focal.
Alpha hiện tại không tăng ưu tiên cho lớp live thiểu số.
Kết quả chưa đủ để kết luận Focal nói chung kém hiệu quả.

### 6.3. Độ ổn định và phạm vi so sánh

E3 tốt hơn E1 ở seed 43 và 45.
E3 kém hơn E1 ở seed 44.
Ba seed dùng cùng 360 video test.
Kết quả chưa chứng minh cải thiện ổn định.
E1 và E3 còn khác ngân sách huấn luyện và weight decay.
Vì vậy, chênh lệch hiệu năng chưa thể quy cho riêng head.
APCER hiện tại được tính gộp trên các loại tấn công.
Phép tổng hợp này cần được phân biệt với đánh giá PAI xấu nhất.

### 6.4. Minh họa CPU và webcam

Hình CPU có sai khác điểm frame so với CUDA vượt dung sai đã đặt.
Quyết định video vẫn dùng kết quả CUDA đã cố định.
Các cửa sổ đủ dữ liệu trong cảnh live đã trả attack.
Nguyên nhân lỗi live chưa được xác định bằng phép thử có đối chứng.
Giả thuyết về ánh sáng hoặc dịch chuyển miền dữ liệu cần được kiểm tra riêng.
Cảnh ảnh in và chu trình quay lại đủ cửa sổ vẫn chưa hoàn tất.
Các clip hiện có chưa chứng minh khả năng xác thực thực tế.
