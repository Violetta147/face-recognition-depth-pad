# Kế hoạch thực nghiệm DeepFace-PAD trên OULU-NPU

**Ưu tiên hiện tại: tái lập CDCN CVPR 2020 trên Protocol 1.** Mốc của
CDCN là ACER 1,0% ở Bảng 4. Trước khi lặp cặp E1–E3, đọc
[đối chiếu paper và mã CDCN công khai](CDCN_CVPR2020_OULU_P1.md) để xác
minh bộ asset tiền xử lý, checkpoint và cấu hình cần cho lượt tái lập.

Cập nhật ngày 14/11/2026. **Điểm bắt đầu khi quay lại: khôi phục cache RGB Train/Dev và chạy thử tạo pseudo-depth trên một nhóm nhỏ.** Kế hoạch này ghi các bước dự kiến. Lượt thực nghiệm đã hoàn tất hiện là MobileNetV3-Small trên Protocol 1, seed 43.

**Notebook cho bước 1–2**: [Face_PAD_OULU_NPU_Depth_Smoke.ipynb](../notebooks/Face_PAD_OULU_NPU_Depth_Smoke.ipynb). Chọn CPU và chạy cell 1–4, rồi xem RGB và map ở cell 5. Notebook chỉ đọc 16 ảnh mỗi split trực tiếp từ ZIP đã khóa. Mỗi split lấy 12 ảnh thật từ sáu camera × hai phiên và bốn ảnh tấn công, mỗi thiết bị tạo mẫu một ảnh. Bước lấy mẫu đã kiểm bằng ZIP thật. Việc dựng map bằng 3DDFA V2 vẫn cần chạy trên Colab.

Cell 4 cần in `DEPTH_SMOKE_PASS` với 24 map thật và 8 map zero trước khi
ước lượng lượt đầy đủ. Gửi `smoke_summary.json` trong
`MyDrive/face-pad/oulu-fast-p1/depth-smoke/p1-32-v1` và nhận xét ảnh ở cell 5.
Nếu có lỗi, gửi traceback và `failures.csv` nếu file đã được tạo. Notebook
cố định commit 3DDFA V2 đã dùng ở CASIA và dùng ONNX trên CPU.

**Smoke đã đạt trên Colab CPU** với 24/24 map thật, 8/8 target zero và
0 lỗi. Hai map thật trong ảnh xem trước hiện rõ cấu trúc mặt, còn hai
mẫu print có target zero theo thiết kế. Worker mất 14,0 giây, gồm cả
xuất ONNX. Log dựng 24 map báo khoảng 1 giây, chưa đủ để dự đoán chính
xác runtime đầy đủ vì ledger lớn hơn và có thời gian lưu snapshot.

**Tiếp theo chạy bước 3** bằng [notebook Depth Full](../notebooks/Face_PAD_OULU_NPU_Depth_Full.ipynb).
Chọn CPU. Ưu tiên phiên smoke còn mở để giữ nguyên ba tài sản ONNX đã xuất.
Notebook kiểm đúng hash RGB và tài sản 3DDFA V2, lưu bản ONNX đã xác minh
lên Drive, rồi ghi snapshot mỗi 500 map thật. Thư mục đầu ra là
`MyDrive/face-pad/oulu-fast-p1/depth-full/p1-v1`. Lượt đầy đủ đạt khi cell
5 in `DEPTH_FULL_PASS` với 16.800 target, gồm 3.360 thật và 13.440 tấn
công. Nếu thất bại, giữ `depth-progress.zip`, xem `failures.csv` và
log worker để xử lý các ID lỗi trước khi train E1.

**Depth Full đã đạt trên Colab CPU.** Đã đối chiếu `depth_summary.json`
trên Drive: đủ 16.800 target (3.360 thật, 13.440 zero), audit hợp lệ.
Log ghi 879 giây cho bước dựng và lưu snapshot từng nhóm, chưa gồm
khôi phục RGB và kiểm cuối. ZIP chốt `depth-final.zip` có SHA-256
`fda2b58e871258906ce7c006e00880fb7d22dcf80aa80480c1992f8724ebc935`.

