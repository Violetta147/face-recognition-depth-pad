# Danh mục tệp và điều kiện giao nhận

## 1. Danh sách chính xác

`delivery/FILES.json` là danh sách tệp thực tế trong bản xuất. Mỗi dòng có
đường dẫn, vai trò, kích thước, SHA-256 và nguồn. Verifier kiểm byte của các
tệp đó. `delivery/VALIDATION_DELIVERY.json` ghi kiểm tra bản xuất sạch.
Không dùng số test của máy nguồn thay kết quả trên bản xuất hoặc máy nhận.
Tệp .gitattributes giữ nguyên byte khi Git nhận hoặc checkout tệp. Không tự
đổi xuống dòng LF/CRLF vì việc đó làm đổi SHA-256 của bằng chứng đã khóa.

## 2. Nhóm tệp có trong GitHub

| Đường dẫn | Vai trò |
| --- | --- |
| README.md, docs/team_handoff/ | Điểm vào, trạng thái, công việc còn lại và cách khôi phục. |
| src/deepface_pad/ | Model, loss, dữ liệu, metric, train, figure, cost, error analysis và median gate. |
| configs/ | Cấu hình nghiên cứu cũ và config webcam đã dùng. |
| tests/ | Kiểm thử nghiên cứu, builder và integrity; không có test công cụ vận hành máy cá nhân. |
| scripts/ | CLI nghiên cứu, builder, exporter và verifier bản bàn giao. |
| data/manifests/ | Manifest nguồn và manifest depth 12.000 frame; cả hai khớp SHA lịch sử. |
| evidence/face-pad/runs/ | Sáu run seed 42 chính và sáu run Lượt 6; checkpoint, config, threshold và score gốc. |
| evidence/face-pad/reports/ | Bản đăng ký, bản khóa, receipt và provenance dữ liệu. |
| evidence/source_archives/ | Source ZIP lịch sử. Dùng để kiểm nguồn, không tự chạy lại gate cũ. |
| artifacts/round6-test-audit-20261022/ | Recovery score/metadata đủ để chạy lại phân tích CPU. |
| artifacts/round6-cost-audit-20261022/ | Timing A100 và registration/results gốc. |
| artifacts/round7/ | Chỉ numerical logs, raw depth arrays, failure diagnostic và detector đã chọn. |
| reports/ | Kết quả, báo cáo, paper, slide, addendum và provenance có ngày tháng. |
| reports/slides_round5/assets/ | Tài sản cần để dựng/kiểm slide cũ. |
| reports/bao_cao_cuoi_ky/hinh_anh/ | Tài sản cần để dựng/kiểm Word cũ. |
| diagrams/, references/ | Sơ đồ phương pháp và nguồn tham khảo đã có. |
| artifacts/figure-notebook-20261016/ | Chỉ các hình nguồn cụ thể mà provenance của slide tham chiếu. |
| artifacts/workspace-audit-20261016/ | Chỉ template Word gốc mà builder paper cần. |

Các thư mục artifact được chọn theo tệp cụ thể. Không sao chép toàn bộ thư
mục artifact nguồn. Manifest ghi rõ tệp nào được chọn.

Các notebook được giữ để đọc lịch sử và dùng công cụ đúng protocol. Notebook
Executed là bằng chứng; notebook Clean là đầu vào công cụ. Hai vai trò khác nhau.
Tài liệu kế hoạch cũ được giữ để truy nguồn quyết định. Bàn giao nhóm quyết
định trạng thái hiện tại; không coi việc chưa tích trong kế hoạch cũ là lệnh mới.

## 3. Nhóm không công bố trong GitHub

| Nhóm | Cách nhận | Điều kiện sử dụng |
| --- | --- | --- |
| casia-fasd.zip đầy đủ | Chủ dữ liệu giao qua kho riêng. | Đúng SHA trong EXTERNAL_ASSETS.json. Kiểm quyền truy cập trước khi cần GPU. |
| Archive pseudo-depth/cache | Chủ dữ liệu giao cùng corpus. | Đúng SHA; không sinh lại 3DDFA để thay cache cũ. |
| Năm video webcam | Bộ ZIP riêng do chủ dự án giữ. | Team nhận qua kênh riêng; kiểm SHA. Không đẩy lên repo công khai. |
| Raw RGB của case | Trích từ đúng corpus khi cần. | Hash mới đối chiếu provenance; không gọi là hash đăng ký trước train. |
| Môi trường Python/venv | Cài từ requirements vào môi trường mới. | Không chép demo-runtime hoặc thư viện đã cài lên GitHub. |

Tên tệp, kích thước, SHA và vị trí nguồn được ghi trong EXTERNAL_ASSETS.json.
Danh mục chỉ mô tả tệp; danh mục không cấp quyền chia sẻ hoặc quyền truy cập.
Nếu người nhận chưa có quyền Drive, H01 chưa đạt. Ghi rõ tình trạng này.

## 4. Nhóm bị loại khỏi bộ bàn giao

Loại công cụ tự động của máy cá nhân, cấu hình agent cục bộ, bộ cài runtime,
cache, log vận hành công cụ, hội thoại xuất, tutorial soạn slide và briefing
khởi đầu đã được thay thế. Danh sách từng tệp Git bị loại có trong FILES.json.

Không xóa hoặc chuyển tệp nguồn để tạo bản sạch. Việc loại khỏi bộ bàn giao
không kết luận tệp nguồn vô dụng. Các bằng chứng nghiên cứu thất bại vẫn giữ.
Remote chỉ có nhánh main tại thời điểm kiểm. Theo yêu cầu chủ dự án, commit
bàn giao nối tiếp main trên GitHub bằng bộ tệp đã chọn. Không nhập các commit
cục bộ chứa công cụ vận hành. Không sửa lịch sử hoặc force-push main.

## 5. Tiêu chí nhận đủ

1. Verifier đạt trên bản clone.
2. Test nghiên cứu đạt hoặc có skip được giải thích.
3. Score analysis khớp ba seed đã ghi.
4. Người nhận tìm được checkpoint theo run ID và kiểm được hash.
5. Tài sản Word/paper/slide có đủ để kiểm nội dung cũ.
6. Tệp ngoài Git có người phụ trách giao và có quyền truy cập.
7. Người nhận phân biệt được kết quả đã đo và kế hoạch chưa chạy.
