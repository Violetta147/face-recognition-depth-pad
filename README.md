# DeepFace-PAD

Dự án nghiên cứu phát hiện tấn công khuôn mặt từ ảnh RGB, dùng giám sát bằng
bản đồ độ sâu giả lập. Nhóm so sánh CDCN dùng điểm độ sâu trung bình với
CDCN có bộ phân loại học từ bản đồ độ sâu. Kế hoạch gồm tám lượt báo cáo.

## Tiếp tục công việc

Đọc [trạng thái và kết quả](docs/PROJECT_STATUS.md), sau đó đọc
[bàn giao hiện hành](docs/handoffs/CURRENT.md). Bàn giao chỉ rõ phần còn thiếu
của Lượt 7–8 và vị trí tài liệu mới. Không cần lịch sử chat hoặc prompt đặc biệt.
Phiên Codex mới làm việc trong thư mục repository đã mở.

Lượt 1–6 đã có kết quả. Lượt 7 đã có phân tích lỗi ba seed, 20 hình và log
webcam thực đo. Lượt 7 còn thiếu cảnh ảnh in, kiểm quay lại đủ cửa sổ và
hoàn thiện giải thích lỗi webcam. [Báo cáo và paper mới](reports/round8_documents_20261023/README.md)
đã tích hợp kết quả đến Lượt 7: báo cáo 35 trang, phần chính 27 trang, đúng
ba chương; paper tiếng Việt sáu trang theo bố cục tham chiếu IEEE conference.
Các bản lịch sử giữ nguyên. Chưa làm webcam, slide hoặc train mới trong
phiên tài liệu; chưa push, upload hoặc nộp bài. Phiên sau đọc bàn giao và
tiếp tục theo nhiệm vụ người dùng giao.

## Thiết lập và dữ liệu

1. Clone hoặc pull nhánh `main` của repository này.
2. Làm theo [SETUP.md](docs/SETUP.md) để tạo môi trường và chạy kiểm thử.
3. Đọc [DATA_ASSETS.md](docs/DATA_ASSETS.md) khi cần dữ liệu gốc hoặc video riêng.

Git chứa code, cấu hình, notebook, checkpoint, score CSV, bản khóa kết quả,
hình, log số và tài liệu cần để tiếp tục nghiên cứu. Các tệp được theo dõi
trong `artifacts/` là bằng chứng có chọn lọc; không xóa cả thư mục.
`evidence/face-pad/` chứa checkpoint và bằng chứng các lượt đã chạy.
Dữ liệu CASIA gốc, target depth và video webcam riêng nhận qua Drive.
Máy mới tự cài Python và thư viện theo SETUP; Git không chứa môi trường đã cài.

## Kết quả cần hiểu trước khi viết tiếp

Trên CASIA development, ACER video của ba seed 43/44/45 là 4,3210 ± 2,1623%
với E1 và 3,7037 ± 0,6415% với E3 (trung bình ± độ lệch chuẩn mẫu).
E3 tốt hơn ở hai trong ba seed. Chưa có bằng chứng cải thiện ổn định.
Webcam thực đo vẫn từ chối người thật; lỗi này được giữ trong báo cáo.
Webcam không thay cho đánh giá CASIA đã khóa.

## Tài liệu và cấu trúc

| Vị trí | Nội dung |
| --- | --- |
| [Kế hoạch tám lượt](KE_HOACH_THUC_HIEN_THEO_BUOI_HOC.md) | Phạm vi và tiêu chí từng lượt; mục 10–11 dành cho Lượt 7–8. |
| [Đặc tả](DAC_TA_HE_THONG_NHAN_DIEN_KHUON_MAT_PAD_DEPTH_MAP.md) | Bài toán, mô hình và yêu cầu nghiên cứu. |
| `src/deepface_pad/`, `scripts/`, `tests/` | Mã thư viện, lệnh chạy và kiểm thử. |
| `configs/`, `notebooks/` | Cấu hình và quy trình Colab; notebook Executed giữ đầu ra lịch sử. |
| `reports/ROUND_6_*`, `reports/round7/` | Kết quả, hình và giới hạn của Lượt 6–7. |
| [reports/round8_documents_20261023/](reports/round8_documents_20261023/README.md) | Báo cáo/paper Word và Markdown mới, kiểm trang, provenance và nguồn số/hình. |
| `reports/bao_cao_cuoi_ky/`, `reports/paper_round5/` | Báo cáo/paper lịch sử đến Lượt 5, được giữ nguyên. |
| `reports/slides_round5/` | Slide lịch sử; slide Lượt 8 chưa thực hiện. |
| `data/`, `evidence/`, các tệp được theo dõi trong `artifacts/` | Manifest, checkpoint, score, số đo và nguồn dựng hình. |

Tài liệu có ngày hoặc số lượt ghi trạng thái tại thời điểm đó. Dùng
`docs/handoffs/CURRENT.md` để xác định việc hiện hành; dùng CSV, JSON và bản
khóa tương ứng để kiểm số liệu. Bàn giao không tự cấp quyền chạy camera,
train, thay kết quả hoặc nộp báo cáo.
