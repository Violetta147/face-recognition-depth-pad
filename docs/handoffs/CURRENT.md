# Bàn giao hiện tại của DeepFace-PAD

**Phạm vi cập nhật 26/11/2026.** Dự án nghiên cứu Face PAD. Xác thực sinh trắc học khuôn mặt là bối cảnh ứng dụng. [Quyết định phạm vi](../reviews/defense_readthrough_20261114/QUYET_DINH.md).

## Điểm tiếp tục hiện tại

OULU-NPU P1, CDCN–PRNet seed 43, batch 56, 100 epoch đã hoàn tất
Test với ngưỡng Dev khóa. Kiểm lại CSV và JSON trên Drive cho APCER
gộp 3,33%, BPCER 10,00%, ACER gộp 6,67%. [Kết quả và nguồn](../results/OULU_P1_CDCN_PRNET_20261118.md).

Bước kế tiếp đã chuẩn bị là tiếp tục từ `resume.pt` epoch 100 tới
tổng 1.300 epoch, chấm Dev mỗi 50 và lưu phục hồi mỗi năm epoch.
Chạy cell 1–4 trong [notebook tiếp tục](../../notebooks/Face_PAD_OULU_NPU_CDCN_PRNet_Continue_Train_Dev.ipynb)
trên A100 80 GB theo quyết định giữ cùng GPU của lượt nguồn. Tự khôi phục
các mốc đang dở trong nhánh `from100-seed43-to1300-every50-a10080`. Kế hoạch cố định và
checkpoint tốt nhất theo Dev lưu trong `dev-continuation-p1` trên
Drive. Lượt huấn luyện dài chưa chạy. Ước lượng 6–7 giờ, cộng đọc cache
và lưu checkpoint. [Kế hoạch OULU hiện tại](../KE_HOACH_OULU_NPU.md).

[Rà soát phần cứng ngày 26/11](../reviews/A100_CONTINUATION_20261126.md)
ghi việc 40 GB đã đo chạy được batch 56 nhưng chưa đối chiếu kết quả
huấn luyện với 80 GB. Notebook kiểm GPU trước train và ghi môi trường
tính toán để đối chiếu khi tiếp tục. Giữ cùng GPU chưa bảo đảm trùng từng bit.

## Nhánh CASIA và giải trình trước đó

Bắt đầu từ câu hỏi dùng BCE khi mô hình được huấn luyện bằng Focal.
Đối chiếu [ghi chú E3 và Focal](../reviews/defense_readthrough_20261114/CHON_E3_VA_FOCAL.md)
và [kết quả rà soát BCE–Focal](../reviews/fair_comparison_20261030/KET_QUA.md).
Xử lý từng câu hỏi một.

Người dùng yêu cầu làm lại phép so sánh E1–E3 có kiểm soát số bước cập nhật
và weight decay sau khi nắm lại trạng thái dự án. Kết quả Lượt 6 vẫn là bằng
chứng lịch sử. Lần rà soát này chưa xác minh được kết quả của phép thử thay thế.

## Nguồn khi cần tra cứu

- [Bàn giao kỹ thuật 30/10](review_20261030/BAN_GIAO_HOP_NHAT_DEEPFACE_PAD_20261030.md).
- [Kế hoạch và trạng thái hồ sơ bảo vệ](../../reports/defense_20261115/KE_HOACH_BAO_VE.md).
- [Bàn giao Lượt 8 lưu trữ](BAN_GIAO_LUOT_8_LICH_SU.md). Tài liệu ghi lại trạng thái tại mốc 24/10.
- [Cài đặt](../SETUP.md) và [tài sản dữ liệu](../DATA_ASSETS.md).
