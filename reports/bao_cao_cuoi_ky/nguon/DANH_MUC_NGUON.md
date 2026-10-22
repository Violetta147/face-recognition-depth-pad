# Danh mục nguồn để viết báo cáo

## Nguồn hiện hành bổ sung ngày 16 tháng 10

| Nội dung | Nguồn gốc hiện hành |
| --- | --- |
| Split, hash, checkpoint/ngưỡng E0/E1/E2 | `reports/RESEARCH_AUDIT_ROUNDS_1_4_2026-10-16.json` |
| E3/E3b/E4 validation, selection, stage và depth MAE | `reports/ROUND_5_FULL_VALIDATION_2026-10-16.json` |
| Sáu cấu hình test, paired errors và quality | `reports/ROUND_5_TEST_RESULTS_2026-10-16.json` |
| Quy trình lượt 5 | Notebook Round5 CASIA E3 E4, ba config, `reports/ROUND_5_CASIA_RUNBOOK.md` |
| Chi phí E1/E2 sơ bộ | `reports/CASIA_E2_OFFICIAL_HEAD_FROZEN_seed42_summary.md`, notebook E2 |
| Nguồn phương pháp đã kiểm tra | Paper gốc, mã upstream và `reports/paper_round5/PAPER.md` |
| Khoa/lớp | Người dùng xác nhận Công nghệ thông tin, 1021673.2610.23.14 |
| Giảng viên | Hồ sơ `https://scv.udn.vn/hhhung`, đọc 16/10: Huỳnh Hữu Hưng, Tiến sĩ |
| Phân công | `PHAN_CONG_HAI_THANH_VIEN.md`; đề xuất theo yêu cầu, chưa xác nhận lịch sử cá nhân |
| Dấu vết báo cáo | `REPORT_PROVENANCE.json` |

Các mục bên dưới mô tả gói sao chép/trạng thái ngày 15/10. Khi có khác biệt,
ưu tiên hồ sơ kiểm toán 16/10 và file gốc hiện hành. Không ghi đè bản sao
notebook cũ hoặc coi bản sao đó tự cập nhật theo source.

Đường dẫn dưới đây tính từ gốc repository DeepFace-PAD. Bản sao cục bộ nằm trong
thư mục báo cáo để đọc thuận tiện. Kiểm tra `NGUON_CUC_BO.json` khi cần xác định
chính xác file nào đã được sao chép và checksum của nó.

## Nguồn theo phần cần viết

| Phần báo cáo | Nguồn gốc ưu tiên | Bản sao cục bộ |
| --- | --- | --- |
| Yêu cầu của thầy | File người dùng `Tổng hợp chat zalo.md`, ảnh lịch 16/10 và xác nhận trong kế hoạch | `tai_lieu/Tong_hop_chat_zalo.md` |
| Câu hỏi, phạm vi | `DAC_TA_HE_THONG_NHAN_DIEN_KHUON_MAT_PAD_DEPTH_MAP.md` | `tai_lieu/` |
| Kế hoạch nghiên cứu cũ | `KE_HOACH_THUC_HIEN_THEO_BUOI_HOC.md` | `tai_lieu/` |
| Dữ liệu và chia tập | `data/README.md`, output notebook và manifest của run | `tai_lieu/DATA_PROTOCOL.md`, `notebooks/` |
| E0 | `notebooks/E0.ipynb`, `reports/CASIA_E0_BCE_5E_seed42_summary.md` | `notebooks/`, `bao_cao/` |
| Official E1 | `notebooks/Face_PAD_Official_CDCN_E1_Rerun.ipynb`, phần Official E1 trong audit | `notebooks/`, `bao_cao/` |
| E2 | `notebooks/Face_PAD_Round4_Official_Frozen_Head.ipynb`, báo cáo E2 | `notebooks/`, `bao_cao/` |
| Chọn kết quả và diễn giải | `reports/PRESENTATION_ROUNDS_1_4.md`, `reports/rounds1_4_presentation_content.json` | `bao_cao/` |
| Cấu hình | Config E0 5 epoch, Official E1 và Official frozen head | `cau_hinh/` |
| Nghiên cứu liên quan | `reports/LITERATURE_MATRIX.md`, paper và mã tác giả được dẫn | `bao_cao/`, `tai_lieu/CDCN_2020.pdf` |
| Kiến trúc thật | `src/deepface_pad/models/`, loss và scorer trong repository | Đọc file gốc để không nhầm phiên bản |
| Định nghĩa metric | `src/deepface_pad/metrics.py` | Đọc file gốc |

Audit Lượt 1–3 có cả mục E1-Lite lịch sử. Chỉ dùng phần Official E1 cho bảng kết
quả chính. Runbook E1 mô tả quy trình dự kiến, chưa thay thế output của run đã chạy.

## Hình có thể sử dụng

| Thư mục | Nội dung | Cách dùng |
| --- | --- | --- |
| `../hinh_anh/so_do/` | Ba sơ đồ người dùng cung cấp | Đối chiếu mã; ảnh mặt và depth trong sơ đồ là minh họa |
| `../hinh_anh/ket_qua/` | Sáu screenshot E2 | Chép số hoặc trích biểu đồ, giữ nhãn validation/test |
| `../hinh_anh/notebook/` | Các hình đã trích ở phiên làm slide | Kiểm tra nguồn cell và loại mẫu trong bảng bên dưới |

Các hình notebook được sao chép nếu file còn trên máy:

- `validation-depth-case.png`: case đúng của Official E1 trên validation,
  `casia_s14_v2_f000055`, cell 24. Không gọi đây là một trong năm video test cùng sai.
- `e0-e1-curves.png`: đường học E0 và Official E1, notebook E1 cell 31.
- `e2-bce-curve.png`: đường BCE của head, notebook E2 cell 12.
- `e1-e2-score-histograms.png`: phân bố điểm E1/E2, notebook E2 cell 15.

Chưa có bộ ảnh RGB/depth của đúng năm video test cùng sai trong gói này. Có thể
viết phân tích bằng bảng lỗi; chỉ kết luận nguyên nhân thị giác sau khi xem đúng ảnh.

## Nguồn dữ liệu chưa nằm trong gói

Dataset, checkpoint và raw CSV/JSON trên Google Drive không được tải mới trong
phiên tổ chức báo cáo. Xem đường dẫn run trong kế hoạch. Nếu cần kiểm toán độc lập
prediction, threshold hoặc latency, phải đọc đúng artifact đó và ghi nhận kết quả.

Notebook hiện có output đã được đọc khi làm slide ngày 02/10. Khi viết báo cáo
mới, kiểm tra source, output, execution và run ID; không mặc định mọi cell đã sửa
đều được chạy lại. Kế hoạch chờ phê duyệt dataset trong tài liệu cũ có thể đã lỗi
thời; cần người dùng xác nhận nếu muốn đưa tình trạng hiện tại vào báo cáo.

## Đối chiếu Khối 1 ngày 15 tháng 10

Xem [bảng bằng chứng](../BANG_BANG_CHUNG.md) cho bảng validation/test, ngưỡng,
epoch, số lỗi và vị trí nguồn. Ba notebook và ba config gốc khớp từng byte với
bản sao khi kiểm tra. Các số cell hình ở phần trên dùng index từ 0; bảng bằng
chứng dùng số cell từ 1, gồm cả Markdown và code, đồng thời ghi execution_count.
Các curve cục bộ đã khớp pixel với output notebook tương ứng.
