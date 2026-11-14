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

Ở thời điểm này đã đối chiếu nguồn và chạy lại bước tính chỉ số. Chưa
chạy training hoặc chấm điểm khung theo pipeline CDCN gốc.
