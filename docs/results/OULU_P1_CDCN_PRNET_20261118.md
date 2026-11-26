# CDCN và PRNet trên OULU-NPU Protocol 1

Lượt chấm Test hoàn tất ngày 18/11/2026. Ngày 22/11/2026 đã đọc lại
JSON và CSV gốc trên Drive, đối chiếu SHA-256, danh sách video và tính
lại chỉ số bằng `scripts/audit_cdcn_prnet_locked_result.py`.

## Kết quả đã xác minh

| Tập | Video thật | Video giả | APCER gộp | BPCER | ACER gộp |
| --- | ---: | ---: | ---: | ---: | ---: |
| Dev | 180 | 720 | 0,97% (7 video) | 1,11% (2 video) | 1,04% |
| Test | 120 | 480 | 3,33% (16 video) | 10,00% (12 video) | 6,67% |

Ngưỡng `0.0007160214008763433` được lấy từ Dev và khóa trước lượt
Test này. Video được nhận là thật khi score lớn hơn ngưỡng. AUC tính
từ CSV đạt 0,999475 trên Dev và 0,985260 trên Test. Chênh lệch ACER
Dev–Test là 5,625 điểm phần trăm.

Lượt này dùng seed 43, batch 56, CDCN θ = 0,7, Adam và 100 epoch.
Mỗi video Train có pool 24 khung, mỗi epoch chọn một khung. Dev và
Test lấy tám khung mỗi video. Điểm video là trung bình các tỷ số giữa
tổng depth dự đoán và tổng map PRNet đã crop của từng khung.

Tập Test gồm đủ 600 ID chính thức, tách người với Train và Dev.
Lượt chấm trên A100 80 GB mất 88,713 giây. Test của Protocol 1 đã được
quan sát ở các thử nghiệm trước, nên ghi rõ lịch sử phát triển khi
trình bày các thực nghiệm tiếp theo.

## Lỗi ở ngưỡng đã khóa

| Loại video Test | Số video | Số lỗi | Tỷ lệ lỗi |
| --- | ---: | ---: | ---: |
| Người thật | 120 | 12 bị từ chối | 10,00% |
| Ảnh in loại 1, access 2 | 120 | 2 lọt qua | 1,67% |
| Ảnh in loại 2, access 3 | 120 | 9 lọt qua | 7,50% |
| Phát lại loại 1, access 4 | 120 | 3 lọt qua | 2,50% |
| Phát lại loại 2, access 5 | 120 | 2 lọt qua | 1,67% |

Gộp hai loại ảnh in cho 11 lỗi trong 240 video, tương ứng 4,58%.
Gộp hai loại phát lại cho 5 lỗi trong 240 video, tương ứng 2,08%.
APCER gộp toàn bộ 480 video là chỉ số dùng trong bảng kết quả chính.
Các lượt E1–E3 cũ còn có báo cáo APCER lấy nhóm cao nhất, nên phải
kiểm quy tắc tính trước khi so các bảng.

| Điện thoại | Người thật bị từ chối trên 20 video | Video giả lọt qua trên 80 video |
| --- | ---: | ---: |
| 1 | 3 | 2 |
| 2 | 0 | 7 |
| 3 | 4 | 1 |
| 4 | 2 | 2 |
| 5 | 1 | 3 |
| 6 | 2 | 1 |

Bảng mô tả vị trí các lỗi đã xảy ra. Nguyên nhân của từng lỗi cần
được kiểm bằng ảnh, bbox, map PRNet và đầu ra mô hình tương ứng.

## Nguồn và dấu vân tay

