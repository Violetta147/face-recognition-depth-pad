# Thiết lập máy để tiếp tục dự án

Chạy lệnh tại thư mục gốc của repository. Không cần thư mục bàn giao khác.
Các bước này không train hoặc score lại toàn tập test.

## 1. Tạo môi trường

Ví dụ PowerShell trên Windows với Python 3.13 đã cài:

```powershell
py -3.13 -m venv .venv
& ./.venv/Scripts/python.exe -m pip install -r requirements-cpu.txt
& ./.venv/Scripts/python.exe -m pip install --no-deps -e .
& ./.venv/Scripts/python.exe -m pytest -q
```

Trên Linux dùng `.venv/bin/python`. `requirements-cpu.txt` ghi phiên bản
trực tiếp đã quan sát, chưa phải lockfile toàn bộ dependency hoặc bằng chứng
mọi hệ điều hành đã được thử. Dùng CPU cho các bước tiếp tục; ghi phiên bản,
log và lý do test skip trên máy nhận. Không chép venv/runtime từ máy nguồn.

## 2. Kiểm phân tích lỗi bằng CSV

```powershell
& ./.venv/Scripts/python.exe scripts/analyze_round7.py --output outputs/analysis-recheck-01
```

Lệnh kiểm hash/membership và không chạy model. Corrected/new_errors cần là
6/0, 1/4, 2/1 cho seed 43/44/45. Output phải mới. Nguồn mặc định
`artifacts/round6-test-audit-20261022/` đã có trong Git. Khi hash không khớp,
tìm tệp sai và phục hồi; không sửa hash để che thay đổi.

## 3. Checkpoint và dữ liệu gốc

Checkpoint nằm ở `evidence/face-pad/runs/<run_id>/`; run ID, threshold và
hash có trong JSON kết quả Lượt 5–6. Giữ cả tên best_stage và best.ckpt khi
bản khóa tham chiếu, kể cả khi hai tệp cùng nội dung.

Chỉ nhận hai archive trong `DATA_ASSETS.md` khi cần RGB/target hoặc chuẩn bị
thí nghiệm khác. Manifest gốc đã phục hồi đúng byte từ manifest depth bằng
cách để trống depth_path và ghi LF. Không chia lại tập hoặc chọn frame mới.
SHA gốc: `58fffcc2fb29649af1b8424d78b85067eefbd0321fde6b27fbd0803ef0fd7192`.

Archive depth chứa target live. Pipeline khôi phục target attack bằng zero
float32 và kiểm SHA theo snapshot. Không chạy lại 3DDFA để thay target đã
khóa. Thiếu target live phải phục hồi nguồn. Train trên máy mới cần đủ dữ
liệu/cache đã giải nén và config đúng đường dẫn, không chỉ có archive.

## 4. Dựng lại hình khi cần

```powershell
& ./.venv/Scripts/python.exe scripts/render_round7.py --drive evidence/face-pad --score-mode diagnostic --output outputs/figures-new-01 --artifacts outputs/figure-inputs-new-01
```

Lệnh cần hai archive và chỉ forward các case đã chọn. Diagnostic giữ
tolerance cũ và ghi sai khác; strict dừng khi một điểm không đạt. Giữ output
lịch sử. Xem PNG và raw arrays đã có không cần dataset hoặc GPU.

## 5. Webcam trên máy nhận

Chỉ chạy khi người vận hành sẵn sàng. Checkpoint, detector ONNX và giấy phép
đã có trong Git. Dùng Python `.venv`, không cần đường dẫn demo-runtime cũ.
Đọc `reports/round7/WEBCAM_GUIDE.md` trước khi thao tác cảnh.

```powershell
& ./.venv/Scripts/python.exe scripts/run_round7_webcam.py --drive evidence/face-pad --probe --no-preview --output outputs/camera-probe-01
& ./.venv/Scripts/python.exe scripts/run_round7_webcam.py --drive evidence/face-pad --scenario live --output outputs/webcam-live-01
```

Chọn cửa sổ READY và nhấn Space. Đợi 5/5 trước khi kiểm rời/quay lại; đợi
5/5 lần nữa sau quay lại. Config đo 45 giây, Q dừng sớm. Replay dùng
`--scenario replay`, print dùng `--scenario print`, mỗi lượt một output mới.
Giữ mặt thật của người cầm ngoài khung khi đưa điện thoại. Ảnh trên màn hình
không phải ảnh in. `5/5` đếm frame, không đếm giây.

Camera/môi trường/frontend khác cần config mới chốt trước lượt đo và ghi
thay đổi. Giữ checkpoint/threshold khóa. Không dùng vài clip tính ACER
benchmark. Tốc độ máy nguồn không phải tốc độ bảo đảm của thiết bị mới.

## 6. Tài liệu

Tiếp tục theo `handoffs/CURRENT.md`, mục 4–5. Nguồn Word/paper/slide và builder
đã có. Sau sửa, chạy test liên quan, render và kiểm bố cục; ghi phạm vi đã kiểm.

Builder Word/paper lịch sử có đường dẫn output cố định. Trước khi dựng bản
Lượt 8, tạo nguồn mới và đổi đường dẫn input/output sang phiên bản mới; không
chạy mặc định để ghi đè Word đã khóa. Các builder chính là
`scripts/build_final_report_completed.py` và `scripts/build_round5_paper.py`.

Để xuất slide bằng script hiện có, cài Node.js và npm, rồi cài Marp CLI đúng
phiên bản đã dùng cho deck lịch sử:

```powershell
npm install --prefix artifacts/marp-report-20261016/tooling --no-audit --no-fund @marp-team/marp-cli@4.5.1
powershell -NoProfile -File scripts/render_marp_report.ps1
```

Lệnh render mặc định xuất deck Lượt 5. Khi làm deck Lượt 8, đổi đường dẫn
Markdown và output trong bản script dành cho deck mới trước khi chạy. Marp
cần trình duyệt Chrome/Edge hoặc Chromium phù hợp để render PDF/PPTX. Đây là
công cụ cài riêng, không có trong requirements Python. Asset đã có trong Git;
không cần xuất lại nền bằng PowerPoint. Chỉ script dựng lại nền mới cần
PowerPoint trên Windows. Mở README của từng thư mục báo cáo để đọc quy trình
lịch sử; dùng CURRENT để xác định kết quả cần bổ sung hiện nay.

Phạm vi kiểm clone đã thực hiện: [VALIDATION_2026-10-23.md](VALIDATION_2026-10-23.md).
