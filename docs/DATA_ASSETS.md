# Dữ liệu và video ngoài Git

Checkpoint, score, manifest, hình và tài liệu đã có trong Git. Không cần tải
dataset chỉ để đọc báo cáo, sửa Word/paper/slide hoặc phân tích CSV.

## Tệp cần nhận riêng

| Tệp trong face-pad | Tình trạng tại máy nguồn ngày 22/10/2026 | Chủ dự án cần làm |
| --- | --- | --- |
| casia-fasd.zip | Đã có trên Drive, 2.198.264.547 byte. | Không upload lại; chia sẻ quyền tải nếu cần ảnh gốc. |
| depth-checkpoints/casia-fasd-depth-checkpoint.tar | Đã có trên Drive, 20.439.040 byte. | Không upload lại; chia sẻ quyền tải nếu cần dựng lại target/hình. |
| webcam-evidence-private.zip | Đã tạo ở máy nguồn; chưa thấy ở đường dẫn đích này trên Drive khi kiểm. | Upload ZIP một lần nếu dùng Drive để giao video, sau đó chia sẻ quyền tải. |

ZIP nguồn: C:/Users/LAPTOP T&T/VIOLETTA/Documents/DeepFace-PAD/artifacts/team-private-20261022/webcam-evidence-private.zip.
ZIP có năm video cùng CSV/summary và danh mục SHA. Kích thước 62.254.973 byte.
SHA-256: 6e107745ea7dfa5b548ccc87437327d0d08f52a3ebdfbd72df32227daf964e56.
SHA của hai archive dữ liệu nằm trong delivery/EXTERNAL_ASSETS.json.

G: là ổ Drive gắn trên máy nguồn, không phải ổ bắt buộc trên máy nhận.
Có thể cấp quyền đọc/tải ba tệp cụ thể; không bắt buộc cấp toàn bộ face-pad.
Chưa kiểm quyền tài khoản người nhận. Nếu dùng notebook Colab có đường dẫn
Drive cũ, sửa đường dẫn theo vị trí người nhận lưu hoặc truy cập tệp.

## Công việc nào cần tệp nào

| Công việc | Tệp ngoài Git |
| --- | --- |
| Đọc/sửa báo cáo, slide; phân tích score CSV; kiểm mã | Không cần. |
| Chạy webcam mới với checkpoint có sẵn | Không cần dataset CASIA; cần camera của máy nhận. |
| Xem video cũ hoặc chọn video demo dự phòng | ZIP webcam. |
| Dựng lại RGB/target/prediction từ corpus | Archive CASIA và archive depth. |

Không upload riêng RGB của các case vì có thể trích từ casia-fasd.zip.
Không upload venv, demo-runtime, thư viện cài sẵn, cache, cấu hình agent,
hook, log vận hành công cụ hoặc bản xuất chat. Máy nhận tự cài theo SETUP.md.
Không cần upload lại checkpoint, runs hoặc reports đã có trong Git.

## Hình nguồn dùng cho slide nào

artifacts/figure-notebook-20261016/ chứa PNG nguồn cho bộ slide tổng hợp đến Lượt 5:

- reports/slides_round5/Bao_cao_DeepFace_PAD.md: nội dung slide.
- reports/slides_round5/Bao_cao_DeepFace_PAD.pptx: bản PowerPoint.
- reports/slides_round5/assets/provenance.json: ánh xạ hình nguồn sang asset và SHA.

Đây chưa phải slide cuối bổ sung Lượt 6–7. Toàn bộ hình nguồn và asset này đã
có trong Git; không cần upload lên Drive.

## Đọc tài liệu trên máy mới

Bắt đầu từ README, PROJECT_STATUS, SETUP và tài liệu này. Chỉ đọc báo cáo hoặc
notebook lịch sử khi việc đang làm cần bằng chứng đó. Không cần đưa danh sách
tệp bị loại hoặc lịch sử công cụ máy nguồn vào context của agent.
