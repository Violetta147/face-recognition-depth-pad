# DeepFace-PAD trên OULU-NPU

## Dữ liệu và giao thức

Thư mục Drive của dự án có `Train_files.tar` (37,75 GB), `Dev_files.tar`
(28,15 GB), `Test_files.tar` (39,21 GB), `Protocols.tar`, `Baseline.tar`
và `Readme.pdf`. Đã đọc README và kiểm danh sách trong `Protocols.tar`.
Ba archive video cộng lại khoảng 105,12 GB theo đơn vị thập phân.

| Giao thức | Yếu tố chưa gặp khi đánh giá | Train / Dev / Test (video) |
| --- | --- | --- |
| 1 | Phiên quay, gồm ánh sáng và phông nền | 1.200 / 900 / 600 |
| 2 | Máy in và màn hình dùng để tạo mẫu | 1.080 / 810 / 1.080 |
| 3 | Camera điện thoại, 6 lượt giữ lại từng máy | 1.500 / 1.125 / 300 mỗi lượt |
| 4 | Cả ba yếu tố, 6 lượt giữ lại từng máy | 600 / 450 / 60 mỗi lượt |

Với Protocol 1, `Test.txt` xác nhận 120 video thật, 240 video print và
240 video replay. Con số 1.200 trong bảng bài báo gốc và cột 180 video
attack trong README không khớp danh sách. Mã đọc danh sách đi kèm dataset
và kiểm từng bộ `(phone, session, subject, access)` theo giao thức.

Chuẩn bị dữ liệu bằng `python -m deepface_pad.oulu_npu`. Mã truy cập file
trong TAR theo offset, dùng một AVI tạm và giữ cache PNG lossless trên
đĩa runtime. Mỗi video lấy 20 khoảng thời gian, tìm khung hợp lệ gần giữa
mỗi khoảng, ưu tiên hộp mặt YuNet và dùng tọa độ mắt tác giả cung cấp
khi YuNet không có hộp. Lưu cách crop và SHA-256 theo khung hình và video.
Nếu một khoảng thiếu crop, lấy khung hợp lệ chưa dùng gần tâm khoảng nhất
trong cùng video sau khi đã chọn khung cho các khoảng còn lại. Manifest ghi
`yunet_nearby` hoặc `eyes_nearby`. Nếu toàn video thiếu số khung hợp lệ,
bước chuẩn bị dừng và ghi ID video. Cache hoàn tất từng video, chạy lại
xác thực hash rồi dùng lại phần đã xong. Các crop đã hoàn tất bằng quy tắc
cũ vẫn hợp lệ vì khi đủ khung trong mọi khoảng, lựa chọn giữ nguyên.
Pilot lấy một video cho mỗi cặp camera và kiểu truy
cập trên Train/Dev, không đọc archive Test.