- [Thư mục kết quả Test](https://drive.google.com/drive/folders/1q2N_N7PTBmHwwW-7_pT6q1Kbnk7WcBsX).
- [CSV Test](https://drive.google.com/file/d/13bfmU753ZS1SF3GMfH51SXKN7RzwEmf7/view).
- [JSON Test](https://drive.google.com/file/d/1E1l479B-xEREbe2lqZbVRQB5YftfnsFE/view).
- [Khóa Test](https://drive.google.com/file/d/1dmDzlzIU1hlEUR3oY4OTbjpPnYWW0bIk/view).
- [Lượt Train và Dev epoch 100](https://drive.google.com/drive/folders/13foE4b4Gc0aHHYfm-YFPXyyLndiK72GN).

| Tệp hoặc tài sản | SHA-256 |
| --- | --- |
| Checkpoint khóa | `ec0a3ecc6828cedc7bfb34c87affabe7b8469fbc8b33a40cf1a7cadedbbe0497` |
| Báo cáo Dev | `0611fa499d38ff84d5e02b38865cd5e57c148f83e3cf086254e4f6815babcc18` |
| CSV Test | `3fb5827bc5e2f7c64402930b01afb36f6a2260fe51714e82f0f6ee512c25e1e4` |
| Manifest Train và Dev | `5fb7ca14a195e4fd6347475574519e4f1c59f79fda5890b9ee833a1586a4357d` |
| Manifest Test | `3039bbbc4add68ede678ca6c7099d1c034462f390f305ba9dac312d40e07fa6f` |

Hai mã hash của báo cáo Dev và CSV Test đã được tính lại từ bản tải
về. Hash checkpoint và manifest được đối chiếu giữa các bản ghi đã
khóa. Lần kiểm tra ngày 22/11 chưa tải lại checkpoint hoặc toàn bộ
asset ảnh để băm lại.

Cache Test đã dùng có khóa `0b7b46e9586477eb911e`, đủ 600 ZIP.
Bước chuẩn bị mới đã so khớp hai video mẫu khi chạy tuần tự và song
song trên cùng runtime. Cache cũ 198 video từng phát hiện lệch tổng
map ở một khung mẫu khi dựng lại trên runtime khác. Mức lệch và nguyên
nhân chưa được đo. Cache mới được dựng riêng cho lượt Test này.

Tệp kiểm tra cục bộ nằm ở `outputs/oulu_prnet_p1_20261122`, gồm bản
sao nguồn, `audit.json`, CSV lỗi và các bảng theo điện thoại, loại
tấn công, người. Thư mục này được giữ ngoài Git. Có thể tính lại bằng

```powershell
$env:PYTHONPATH = 'src'
python scripts/audit_cdcn_prnet_locked_result.py --source outputs/oulu_prnet_p1_20261122/source --output outputs/oulu_prnet_p1_20261122/audit
```

## Đối chiếu paper và lượt tiếp theo

Bảng 4 của paper báo CDCN đạt APCER 0,4%, BPCER 1,7% và ACER 1,0%
trên Protocol 1. Lượt hiện tại còn cách mốc ACER đó 5,67 điểm phần
trăm. Paper cho phép tối đa 1.300 epoch, giảm LR một nửa sau mỗi 500
epoch. Lượt hiện tại mới dừng ở 100 epoch. [Paper, mục 4.2 và Bảng 4](https://arxiv.org/html/2003.04092#S4).

Cấu hình dựng lại còn khác bộ asset tiền xử lý của tác giả, pool Train
24 khung và một GPU thay cho tám GPU. Ảnh hưởng riêng của mỗi khác
biệt chưa được đo. [Đối chiếu nguồn và các quyết định tái lập](../CDCN_CVPR2020_OULU_P1.md).

Lượt tiếp theo đã được chuẩn bị trong
[notebook tiếp tục Train và Dev](../../notebooks/Face_PAD_OULU_NPU_CDCN_PRNet_Continue_Train_Dev.ipynb).
Nó khôi phục trạng thái epoch 100, train tới tổng 1.300 epoch và chấm
Dev tại mỗi mốc 50 epoch. Quy tắc chọn là ACER gộp Dev thấp nhất,
hòa giữ epoch sớm, gồm cả mốc 100. Cứ năm epoch lưu trạng thái phục hồi.
Lịch Dev 50 epoch và quy tắc chọn là quyết định của dự án.

[Notebook tiếp tục trên A100 40 GB hoặc 80 GB](https://drive.google.com/file/d/1Uu38sF-tfA7tAxG_q2-pCxyEZ3m7IloH/view)
được cập nhật theo [rà soát phần cứng ngày 26/11](../reviews/A100_CONTINUATION_20261126.md).

Ước lượng khoảng 6–7 giờ A100 cho 1.200 epoch bổ sung và 24 lượt Dev,
cộng khôi phục cache và lưu checkpoint. Notebook đã kiểm mã và kiểm
thử phục hồi cục bộ. Lượt huấn luyện dài này cần chạy trên Colab.
