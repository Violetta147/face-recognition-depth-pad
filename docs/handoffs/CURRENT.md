# Bàn giao hiện tại của DeepFace-PAD

**Phạm vi cập nhật 14/11/2026.** Dự án nghiên cứu Face PAD. Xác thực sinh trắc học khuôn mặt là bối cảnh ứng dụng. [Quyết định phạm vi](../reviews/defense_readthrough_20261114/QUYET_DINH.md).

## Điểm tiếp tục hiện tại

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