Nguồn: [trang OULU-NPU](https://sites.google.com/site/oulunpudatabase/welcome),
[bài báo FG 2017](https://yty.kapsi.fi/papers/FG2017_OULU-NPU.pdf),
[README của gói dữ liệu](https://drive.google.com/file/d/1qB2LloXSwzwHTocpTUUYxoVU2jAQU6b0/view).

## Lượt nhanh trước bảo vệ

Mở `notebooks/Face_PAD_OULU_NPU_A100.ipynb` trong Google Colab và chọn GPU
A100. Notebook mang theo mã nguồn cần dùng và detector YuNet. Nếu thư
mục dataset nằm trong Shared with me, thêm shortcut vào My Drive và sửa
`DATA` tại cell 1. Chạy cell 1, 2, 4, 5 theo thứ tự. Cell 3 là pilot tùy chọn.
Cell 4 chép từng TAR cần thiết về đĩa runtime, chuẩn bị và lưu từng split.
Cell 5 đo throughput trước khi train.
Sau khi thấy dòng `RUN_DIR=`, điền đường dẫn đó vào cell 6 để chấm Test.

| Quyết định | Cấu hình lượt nhanh |
| --- | --- |
| Dữ liệu | Protocol 1, 8 khung/video, 9.600 khung Train và 7.200 khung Dev |
| Mô hình | MobileNetV3-Small pretrained ImageNet, 224 × 224, BCE, AdamW |
| Huấn luyện | 3 epoch, LR 0,0003, seed 43, chọn batch 64 hoặc 128 bằng khung/giây |
| GPU | BF16 khi GPU hỗ trợ, tính loss và đánh giá ở FP32 |
| Chọn checkpoint | ACER cấp video trên Dev tại ngưỡng gần EER, hòa giữ epoch sớm |
| Chấm Test | Giữ ngưỡng Dev, báo riêng APCER print/replay, lấy max cho APCER chung |

Ngưỡng gần EER dùng APCER gộp khi tìm điểm cân bằng với BPCER. Khi nhiều
ngưỡng có cùng khoảng cách, ưu tiên trung bình lỗi thấp hơn rồi ngưỡng
nhỏ hơn. Điểm video là trung bình điểm live của các khung. Báo thêm số
video lỗi, AUC, EER và APCER gộp. Kết quả lưu trong
`MyDrive/face-pad/oulu-fast-p1`. Log tiến trình con, gồm cả stderr, nằm
trong thư mục `logs`. Nhịp báo khoảng 30 giây cho bước có bộ đếm và 60
giây cho tiến trình con. Báo ETA theo tốc độ trung bình nếu bộ đếm tăng.
Thời gian đọc/crop, train, validation và chấm Test được theo dõi riêng.

Cache RGB nằm ở `/content` khi chạy. Mỗi split hoàn tất được lưu thành
ZIP riêng trong `prepared-cache` trên Drive, gồm PNG, manifest, tóm tắt
và bản ghi từng video. Notebook khôi phục ZIP phù hợp về đĩa runtime rồi
kiểm SHA-256 từng file. Khóa RGB gồm protocol, split, danh sách protocol,
metadata TAR gốc, detector, phiên bản OpenCV, quy tắc crop và số khung.
Khi runtime đổi, chạy lại cell 1, 2 và 4. Với runtime đang dở từ bản cũ,
có thể chạy lại cell 2 và 4 của bản mới sau khi mount Drive. TAR đủ byte
và cùng mtime được dùng lại. Lưu ZIP riêng trong Drive cá nhân được phép
chứa dữ liệu OULU-NPU.

Nếu cần train trước, đặt `BACKUP_RGB = False` ở cell 4, rồi chạy lại cell
với `True` để lưu trước khi xóa runtime. Cell kiểm manifest đã chuẩn bị
trước khi quyết định có cần đọc lại TAR hay không.

Nếu Dev lỗi, chạy lại cell 4 sau khi xử lý lỗi gốc. Train đủ 9.600 khung
được giữ và crop Dev hoàn chỉnh được dùng tiếp. Chạy cell 5 khi Dev đủ
7.200 khung. Gửi traceback gốc trong `logs` nếu một video vẫn thiếu tám
crop hợp lệ.

Mốc kiểm thử là số video/khung, độ phủ crop, log thời gian/VRAM, checkpoint
và bộ chỉ số Test. Test thật và tốc độ A100 cần được xác nhận trên Colab.

## Tiếp tục chuẩn bị CDCN với PRNet

Dùng [notebook Train/Dev đầy đủ](../notebooks/Face_PAD_OULU_NPU_CDCN_PRNet_Full_Train_Dev.ipynb).
Nếu ổ Drive gắn vào Colab báo `Errno 107`, đặt `REMOUNT_DRIVE = True` ở
cell 1 rồi chạy lại cell 1–3. Nếu runtime vẫn báo lỗi khi mount lại, kết nối
runtime CPU mới và chạy cell 1–3. Giữ thư mục `full-cache` trên Drive.

Cell 3 in `FULL_CACHE` và `CACHE_ZIPS` trước khi cài môi trường PRNet.
Các số này đếm tệp. Khi khôi phục, notebook chép từng ZIP về đĩa runtime
rồi mới mở và kiểm nội dung. Thư mục tạm của mỗi ZIP được dọn sau lần đọc.
Nếu bản sao thất bại do mất kết nối, log ghi đường dẫn ZIP đang chép.
Đường dẫn cache cũ được giữ với đúng cặp mã băm bộ tiền xử lý tương thích.
Nếu Train đã có 1.200 ZIP, có thể đặt
`SPLITS = ["Dev"]` để tiếp tục riêng Dev. Trước khi train, khôi phục cả
hai tập trên runtime A100 và kiểm cell 3 báo đủ 36.000 khung.

Mỗi tiến trình con ghi log vào `/content/cdcn-prnet-full/logs/<run>`
rồi chép một lần lên Drive sau khi kết thúc. Nếu Drive mất kết nối,
tải log cục bộ về trước khi xóa runtime. Các ZIP hoàn tất vẫn được tìm
trong cùng khóa cache khi chạy lại với cùng dữ liệu và bộ tiền xử lý.

Cell 4 lưu `resume.pt` sau mỗi `CHECKPOINT_EVERY = 5` epoch và ở epoch
cuối. Dòng `RECOVERY_CHECKPOINT` ghi số epoch đã lưu cùng đường dẫn.
Tệp phục hồi lưu trọng số, trạng thái Adam, lịch tốc độ học, bộ sinh số
ngẫu nhiên và lịch sử loss. Mỗi lần lưu thay thế mốc phục hồi trước của
cùng lượt. Nếu không chép được lên Drive, lỗi ghi đường dẫn bản lưu trên
runtime.

Để dừng thủ công, chờ dòng `RECOVERY_CHECKPOINT` rồi dừng cell 4.
Khi chạy lại, dán đường dẫn `resume.pt` vào `RESUME_CHECKPOINT` ở cell 4.
Đặt `EPOCHS` bằng số epoch đã lưu nếu chỉ cần chấm Dev tại mốc đó, hoặc
đặt cao hơn để huấn luyện tiếp tới tổng số epoch mong muốn. Giữ seed,
batch, số worker và manifest dữ liệu của lượt gốc. Trên runtime mới, chạy
lại cell 1–3 trước khi chạy cell 4. Kết quả của lần chấm Dev được lưu trong
thư mục lượt mới, gồm `checkpoint.pt`, `dev_scores.csv` và `pilot_result.json`.

### Chấm Test Protocol 1 với checkpoint 100 epoch

Lượt seed 43, batch 56 đạt ACER gộp 1,04% trên 900 video Dev. Lượt 50
epoch đạt 10,35% trên cùng Dev. Chọn checkpoint 100 epoch và khóa ngưỡng
Dev `0.0007160214008763433` trước khi chuẩn bị Test.

1. Mở [notebook Test](../notebooks/Face_PAD_OULU_NPU_CDCN_PRNet_Locked_Test.ipynb).
   Chạy cell 1–3 trên CPU. Cell 3 kiểm SHA-256 của checkpoint và protocol,
   rồi dựng 4.800 khung bằng MTCNN và PRNet cho đúng 600 video Test chính
   thức. ZIP theo video nằm trong `test-cache` trên Drive. Có thể chạy lại
   cell 1–3 để tiếp tục từ các video còn thiếu.
2. Khi thấy `TEST_DATA_READY`, chuyển sang GPU, chạy lại cell 1–3 để khôi
   phục cache rồi chạy cell 4. Cell 4 dùng chung phép tính điểm theo video
   với Dev. Video có điểm lớn hơn ngưỡng được nhận là thật.
3. Tìm đường dẫn `CDCN_LOCKED_TEST_READY`. Drive lưu `test_lock.json`,
   `test_scores.csv` và `test_metrics.json` dưới `locked-test-p1`. JSON
   ghi số lỗi, APCER gộp, BPCER, ACER và dấu vân tay của dữ liệu và mô hình.

Kết quả Test của cấu hình này đang chờ lượt chấm trên Colab.

Cell 3 mặc định đặt `PREP_WORKERS = 0` để chọn tối đa bốn tiến trình
theo vCPU và RAM còn trống. Mỗi tiến trình dùng cấu hình MTCNN và PRNet
của lượt tuần tự. Trước khi chạy song song, cell dựng cùng hai video
bằng hai cách trên cùng runtime. Cell so frame ID, bbox, pixel RGB đã
crop và map độ sâu 32 × 32 cùng tổng map. Nếu có ZIP cũ, cell so thêm
với dữ liệu đã lưu. Dòng `PARALLEL_NUMERIC_MATCH` xác nhận hai video
kiểm tra trùng nhau. Khi có sai khác, cell báo rõ trường bị lệch và
dừng trước khi ghi video mới. Hai video kiểm tra giúp phát hiện sai
khác sớm. Muốn chứng minh trùng từng khung cho cả tập cần đối chiếu cả tập.

Dòng `PREP_WORKERS` báo số tiến trình thực tế. Tiến trình chính ghi từng
ZIP hoàn tất và in số video cùng ETA. Khi đổi notebook, dừng cell 3 cũ
trước rồi mở bản mới trong cùng runtime nếu có thể để dùng lại TAR và
các ZIP. Đặt `START_FRESH = True` khi chủ động dựng lại toàn bộ Test
trong cache riêng. Checkpoint và ngưỡng Dev tiếp tục dùng bản đã khóa.


## Các nghiên cứu tiếp theo

- E1 dự đoán bản đồ giả độ sâu từ 3DDFA V2 cho mặt thật. E2 thêm đầu
  phân loại trên backbone E1. E3 huấn luyện chung với BCE. E3b/E4 dùng
  cùng lịch độ sâu → head → joint, với BCE hoặc Focal. Lượt nhanh trên
  chỉ đo MobileNet. Muốn chạy nhánh độ sâu cần tạo target riêng cho
  Train/Dev OULU bằng worker 3DDFA V2 của repo và kiểm độ phủ target.
- Khi kiểm tác dụng đầu phân loại, dùng cùng checkpoint E1 theo seed
  để tiếp tục E1 và để bắt đầu E3. Giữ cùng ảnh, batch, số cập nhật,
  Adam, LR, weight decay và quy tắc chọn checkpoint. Khi kiểm Focal,
  ghép E3b/E4 theo seed và giữ cùng lịch. So trên Dev trước khi khóa Test.
- Một câu hỏi mới ít tốn compute là giữ cùng checkpoint và so cách
  tổng hợp điểm video theo mean và median trên Dev. Sau khi chốt quy
  tắc, thử trên Protocol 2 để xem lỗi thay đổi khi máy in và màn hình
  chuyển sang thiết bị mới.

Tham chiếu thiết kế: [Kassis, Agarwal, He, Patel và Brueckner, Scientific Agent Skills, 2026](https://arxiv.org/abs/2609.00065).
