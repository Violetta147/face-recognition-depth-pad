# Gói Lượt 6 đã chuẩn bị cục bộ

**Cập nhật sau thực thi:** replication và kiểm toán test đã xong. Đọc
`reports/ROUND_6_RESULTS_2026-10-22.md/.json` và `docs/handoffs/CURRENT.md`.
Nội dung dưới đây ghi lại thời điểm chuẩn bị gói, không yêu cầu chạy lại.

Sáu config ở `configs/round6/`, runner/bộ kiểm tra ở
`src/deepface_pad/round6.py`, notebook mới ở
`notebooks/Face_PAD_Round6_CASIA_E1_E3.ipynb`.
Builder: `scripts/build_round6_colab.py`; đóng gói từ Git commit:
`python scripts/package_round6.py --output artifacts/round6-colab-20261022`.
ZIP, notebook độc lập và `package-receipt.json` lưu trong thư mục output;
receipt ghi chính xác commit/hash/byte size. ZIP chứa runtime/test/config,
không chứa dữ liệu ảnh, checkpoint hay phụ phẩm hooks.

Đã kiểm CPU bằng fixture và test hồi quy, chưa có số đo GPU/CASIA mới.
Xem receipt kiểm thử hiện tại ở `artifacts/project-hooks/state/validation.json`;
PASS chỉ gắn với nội dung đã kiểm. Các log thất bại trong quá trình chuẩn bị
được giữ, gồm lỗi import package khi thiếu PYTHONPATH và lần kiểm notebook
trước khi builder tạo file; không coi đó là run GPU thất bại.

Bước tiếp theo: người dùng mở notebook trên Colab, bật A100, mount đúng Drive,
upload ZIP và chạy **0.1–1.4 rồi dừng tại PREFLIGHT PASS**. Gửi output CPU tests,
GPU/source commit/manifest/cache/registration để kiểm; xác nhận budget còn lại
trước khi mở cổng seed 43. Quy trình đầy đủ và giới hạn resume ở
`reports/ROUND_6_CASIA_RUNBOOK.md`. Không mở test trước freeze cả sáu validation.

Hai thay đổi có sẵn khi mở phiên ở `KE_HOACH_HOOKS_VA_BAN_GIAO.md` và
`docs/handoffs/CURRENT.md` được để nguyên ngoài commit gói mới. Hai Word,
notebook lịch sử, split/cache và kết quả Lượt 5 không bị biên tập. Chưa upload
hoặc push; các commit trong phiên này chỉ cục bộ. Đo chi phí E1/E3/E4 cùng GPU
vẫn là việc sau replication, chưa được ghi thành số đo đã có.