**Tiếp theo chạy E1** bằng [notebook E1 CDCN](../notebooks/Face_PAD_OULU_NPU_E1_CDCN.ipynb)
trên Colab A100. Chạy cell 1–3 để kiểm dữ liệu và chọn batch 8 hoặc 16
theo tốc độ đo được. Cell 4 chạy seed 43, BF16, ảnh 256 × 256, Adam
(LR 0,0001, weight decay 0,00005) trong 5 epoch. Đây là mốc khởi tạo
OULU cho đối chứng E1–E3. Mỗi epoch chọn theo ACER video trên Dev;
ngưỡng lấy gần EER trên Dev. Khi thấy `E1_DEV_READY`, gửi đường dẫn
run và `metrics.json`; kiểm `e1_dev_lock.json` trước khi dùng checkpoint
cho đối chứng. Notebook này chỉ sử dụng Train/Dev.

**E1 đã hoàn tất.** A100 40 GB, batch 16, 5 epoch × 600 bước, tổng
465 giây cho phiên Train/Dev. Epoch 5 đạt ACER Dev 2,92%, BPCER 5/180,
APCER in 9/360 và phát lại 11/360. Ngưỡng Dev 0,10381030. Đã đối chiếu
SHA-256 của tám file trong `e1_dev_lock.json` trên Drive.

**Tiếp theo dùng [notebook E1–E3](../notebooks/Face_PAD_OULU_NPU_E1_E3_Pair.ipynb).**
Hai nhánh đều nạp trọng số E1 epoch 5 và khởi tạo Adam mới. Mỗi nhánh
thêm 3.000 bước với batch 16, BF16, LR 0,0001, weight decay 0,00005, cùng
seed cho loader và tiêu chí ACER video trên Dev. E3 thêm đầu phân loại
với BCE hệ số 1. Kết quả đo tác động phối hợp của đầu phân loại và mục
tiêu BCE, còn E2 là đối chứng riêng cho tác dụng đọc điểm.
Khi thấy `PAIR_DEV_READY`, gửi JSON Dev và đường dẫn lock. Khi đổi runtime
có thể điền `RESUME_PAIR` để bỏ qua nhánh đã hoàn tất; nhánh dở chạy lại
từ checkpoint chung. So Test dùng bước đánh giá riêng sau khi khóa cặp.

**Cặp seed 43 đã khóa Dev.** E1 tiếp tục chọn epoch 2, ACER 1,25%.
E3 chọn epoch 4, ACER 1,11%. Mỗi nhánh từ chối nhầm 2/180 video thật.
E1 cho lọt 3 video in và 5 video phát lại. E3 cho lọt 4 video ở mỗi nhóm.
Hai nhánh cùng cho lọt 8/720 video tấn công. Chênh ACER đến từ tỷ lệ
lỗi của nhóm tấn công cao nhất giảm ở E3.

Dán [cell chấm Test](../scripts/oulu_pair_test_colab_cell.py) vào cuối
notebook E1–E3 đang mở, sau dòng `PAIR_DEV_READY`. Nếu đã đổi runtime,
chạy lại phần thiết lập cell 1–2 trước để nạp mã và đường dẫn.
Cell dùng ZIP Test RGB đã lưu, kiểm hash của khóa và các tệp run,
rồi chấm 600 video bằng ngưỡng Dev của từng checkpoint. Kết quả ghi
vào `locked-test` bên dưới thư mục cặp. Test Protocol 1 đã được quan sát
ở lượt MobileNet, nên ghi kết quả này như so sánh phát triển trên một seed.

**Test của cặp seed 43 đã hoàn tất.** Hai run chấm cùng 600 video,
dùng ngưỡng Dev đã khóa. Đã đối chiếu JSON, khóa và điểm theo video trên
Drive tại `cdcn-pair-p1/seed43-1794667766717400448/locked-test`.

