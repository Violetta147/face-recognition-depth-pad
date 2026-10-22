# DeepFace-PAD: bộ bàn giao nghiên cứu

Bản bàn giao ngày 22/10/2026. Ngôn ngữ: tiếng Việt.

Dự án kiểm tra khả năng dùng bản đồ độ sâu để phân biệt mặt thật với ảnh in
và video phát lại. Mã nguồn và kết quả đã có đến Lượt 7. Dự án chưa hoàn tất.

## Bắt đầu tại đây

1. Đọc [bàn giao nhóm](docs/team_handoff/BAN_GIAO_NHOM.md).
2. Đọc [danh mục giao nhận](docs/team_handoff/DANH_MUC_GIAO_NHAN.md).
3. Làm theo [khôi phục và kiểm tra](docs/team_handoff/KHOI_PHUC_VA_KIEM_TRA.md).
4. Chọn một việc trong bảng công việc còn lại.
5. Lập [phiếu thí nghiệm mới](docs/team_handoff/THI_NGHIEM_MOI_MAU.md) trước khi thay phương pháp.

Lượt 6 đã hoàn tất sáu lượt chạy và 138 epoch. E3 giảm ACER trung bình nhưng
kém E1 ở seed 44. Chưa có bằng chứng cải thiện ổn định. Webcam đã có timing
thực nhưng còn từ chối người thật. Giữ cả các kết quả không cải thiện.

## Kiểm tra bản nhận

```powershell
python scripts/verify_team_handoff.py --root .
```

Tệp [delivery/FILES.json](delivery/FILES.json) liệt kê từng tệp, kích thước,
SHA-256, nguồn và vai trò. Bản bàn giao cập nhật nhánh main hiện có trên GitHub.
Commit bàn giao nối tiếp lịch sử remote; không nhập các commit cục bộ chứa hook.
Mã commit cũ trong báo cáo được giữ làm thông tin nguồn.
Dùng các source ZIP đi kèm để đọc phiên bản cũ; không giả định commit cũ có
trong lịch sử của nhánh này.

Bản GitHub có mã nguồn, kiểm thử nghiên cứu, bản thảo, hình, score CSV và
checkpoint. Bộ dữ liệu ảnh đầy đủ và video webcam không nằm trong GitHub.
Các điều kiện nhận chúng được ghi trong danh mục giao nhận. Bản clone đủ để
kiểm hash và phân tích score trên CPU; dựng lại ảnh cần thêm archive dữ liệu.

Tài liệu trong `reports/` là bằng chứng có ngày tháng. Chỉ tài liệu bàn giao
nhóm này mô tả công việc hiện tại. Không dùng kế hoạch cũ làm lệnh chạy lại
thí nghiệm đã hoàn tất. Bản Word/paper hiện tại chỉ đến Lượt 5.
