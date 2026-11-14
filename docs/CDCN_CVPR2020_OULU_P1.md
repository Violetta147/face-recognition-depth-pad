# Đối chiếu và tái lập CDCN CVPR 2020 trên OULU-NPU Protocol 1

Mục tiêu trước mắt là dòng **CDCN, ACER 1,0%** trong Bảng 4 của Yu và
cộng sự. Dòng CDCN++ đạt 0,2% và dùng kiến trúc tìm kiếm cùng mô-đun
chú ý đa tỉ lệ. E1–E3 hiện tại là thử nghiệm kiến trúc CDCN trên pipeline
DeepFace-PAD. Điểm của các lượt đã chạy được giữ làm bằng chứng của đúng
cấu hình tương ứng. [Bản CVPR](https://openaccess.thecvf.com/content_CVPR_2020/html/Yu_Searching_Central_Difference_Convolutional_Networks_for_Face_Anti-Spoofing_CVPR_2020_paper.html) · [Mục 4.2 và Bảng 4](https://arxiv.org/html/2003.04092#S4).

| Chi tiết | Paper hoặc mã tác giả | Lượt DeepFace-PAD đã chạy |
| --- | --- | --- |
| Dữ liệu | OULU-NPU P1, Train/Dev/Test chính thức | Cùng danh sách P1 đã kiểm |
| Hộp mặt và target | MTCNN và PRNet. Loader đọc ảnh scene, bbox từng frame và ảnh PRNet. Map thật 32 × 32 và target attack bằng 0 | YuNet, tọa độ mắt dự phòng và 3DDFA V2 |
| Lấy frame và augmentation | Train lấy một frame ngẫu nhiên mỗi video mỗi epoch và thay đổi scale crop. Dev/Test lấy 8 frame theo bước `files_total // 10`, dịch sang frame kế nếu thiếu asset. Loader train còn có augmentation ảnh ngoài lật ngang | 8 frame cố định cho cả ba split, crop sẵn, lật ngang train |
| Huấn luyện | Paper ghi batch 56, Adam LR 0,0001, weight decay 0,00005, tối đa 1.300 epoch, LR giảm nửa mỗi 500 epoch | Batch 16, BF16, 5 epoch khởi tạo và thêm 5 epoch ở đối chứng |
| Mô hình | CDCN θ=0,7 cho mốc 1,0%. Script công khai mặc định chọn CDCN++ khi train từ đầu, batch 7, tối đa 1.400 epoch | E1 dùng CDCN θ=0,7. E3 thêm đầu học BCE |
| Điểm và chỉ số | Paper mô tả trung bình depth dự đoán. Script công khai chia tổng depth dự đoán cho tổng map PRNet đầu vào ở từng frame rồi lấy trung bình video. Evaluator công khai lấy điểm ROC Dev gần EER, quyết định live khi điểm lớn hơn ngưỡng, và gộp mọi attack khi tính APCER | E1 trung bình không gian của depth dự đoán. E3 dùng điểm sigmoid. Cách chấm đã khóa dùng APCER lớn nhất giữa print và replay |

Nguồn thực thi tại commit `fd8370e8f32bdd090a3552f5a1fe4c301fa99f2b`.
[Xác nhận MTCNN và PRNet của tác giả](https://github.com/ZitongYu/CDCN/issues/14) ·
[Loader train và Dev/Test](https://github.com/ZitongYu/CDCN/tree/fd8370e8f32bdd090a3552f5a1fe4c301fa99f2b/CVPR2020_paper_codes) ·
[Script train và chấm](https://github.com/ZitongYu/CDCN/blob/fd8370e8f32bdd090a3552f5a1fe4c301fa99f2b/CVPR2020_paper_codes/train_CDCN.py) ·
[Evaluator](https://github.com/ZitongYu/CDCN/blob/fd8370e8f32bdd090a3552f5a1fe4c301fa99f2b/CVPR2020_paper_codes/utils.py).

**Điểm cần xác nhận trước khi chạy đầy đủ.** Loader Dev/Test ghi chú nhị
phân hóa map, nhưng gọi `np.where` rồi bỏ giá trị trả về. Script dùng tổng
map được nạp, nên kết quả còn phụ thuộc giá trị thực tế của file PRNet
tác giả dùng. Paper và mặc định script cũng khác về batch, số epoch và
kiến trúc mặc định. Trong cây mã CDCN đã kiểm, chưa thấy snapshot của bộ
scene/bbox/map, checkpoint P1 hay cấu hình chính xác của dòng CDCN Bảng 4.
Tệp OULU nhận từ tác giả dataset có AVI, tọa độ mắt và danh sách protocol.
Các asset đó chưa đủ để khôi phục bộ tiền xử lý của tác giả CDCN.
[Mã Dev/Test](https://github.com/ZitongYu/CDCN/blob/fd8370e8f32bdd090a3552f5a1fe4c301fa99f2b/CVPR2020_paper_codes/Load_OULUNPU_valtest.py) ·
[Thảo luận về trọng số](https://github.com/ZitongYu/CDCN/issues/70).

## Kiểm riêng ảnh hưởng của cách chấm

Đã dùng `scripts/audit_cdc_n_p1_scores.py` để tính lại CSV Dev/Test của
cặp seed 43. Script dùng ROC của scikit-learn, ngưỡng Dev và APCER gộp
như mã công khai. Đầu vào vẫn là điểm video DeepFace-PAD đã lưu.

| Run | Ngưỡng từ Dev | APCER gộp Test | BPCER Test | ACER gộp Test |
| --- | ---: | ---: | ---: | ---: |
| E1 tiếp tục | 0,10356927 | 2,08% (10/480) | 25,00% (30/120) | 13,54% |
| E3 joint BCE | 0,15423261 | 2,92% (14/480) | 10,00% (12/120) | 6,46% |

Cách tính lại chỉ số và ngưỡng trên cùng điểm video vẫn để lại khoảng
cách lớn với 1,0%. Số liệu này chưa định lượng ảnh hưởng riêng của PRNet,
crop, cách tính điểm khung hoặc lịch huấn luyện. Có thể kiểm lại bằng
`python scripts/audit_cdc_n_p1_scores.py --dev <val_scores.csv> --test <test_scores.csv>`.

## Bước chạy tái lập

1. Ưu tiên xác minh checkpoint và bộ scene/bbox/PRNet của CDCN P1 từ tác
   giả CDCN. Nếu có, chấm lại checkpoint bằng loader và evaluator gốc trên
   Dev/Test để kiểm đúng biến thể, thứ tự frame, map dùng làm mẫu số và số
   lỗi video. Ghi commit, hash checkpoint, các asset và môi trường.
2. Nếu cần dựng dữ liệu từ AVI, tạo nhánh tiền xử lý MTCNN + PRNet và
   kiểm bằng mẫu nhỏ trước. Kiểm độ khớp RGB–bbox–depth, quy ước tọa độ
   và phạm vi giá trị PRNet, kể cả map dùng khi chấm attack. Ghi từng
   chi tiết nguồn tác giả chưa công bố như một quyết định tái lập.
3. Train CDCN θ=0,7 từ đầu, với loader và augmentation của tác giả. Dùng
   lịch paper làm cấu hình mục tiêu, ghi sai khác phần cứng và BatchNorm
   nếu chuyển từ tám GPU sang một A100. Khóa cách chọn checkpoint và
   ngưỡng từ Dev trước khi chấm Test. Báo APCER/BPCER/ACER của evaluator
   công khai và đếm video lỗi. So với dòng CDCN 1,0% trong Bảng 4.

## Chạy thử tiền xử lý MTCNN và PRNet

Mở [notebook Colab](../notebooks/Face_PAD_OULU_NPU_CDCN_PRNet_Smoke.ipynb),
chọn runtime CPU rồi chạy bốn cell theo thứ tự. Cell đầu mặc định đọc bộ
OULU-NPU trong `MyDrive/face-pad/datasets/OULU-NPU`. Lượt mặc định lấy
ba video mỗi tập Train và Dev của Protocol 1 từ điện thoại 1, phiên 1.
Mỗi tập lấy một video thật, một ảnh in và một video phát lại. Mỗi video
lấy ba vị trí trong tám vị trí theo bước lấy mẫu Dev của loader công khai.
`WIDE_SAMPLE=True` thêm ba video mỗi tập từ điện thoại 4, phiên 2.
Đọc trực tiếp TAR trên Drive có thể lâu khi video nằm sâu trong archive.

Notebook lưu log, `smoke_summary.json`, mã nguồn đi kèm và ZIP chứa ảnh
scene, hộp mặt `.dat` và depth JPEG vào thư mục riêng dưới
`MyDrive/face-pad/cdcn-prnet-smoke-p1`. Log báo mỗi video hoàn tất và
nhắc định kỳ khi đọc TAR hoặc dựng depth. Mã CLI giữ từng khung hoàn tất
trong `frames.jsonl` để kiểm tra nếu lượt chạy bị ngắt.

Đây là cấu hình tiền xử lý dựng từ nguồn công khai. MTCNN lấy hộp mặt
lớn nhất. PRNet dùng checkpoint của tác giả PRNet. Hàm dựng depth dùng
mã từ công trình liên quan của Wang và cộng sự với tùy chọn lọc trung vị.
Mẫu giữ map PRNet có giá trị dương cho cả video thật và video giả vì
loader Dev dùng tổng map khi tính điểm khung. Target train bằng 0 cho
video giả được ghi trong manifest. Điểm khác biệt cần xác minh là cách
chọn bbox, thiết lập lọc và phân bố giá trị map trong chính bộ dữ liệu
tiền xử lý của CDCN. [PRNet](https://github.com/yfeng95/PRNet) ·
[Mã dựng depth](https://github.com/clks-wzz/PRNet-Depth-Generation) ·
[Loader Dev của CDCN](https://github.com/ZitongYu/CDCN/blob/fd8370e8f32bdd090a3552f5a1fe4c301fa99f2b/CVPR2020_paper_codes/Load_OULUNPU_valtest.py).

Ảnh mẫu công khai của PRNet đã cho bbox hợp lệ và map có 47.136 pixel
khác 0, giá trị lớn nhất 254. Lượt CPU trên Windows ngày 14/11/2026 đã
xử lý đủ 18 khung từ sáu video OULU gốc, 9 khung mỗi tập Train và Dev.
Đọc lại JPEG và bbox của cả 18 khung cho thấy map 32 × 32 có tổng từ
95.545 đến 123.007. Một khung cần tính lại tổng vì làm tròn tọa độ crop
lệch một pixel. Mã hiện dùng đúng thứ tự phép tính của loader công khai.
ZIP đã đọc kiểm tra và lưu ở
`MyDrive/face-pad/cdcn-prnet-smoke-p1/windows-20261114-p1/oulu-18-frame-smoke.zip`
cùng JSON và log. SHA-256 của ZIP là
`d59685c21cb1624b4a002b10bb741c33513a7c4e0eeb9bff6e2e3ec6787e3074`.

Script này mới kiểm tiền xử lý. Mốc ACER 1,0% chỉ đánh giá được sau khi
train CDCN, chọn checkpoint và ngưỡng trên Dev rồi chấm Test theo quy
trình đã nêu.

## Lượt chạy thử Train/Dev

Mở [notebook CDCN Train/Dev](../notebooks/Face_PAD_OULU_NPU_CDCN_PRNet_Train_Pilot.ipynb)
trên Colab, chọn GPU A100 và chạy bốn cell. Bộ 48 khung từ sáu video
OULU gốc đã sẵn trên Drive trong
`MyDrive/face-pad/cdcn-prnet-train-pilot-p1/prepared-cache/c375c1dfc4bce1acc988`.
Cell 3 kiểm phiên bản mã tiền xử lý, SHA-256 của protocol, cỡ và hash
64 KiB đầu của hai TAR, rồi kiểm SHA-256 toàn ZIP trước khi giải nén.
Nếu cấu hình thay đổi, cell dựng lại các khung và lưu snapshot mới.
Cell 4 ghi checkpoint, `dev_scores.csv`, `pilot_result.json` và log
dưới `MyDrive/face-pad/cdcn-prnet-train-pilot-p1`.

CDCN θ=0,7 chạy FP32, ba epoch với batch 3, từ khởi tạo mới. Mỗi epoch
lấy ngẫu nhiên một trong tám khung đã lưu của mỗi video Train.
Ảnh được crop ngẫu nhiên ở các scale 1,2–1,4 và biến đổi màu, xóa
vùng ảnh, lật và cutout. Biến đổi màu dùng NumPy trong lượt pilot.
Video thật dùng depth chuẩn hóa về [0,1], video giả dùng target bằng 0.
Loss gồm depth MSE và contrast MSE. Dev chạy cả tám khung mỗi video. Với
mỗi khung, tổng depth dự đoán được chia cho tổng map PRNet đã crop và
lưu JPEG, rồi lấy trung bình các tỷ số theo video. Chỉ số dùng APCER
gộp và quy tắc lấy ngưỡng ROC của mã công khai khi có ngưỡng hữu hạn.
[Loader Train](https://github.com/ZitongYu/CDCN/blob/fd8370e8f32bdd090a3552f5a1fe4c301fa99f2b/CVPR2020_paper_codes/Load_OULUNPU_train.py) ·
[Script huấn luyện và chấm của tác giả](https://github.com/ZitongYu/CDCN/blob/fd8370e8f32bdd090a3552f5a1fe4c301fa99f2b/CVPR2020_paper_codes/train_CDCN.py).

Batch, số epoch và số video trên dành cho kiểm tra pipeline. Dev pilot
có một video thật và hai video giả. Khi chuyển sang lượt đầy đủ, cần
chuẩn bị tập khung Train lớn hơn để loader có thể lấy mẫu theo video,
đo thông lượng với batch thực tế, chốt tiêu chí chọn checkpoint trên
Dev đầy đủ rồi mới dùng Test để đối chiếu Bảng 4.

Lượt Windows CPU đã hoàn thành ba lần cập nhật, lưu và đọc lại
checkpoint, rồi chấm đủ 24 khung Dev. Train mất 87 giây, chấm Dev mất
55 giây. Tổng hai thành phần loss đi từ 0,2396 đến 0,1691. Điểm video
thật đứng cao nhất và trùng ngưỡng ROC. Quy tắc `score > threshold`
của tác giả loại video đó, cho APCER gộp 0%, BPCER 100% và ACER 50%
trên ba video. Checkpoint, điểm và log lưu trong
`MyDrive/face-pad/cdcn-prnet-train-pilot-p1/windows-cpu-pilot`.
Nhánh khôi phục của cell 3 đã chạy với bản sao ZIP Drive trên Windows.
Thời gian và VRAM của lượt A100 chờ log Colab.