| Chỉ số Test | E1 tiếp tục | E3 joint BCE |
| --- | ---: | ---: |
| ACER | 13,33% | 7,08% |
| BPCER | 24,17% (29/120) | 10,83% (13/120) |
| APCER in | 2,50% (6/240) | 2,08% (5/240) |
| APCER phát lại | 1,67% (4/240) | 3,33% (8/240) |
| APCER chung (nhóm cao nhất) | 2,50% | 3,33% |
| AUC | 0,9651 | 0,9852 |
| EER | 10,00% | 6,67% |

Ở seed 43, E3 nhận đúng thêm 16 video thật từng bị E1 từ chối.
E3 cũng chặn thêm 4 video tấn công từng lọt qua và để lọt 7 video
tấn công từng bị E1 chặn. ACER giảm 6,25 điểm phần trăm trong khi
APCER chung tăng 0,83 điểm phần trăm. Lượt tiếp theo ưu tiên lặp đối
chứng với seed 44/45, mỗi seed dùng checkpoint E1 khởi tạo của chính nó.

## Mốc kết quả đã khóa

| Hạng mục | Giá trị |
| --- | --- |
| Train / Dev / Test | 1.200 / 900 / 600 video, 8 khung/video, tách theo người |
| Mô hình | MobileNetV3-Small khởi tạo từ ImageNet, BCE, AdamW |
| Cấu hình đã chạy | A100 80 GB, BF16, batch 128, LR 0,0003, 3 epoch, 75 bước cập nhật/epoch |
| Chọn checkpoint và ngưỡng | Epoch 3, ngưỡng 0,45529577 từ Dev, điểm video là trung bình điểm các khung |
| Dev | ACER 1,25%, từ chối nhầm 2/180 video thật |
| Test | ACER 16,25%, từ chối nhầm 38/120 video thật (BPCER 31,67%) |
| Tấn công lọt qua trên Test | In 1/240 (0,42%), phát lại 2/240 (0,83%). APCER chung lấy tỷ lệ cao hơn |
| Chỉ số bổ sung trên Test | AUC 0,9790, EER 6,77% |

**Câu hỏi tiếp theo:** mô hình dự đoán độ sâu và đầu phân loại có giúp giảm từ chối nhầm người thật ở phiên quay khác trong khi giữ tỷ lệ lọt của từng loại tấn công ở mức thấp không? Kết quả MobileNet mới có một seed. Test Protocol 1 đã được xem, nên các phép so sánh tiếp theo trên tập này là bằng chứng phát triển. Mọi quyết định chọn checkpoint, ngưỡng và cấu hình cho lượt mới dựa trên Train/Dev.

