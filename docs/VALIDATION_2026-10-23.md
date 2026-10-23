# Kiểm tra repository để tiếp tục Lượt 7–8

Ngày kiểm: 23/10/2026. Snapshot được kiểm:
`26dfb5f5492e29c389437b336a1cfbc5c7c0b840`.
Commit ghi nhận tài liệu kiểm tra này chỉ bổ sung hồ sơ, không sửa mã nghiên cứu.

## Kết quả

| Phạm vi | Kết quả | Giới hạn |
| --- | --- | --- |
| Repository gốc, gồm công cụ vận hành giữ riêng tại máy nguồn | 214 passed, 1 skipped, 34 subtests; 69,53 giây | Skip do quyền tạo symlink Windows. Bộ này gồm test công cụ cục bộ không công bố. |
| Clone chỉ từ nhánh main, không chép tệp bị ignore của máy nguồn | 167 passed, 1 skipped, 34 subtests; 40,17 giây | Skip test kiểm bản PPTX ngày 03/10 cũ vì binary đó chỉ có cục bộ; không phải deck Lượt 5. |
| Phân tích CSV ngay trong clone | PASS; 20 case | Seed 43/44/45: corrected/new_errors 6/0, 1/4, 2/1. Không chạy model. |
| Bằng chứng khoa học có trong bản Git đã kiểm | 659 tệp khớp SHA với nội dung đã xác minh trước đó | Không thay checkpoint, score, ngưỡng, bản khóa, raw arrays hoặc hình đã lưu. |
| Bốn ZIP nguồn lịch sử | Đã kiểm 368 tên thành viên | Không có thư mục hook/agent, Git hoặc tên bản xuất chat trong các ZIP này. |

JUnit của clone: [pytest-clean-clone.xml](validation/pytest-clean-clone.xml).
Clone đã dùng module từ chính `clone-validation/src/deepface_pad`, không dùng
mã thư viện của repository gốc qua editable install. Working tree clone sạch
sau kiểm thử và phân tích; output phân tích nằm trong thư mục bị ignore.

## Cách kiểm và phạm vi chưa kiểm

Clone được kiểm bằng Python 3.13.11 hiện có trên máy nguồn, với PYTHONPATH
trỏ vào `src` và root của clone; torch 2.11.0, torchvision 0.26.0,
numpy 2.4.3, pandas 3.0.1, pytest 9.1.1 và python-docx 1.2.0.
Đây là kiểm tệp của một clone sạch; chưa phải bằng chứng cài mới toàn bộ
requirements trong venv rỗng hoặc chạy trên máy của đồng đội.

Lệnh chính: `python -m pytest -q -p no:cacheprovider` và
`python scripts/analyze_round7.py --output outputs/analysis-recheck-01`.
Máy mới cài theo `SETUP.md` rồi chạy lại. Kết quả webcam lịch sử dùng runtime
OpenCV riêng; kiểm tra lần này không bật camera hoặc đo lại FPS/TTD.

Chưa train, score lại toàn tập, nhận dữ liệu bằng tài khoản đồng đội, kiểm
quyền Drive, sửa báo cáo Lượt 8 hoặc nộp bài trong tác vụ đồng bộ này.
Các việc còn lại được ghi rõ trong `handoffs/CURRENT.md`.
