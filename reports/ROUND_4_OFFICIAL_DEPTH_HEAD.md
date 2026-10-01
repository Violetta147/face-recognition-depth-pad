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
Config `configs/e2_head_frozen.yaml` hiện cũng dùng Official CDCN và yêu cầu
checkpoint Official E1; config CASIA ở trên giữ nguyên cấu hình của run đã báo cáo.

## Chạy trên Colab

Mở `notebooks/Face_PAD_Round4_Official_Frozen_Head.ipynb`, chọn GPU và chạy tuần tự.
Cell 0.2 yêu cầu `DeepFace-PAD-Round4-source.zip` chứa source đã commit khi tạo
notebook. ZIP dùng để tránh phụ thuộc việc code mới đã push lên GitHub hay chưa.
Không cần thay hoặc chạy lại notebook E1 đang có output.

Notebook khôi phục dataset/depth bằng các cell setup từ bản E1 đã commit,
kiểm tra checksum manifest khớp E1 và tái tính validation score E1 trước train.
Nó chạy smoke 1 epoch rồi full 10 epoch, kiểm tra backbone bất biến, khóa artifact,
score E2 test phát triển và xuất paired error analysis cùng params/latency.
Train loop dùng epoch/lr từ stage head; không yêu cầu các khóa joint-training
epoch/lr bên ngoài stage trong cấu hình E2.
Run hoàn tất cùng config được tái dùng khi chạy lại cell; run khác config không
được tự động xem là kết quả của thí nghiệm này.

Output nằm ở `/content/drive/MyDrive/face-pad/reports/<E2_RUN_ID>`.

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

Người dùng đã cung cấp log và sáu screenshot run E2 CASIA ngày 01/10/2026:
`CASIA_E2_CDCN_OFFICIAL_HEAD_FROZEN_seed42_20261001T155213Z`.
E2 cùng ACER 2,7778% và cùng năm live video sai như E1; frozen head chưa cải thiện
run này. Xem [báo cáo kết quả](CASIA_E2_OFFICIAL_HEAD_FROZEN_seed42_summary.md).
Các số hiện được đối chiếu từ output người dùng; raw CSV/JSON/checkpoint trên
Drive chưa được kiểm chứng độc lập trong workspace.

Kiểm thử local: 49 tests pass, gồm một run E2 synthetic 1 epoch đi hết train,
checkpoint, validation score và threshold. Test xác nhận mọi weight/BatchNorm
buffer của Official CDCN không đổi; đây không phải số đo PAD trên CASIA.
