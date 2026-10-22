# Bàn giao công việc nghiên cứu DeepFace-PAD

Ngày lập: 22/10/2026. Điểm nguồn trước khi lập bàn giao:
`256690e5daf94adf62efa62afc0a7cf0d91c330c`.

## 1. Mục đích và cách đọc

Nhóm cần hoàn tất Lượt 7 và Lượt 8. Nhóm có thể lập thí nghiệm mới sau đó.
Bản này xác định phần đã có, phần còn thiếu và bằng chứng cần lưu.

Bản này áp dụng nguyên tắc viết rõ của ASD-STE100: thuật ngữ nhất quán,
câu ngắn, thao tác theo thứ tự và điều kiện hoàn tất cụ thể. ASD-STE100 là
tiêu chuẩn tiếng Anh. Bản tiếng Việt này không phải bản được chứng nhận STE.
Tham khảo [nguồn chính thức](https://www.asd-ste100.org/about_STE.html).

Đọc trạng thái trong bản này trước kế hoạch cũ. Tài liệu lịch sử vẫn giữ
nguyên số liệu và ngày lập. Một ô chưa tích trong tài liệu cũ không tự tạo
thêm công việc hiện tại. Một ô đã tích không thay bằng chứng thực tế.

## 2. Thuật ngữ

| Thuật ngữ | Nghĩa dùng trong dự án |
| --- | --- |
| PAD | Phân biệt mặt người thật với tấn công dùng ảnh in hoặc màn hình phát lại. |
| E0 | MobileNetV3-Small phân loại trực tiếp ảnh RGB. |
| E1 | Kiến trúc Official CDCN, học bản đồ độ sâu; điểm là trung bình bản đồ dự đoán. |
| E2 | E1 được giữ cố định, thêm bộ phân loại học từ bản đồ độ sâu. |
| E3 | E1 và bộ phân loại độ sâu được học đồng thời bằng loss độ sâu và BCE. |
| E3b | Học theo giai đoạn; dùng BCE ở phần phân loại. |
| E4 | Học theo giai đoạn; dùng Focal Loss ở phần phân loại. |
| Pseudo-depth | Bản đồ độ sâu giám sát từ 3DDFA; không phải độ sâu 3D đo thật. |
| Seed | Giá trị khởi tạo bộ sinh số ngẫu nhiên. |
| Validation | Tập dùng để chọn checkpoint và ngưỡng. |
| Test | Tập dùng để đánh giá sau khi khóa lựa chọn. CASIA hiện tại đã được quan sát. |
| Checkpoint | Tệp trọng số và thông tin lựa chọn mô hình. |
| Bản khóa | JSON ghi mô hình, ngưỡng và hash trước khi mở test. |
| False live | Attack bị nhận nhầm là người thật. |
| False spoof | Người thật bị từ chối. |
| APCER | Số false live chia số video attack. |
| BPCER | Số false spoof chia số video live. |
| ACER | Trung bình APCER và BPCER. |
| TTD | Thời gian từ lần đọc đầu của đoạn mặt hợp lệ đến quyết định đủ cửa sổ. |
| RGB | Ảnh màu có ba kênh đỏ, xanh lá và xanh dương. |
| CDCN | Mạng tích chập dùng phép sai phân trung tâm để học bản đồ độ sâu. |
| Head | Bộ phân loại nhận bản đồ độ sâu làm đầu vào. |
| BCE | Hàm mất mát cho phân loại hai lớp. |
| Focal Loss | Hàm mất mát giảm trọng số đóng góp của các mẫu dễ. |
| Frontend | Phần tìm mặt, chọn vùng ảnh và theo dõi mặt trước khi chạy PAD. |
| IoU | Diện tích giao chia diện tích hợp của hai khung mặt. |
| FPS | Số frame xử lý trong một giây; phải ghi rõ phạm vi đo. |
| SHA-256 | Mã kiểm nội dung tệp. Nội dung khác phải có mã khác. |

Mean là trung bình. Sample SD là độ lệch chuẩn mẫu, dùng mẫu số n−1.

Checkpoint hiện tại không lưu đủ optimizer, scheduler và RNG để tiếp tục
đúng trạng thái huấn luyện đã ngắt. Nạp trọng số để khởi tạo là thao tác khác.

## 3. Dữ liệu và quy tắc đã khóa

CASIA development có 50 người, 600 video và 12.000 frame. Split theo người:
16 train, 4 validation, 30 test. Train có 192 video/3.840 frame; validation
có 48 video/960 frame; test có 360 video/7.200 frame. Mỗi video dùng 20 frame.
Test gồm 270 attack và 90 live. Nhãn 0 là attack; nhãn 1 là live.

Điểm cao hơn biểu thị khả năng live cao hơn. Quyết định live khi score >=
threshold. Điểm video là trung bình 20 điểm frame. Ngưỡng lấy riêng từ
validation: ACER nhỏ nhất, sau đó độ lệch APCER/BPCER nhỏ nhất, rồi ngưỡng nhỏ hơn.

Giữ manifest depth có SHA-256:
`4c302c9039e48a8ea6baedf426b26e1b0a6663bc295c661bb71fefccdb9b37fd`.
Giữ bản khóa Lượt 6 có SHA-256:
`1a669e3878c561abfcd245a12eb2d4d8edb434af1a8854aecc1bcdd89a0e43a1`.
Không đổi split, target depth hoặc threshold để sửa kết quả đã công bố.

## 4. Kết quả đã có

### 4.1. Lượt 1 đến Lượt 5

Seed lịch sử là 42. Test video ACER: E0 5,5556%; E1 2,7778%; E2 2,7778%;
E3 5,0000%; E3b 5,0000%; E4 4,4444%. E3 được chọn bằng validation trước test.
Không thay E3 bằng E4 sau khi xem thứ hạng test. E1-Lite và các lượt smoke
không thuộc bảng kết quả chính.

Nguồn số chính xác và run ID: `reports/ROUND_5_TEST_RESULTS_2026-10-16.json`.
Bản Word báo cáo, paper và slide hiện tại trình bày đến Lượt 5. Các bản này
chưa chứa kết quả mới của Lượt 6 và Lượt 7.

### 4.2. Lượt 6: ba cặp E1/E3

Đã chạy đủ sáu model và 138 epoch. Mỗi E1 học 30 epoch. Mỗi E3 học 16 epoch
từ best E1 cùng seed. Không trộn seed 42 vào thống kê ba seed mới.

| Seed | ACER E1 (%) | ACER E3 (%) | E3 − E1 (điểm phần trăm) | Sửa lỗi / tạo lỗi mới |
| --- | ---: | ---: | ---: | ---: |
| 43 | 6,6667 | 3,3333 | −3,3333 | 6 / 0 |
| 44 | 2,4074 | 4,4444 | +2,0370 | 1 / 4 |
| 45 | 3,8889 | 3,3333 | −0,5556 | 2 / 1 |

Mean ± sample SD, ddof=1: E1 4,3210 ± 2,1623%; E3 3,7037 ± 0,6415%.
Paired delta là −0,6173 ± 2,6857 điểm phần trăm. E3 chỉ tốt hơn ở 2/3 seed.
Chưa chứng minh cải thiện ổn định. Không tuyên bố ý nghĩa thống kê từ ba seed.
Training budget và weight decay khác nhau; chưa cô lập tác dụng riêng của head.
Ba seed dùng lại cùng 360 video, không tạo 1.080 video độc lập.

Nguồn: `reports/ROUND_6_RESULTS_2026-10-22.md/.json`.

### 4.3. Chi phí forward đã đo trên A100

Đủ 1.200 mẫu/model trong cùng block A100 mới. E1/E3/E4 lần lượt có
2.245.016 / 2.246.281 / 2.246.281 tham số. CUDA p50 lần lượt khoảng
5,9167 / 5,9638 / 5,9617 ms. E3 tăng 1.265 tham số, tương đương 0,05635%;
CUDA p50 tăng 0,7961%, p95 tăng 0,8282%. Không chọn lượt đo nhanh nhất.

Đây là forward float32, batch 1. Phép đo không gồm detector, crop hoặc webcam.
Không lấy nghịch đảo latency A100 làm FPS webcam. Nguồn: báo cáo cost Lượt 6.
Đối chiếu paper chỉ là bối cảnh khi protocol khác. Không lập thứ hạng chung.

### 4.4. Lượt 7: phân tích lỗi và hình

Đã ghép đúng E1/E3 theo seed, video và nhãn. Subgroup có số lỗi và mẫu số.
Quality không phải phép đo ánh sáng hoặc blur. Không suy nguyên nhân từ tên nhãn.

Đã chọn 20 case trước khi xem RGB và chạy 40 forward CPU để dựng hình.
Hình gồm RGB, target, prediction và absolute error. Các panel dùng cùng thang màu.
20/40 score frame không đạt tolerance cũ so với CUDA; max lệch khoảng 0,000684.
Đây là inference CPU minh họa, chưa tái lập chính xác score CUDA. Không nới
tolerance hoặc thay score cũ. Quyết định video trên hình vẫn lấy từ CSV đã khóa.

Nguồn: `reports/round7/analysis/`, `reports/round7/figures-attempt03/` và
`reports/round7/ADDENDUM_RESULTS_DISCUSSION_2026-10-22.md`. Raw arrays được giao.
Lần strict dừng và numeric diagnostic được giữ để nhóm xem lại.

### 4.5. Webcam

Đã dùng CPU Intel i5-7200U, hai thread, webcam MSMF 640×480. Model E3 seed 43
là seed đầu đã đăng ký. Threshold validation là 0,3983212910592556.
Config cuối: YuNet 2023mar, confidence detector 0,5; median 5 frame;
gap 5 giây; IoU 0,4. Confidence detector khác threshold PAD.

| Lượt | Giây đo | Frame đọc/PAD | FPS vòng | Frame PAD/s | TTD (s) |
| --- | ---: | ---: | ---: | ---: | --- |
| Haar live pilot | 30,399 | 450/2 | 14,803 | 0,066 | thiếu |
| live-03 | 45,224 | 738/12 | 16,319 | 0,265 | 10,378 |
| replay-01 | 46,338 | 108/26 | 2,331 | 0,561 | thiếu, tối đa 4/5 |
| replay-02 | 45,594 | 34/28 | 0,746 | 0,614 | 7,407; 8,606 |
| live-reset-01 | 45,750 | 166/25 | 3,628 | 0,546 | 7,174 |

FPS vòng gồm cả frame không chạy PAD. Frame PAD/s đếm forward thật chia cùng
thời lượng. TTD gồm thời gian gom đủ cửa sổ. Warm-up và chờ Space ngoài timing.
Không đo được thời điểm vật lý mặt bắt đầu xuất hiện hoặc timestamp cảm biến.

Các cửa sổ đủ dữ liệu ở cảnh live đều trả attack. Đây là failure case từ chối
người thật. Replay-02 trả attack, nhưng không chứng minh khả năng tổng quát.
Replay-01 chưa có quyết định. Không ghi lượt thiếu TTD thành TTD bằng 0.

`0/5` đến `5/5` đếm frame hợp lệ, không đếm giây. `no_face` là detector không
tìm thấy box. Trạng thái này không chứng minh người đã rời khung. Người dùng
xác nhận không chủ ý rời khung ở live-03. Ở lượt reset riêng, đã thấy buffer
về 0 và gom mới; khi quay lại chỉ đạt 2/5 trước hết giờ. Chưa kiểm đủ chu trình.

Năm video/CSV đã được kiểm hash, số frame giải mã, median, state và timing.
Bản GitHub chứa log số. Video đi qua bộ giao nhận riêng. Nhãn cảnh do người
chạy khai báo. Không tính ACER từ vài clip hoặc coi các frame là trial độc lập.

## 5. Công việc còn lại, theo thứ tự

| Mã | Công việc | Đầu vào | Thao tác cần làm | Điều kiện hoàn tất |
| --- | --- | --- | --- | --- |
| H01 | Nhận và kiểm tệp ngoài Git | Danh mục giao nhận | Nhận archive CASIA/cache và bộ riêng. So SHA. | Tệp cần dùng khớp SHA; ghi rõ quyền truy cập còn thiếu. |
| H02 | Chốt môi trường máy nhận | Bộ GitHub | Cài môi trường mới. Chạy verifier và tests. | Lưu phiên bản, thiết bị, log test; không gọi kết quả cũ là test máy mới. |
| H03 | Điều tra sai khác CPU/CUDA | 20 case, checkpoint, source và diagnostic | So tensor, batch, dtype và backend trong output mới. | Giải thích bằng bằng chứng hoặc giữ nguyên trạng thái chưa xác định. Không nới tolerance để báo PASS. |
| H04 | Sửa frontend webcam | Log/video thất bại, detector và crop | Lập protocol riêng. Đo detection, box và reset trước PAD. | Có cảnh mất mặt, nhiều mặt, đổi mặt, quay lại đủ 5 frame. Không nhận live khi thiếu mặt/window. |
| H05 | Điều tra false spoof trên webcam | Cảnh live và model cố định | Kiểm crop/normalization/domain. Thu dữ liệu riêng có nhãn. | Báo nguyên nhân đã kiểm và giới hạn. Nếu chỉnh ngưỡng, dùng calibration riêng và đánh giá trên tập khác. |
| H06 | Bổ sung print | Ảnh in giấy và người vận hành | Ghi một cảnh print thật, config chốt trước đo. | Có video/log/FPS/TTD hoặc báo rõ vì sao chưa quyết định. Ảnh điện thoại không thay print. |
| H07 | Hoàn thiện Results/Discussion | Kết quả Lượt 6, addendum Lượt 7 | Ghép nội dung vào bản thảo mới. Giữ seed 44 và lỗi live. | Mọi bảng/hình truy được nguồn. Nêu khác protocol và giới hạn. |
| H08 | Hoàn thiện Word và paper | Bản thảo mới, template, tài sản hình | Tạo phiên bản mới, cập nhật mục lục và kiểm từng trang. | Có file chỉnh sửa được và bản render đã kiểm. Không ghi đè bản lịch sử. |
| H09 | Hoàn thiện Lượt 8 | Report/paper mới và log | Cập nhật slide, script, Q&A và video dự phòng. | Nhóm kiểm claim, nguồn, bố cục và tập báo cáo. Không ghi đã nộp nếu chưa nộp. |
| H10 | Xác nhận đóng góp và yêu cầu nộp | Quy định học phần và hai thành viên | Xác nhận vai trò, độ dài và định dạng cuối. | Có xác nhận của người chịu trách nhiệm; phân công dự kiến không thành lịch sử. |
| H11 | ArcFace, tùy chọn | PAD đã đạt điều kiện demo | Tích hợp sau phần bắt buộc. | Chỉ công bố danh tính sau PAD live. Không mở rộng web/mobile ngoài phạm vi. |

A dẫn báo cáo Lượt 7; B hỗ trợ demo. B dẫn Lượt 8; A rà soát. Đây là phân công
đề xuất trong kế hoạch. Hai thành viên phải xác nhận công việc thực tế.

## 6. Hướng nghiên cứu tiếp theo

Các mục dưới đây là đề xuất, chưa có số đo.

1. Tách lỗi detector/crop khỏi lỗi PAD. Dùng cùng ảnh đầu vào đã kiểm để so sánh.
2. Kiểm bộ phân loại trên cùng backbone được giữ cố định. Cách này giảm confound
   do budget và weight decay. E2 một seed là bằng chứng lịch sử, chưa đủ kết luận.
3. Nếu đổi architecture/loss, đăng ký ablation và ngân sách trước train.
4. Đánh giá dữ liệu khác domain bằng giao thức riêng. CASIA hiện tại đã được quan sát.
5. Nếu nghiên cứu ánh sáng/blur, định nghĩa phép đo trước. Giữ metadata quality riêng.
6. Đo end-to-end trên thiết bị mục tiêu. Không dùng số forward A100 thay trải nghiệm.

Mỗi thí nghiệm cần ID, câu hỏi, dữ liệu/split, seed, đối chứng, metric chính,
quy tắc chọn checkpoint/threshold, budget, môi trường, điều kiện dừng và output.
Lưu cả thất bại. Một kết quả validation tốt không phải kết quả test độc lập.

## 7. Điều kiện đóng bàn giao

Người nhận kiểm manifest và test trên máy nhận. Người nhận xác nhận quyền
truy cập dữ liệu/video riêng. Nhóm gán người và hạn hoàn tất cho H01–H10.
Giữ H03, H04, H05, H06 và H08 là chưa hoàn tất cho đến khi có bằng chứng tương ứng.
Không đánh dấu toàn bộ dự án hoàn tất chỉ vì đã tạo repository bàn giao.