- [Thư mục run đã khóa trên Drive](https://drive.google.com/drive/folders/1RWkKGFNrKqfIFnCJ6DWKjXS7Oy-RSEDJ)
- [Ba ZIP cache RGB trên Drive](https://drive.google.com/drive/folders/1oQMEbg0Bh_rRrplUWTqAVff75Jq5PKbh). Đã kiểm tên và kích thước sau khi Colab ghi file.
- [Notebook đã chạy](../notebooks/Face_PAD_OULU_NPU_A100_Executed.ipynb). Bản lưu cục bộ có cả lỗi crop Dev ban đầu và kết quả cuối.

## Thứ tự triển khai

| Bước | Việc cần làm | Đầu ra để đi tiếp |
| --- | --- | --- |
| 1. Khôi phục RGB | Mở [notebook sạch](../notebooks/Face_PAD_OULU_NPU_A100.ipynb), chạy cell 1, 2 và 4 để khôi phục/cache đúng cấu hình. Kiểm tra Train 9.600 và Dev 7.200 khung, cùng SHA-256 của manifest và ảnh. | Hai split sẵn sàng. Nếu Colab báo cache khác phiên bản, kiểm tra phiên bản OpenCV và thông tin trong ZIP trước khi chép lại TAR. |
| 2. Kiểm tra pseudo-depth | Chuẩn bị notebook gọi worker 3DDFA V2 hiện có. Chạy một nhóm nhỏ ảnh người thật từ Train/Dev, lấy mẫu qua vài camera và phiên quay. Kiểm tra kích thước 32 × 32, giá trị hữu hạn, bản đồ thật có biến thiên và target attack bằng 0. Kiểm tra trực quan vài cặp RGB/target và ghi thời gian. | Log smoke, độ phủ và lỗi theo mẫu, cùng cấu hình worker và hash tài sản. Dùng tốc độ đã đo để ước lượng thời gian xử lý đủ. |
| 3. Tạo pseudo-depth đầy đủ | Tạo target cho Train/Dev theo nhóm và lưu snapshot ra Drive, rồi thử khôi phục một snapshot. Tổng đầu vào theo manifest hiện tại là 3.360 khung người thật cần dựng và 13.440 khung tấn công có target bằng 0. Rà lỗi dựng mặt trước khi train. | Manifest có depth và preflight đạt. Snapshot có map, ledger, hàng đợi, provenance và đối chiếu hash RGB, cấu hình, trọng số. [Hướng dẫn cache](COLAB_PROGRESS_AND_CACHE.md) |
| 4. Đo E1 rồi đối chứng E1–E3 | Train E1 (CDCN đọc điểm bằng trung bình bản đồ độ sâu) một seed 43. Từ cùng checkpoint E1, so sánh **E1 tiếp tục học độ sâu** với **E3 học chung độ sâu và phân loại BCE**. Giữ cùng dữ liệu, seed, số bước cập nhật thêm, batch, optimizer, LR, weight decay và quy tắc chọn theo PAD trên Dev. | Có log số bước thực tế, checkpoint, điểm video và chỉ số Dev của hai nhánh. Thêm E2, chỉ học đầu phân loại trên backbone khóa, nếu cần tách tác dụng đọc điểm khỏi việc cập nhật backbone. |
| 5. So BCE–Focal | Ưu tiên sau khi E1–E3 chạy ổn. So E3b và E4 với cùng checkpoint khởi tạo và cùng lịch depth → head → joint. Hai nhánh dùng một quy tắc chọn checkpoint và ngưỡng. Với Focal, ghi rõ alpha, gamma và hệ số loss. | So sánh được tác động của thay đổi loss phân loại trong cùng lịch. Sau lượt đầu, dự kiến chạy cặp seed 44 và 45 cho đối chứng chính nếu còn ngân sách. |
| 6. Mở rộng đánh giá | Khóa danh sách run, checkpoint và ngưỡng từ Dev trước khi chấm Test. Nếu muốn thử thêm một thay đổi rẻ, so mean với median khi gộp khung trên Dev bằng cùng checkpoint. Sau đó chạy Protocol 2 nếu câu hỏi là độ bền trước máy in và màn hình khác. | Kết quả theo protocol và theo seed, kèm số video lỗi. Protocol 2 có thể trùng video hoặc người với nguồn đã quan sát ở Protocol 1. |

## Quy tắc cho lần chạy mới

- Dùng video làm đơn vị đánh giá. Báo BPCER, APCER print, APCER replay, APCER chung và ACER, kèm tử số/mẫu số. Báo thêm AUC và EER để phân biệt chất lượng xếp hạng với lỗi tại ngưỡng đã khóa. Nếu mô hình giảm BPCER nhưng tăng APCER, trình bày cả hai thay đổi.
- Chạy thử vài batch CDCN trên GPU thực tế để chốt batch và precision. Batch 128 đã đo cho MobileNetV3-Small. Với hai nhánh cần đối chứng, dùng chung cấu hình đã chốt và ghi số cập nhật cùng thời gian. Giữ riêng thời gian khôi phục cache, dựng depth, train và chấm.
- Nếu một video hoặc map lỗi, lưu đúng ID và traceback, dùng lại phần cache đã hoàn tất rồi chạy lại phần lỗi. Rà lại bất kỳ thay đổi nào về số khung, nội dung ảnh hoặc cấu hình dựng depth trước khi tiếp tục từ cache.

Tham chiếu thiết kế thí nghiệm và triển khai [hướng dẫn OULU-NPU của dự án](OULU_NPU.md), [bàn giao BCE–Focal của CASIA](reviews/defense_readthrough_20261114/CHON_E3_VA_FOCAL.md) và [Kassis và cộng sự, Scientific Agent Skills (2026)](https://arxiv.org/abs/2609.00065).
