# Lượt 4: learned head trên Official CDCN đã đóng băng

## Phạm vi báo cáo ngày mai

E1 đã tái lập kiến trúc/loss CDCN của tác giả dưới protocol CASIA phát triển
của nhóm. Đây chưa phải tái lập toàn bộ pipeline hay số benchmark của paper.
Tác giả có công bố `train_CDCN.py`; không giải thích lựa chọn protocol của nhóm
bằng khẳng định tác giả không công bố mã train hoặc toàn bộ xử lý dữ liệu.

E2 chỉ thử cách đọc predicted depth map. E2 không phải UCDCN, CDCN++ hay SOTA;
learned classifier và staged training đã có tiền lệ trong UCDCN 2024.

## Thiết kế

- E1 đối chứng: `CASIA_E1_CDCN_OFFICIAL_seed42_20260921T114029Z`.
- Nạp đúng `best.ckpt` của run này vào `OfficialCDCNWithDepthHead.backbone`.
- Khóa toàn bộ trọng số và thống kê BatchNorm; depth map không đổi sau train head.
- Head: Conv 1→8→16, ReLU, global average pooling, Linear 16→1; BCE với live=1.
- Train head 10 epoch, Adam lr=0.001; chọn checkpoint bằng validation BCE.
- Giữ manifest, frame sampling, image size 256, normalization official,
  horizontal flip train và video aggregation mean của E1.
- Ngưỡng E2 chọn riêng bằng cùng hàm validation như E1; không dùng cùng giá trị
  ngưỡng vì mean-depth score và sigmoid head có thang điểm khác nhau.

Config thực chạy: `configs/casia_e2_official_head_frozen.yaml`.
Config `configs/e2_head_frozen.yaml` là template legacy cho pilot,
không dùng để so với Official E1.

## Bằng chứng cần có trước khi gọi hoàn tất

1. Checkpoint nạp đúng; mọi tensor và BatchNorm buffer backbone giữ nguyên.
2. Cùng checksum manifest với E1 và cùng preprocessing/evaluation.
3. Train/validation BCE curve, checkpoint tốt nhất, threshold từ validation.
4. Bảng video-level APCER, BPCER, ACER, EER và AUC E1–E2.
5. Params và latency batch=1, cùng máy, input và warmup, CUDA synchronize.
6. Danh sách video E2 sửa được, làm sai thêm và vẫn sai so với E1.

CASIA test đã được xem ở Lượt 3. Kết quả E2 trên tập này là so sánh phát triển
có test đã mở, không phải một xác nhận độc lập mới. Chốt cấu hình/epoch/ngưỡng
bằng validation trước khi xem E2 test; không điều chỉnh để thắng E1 trên test.
Benchmark độc lập và nhiều seed vẫn cần cho kết luận cuối.

## Cách giải thích với thầy

“Nhóm đã tái lập CDCN trong cùng điều kiện thí nghiệm để làm đối chứng.
Lượt 4 giữ nguyên checkpoint và predicted depth, chỉ học bộ phân loại nhỏ.
Thí nghiệm đo tác động của cách đọc map bằng metric PAD ở mức video và chi phí
suy luận. Kết quả chỉ kết luận trong protocol này; chưa tuyên bố SOTA.”

## Nguồn

- CDCN và mã train: https://github.com/ZitongYu/CDCN/blob/master/CVPR2020_paper_codes/train_CDCN.py
- UCDCN: https://link.springer.com/article/10.1007/s40747-024-01397-0

## Trạng thái

Đã chuẩn bị implementation, config và kiểm thử. Chưa có kết quả train E2 thực
trên CASIA; chỉ điền bảng bằng artifact từ run thực, không suy đoán improvement.
