# Khôi phục dự án và kiểm tra bản nhận

Làm các bước theo thứ tự. Các lệnh dưới đây không huấn luyện hoặc score lại test.
Chạy lệnh từ thư mục gốc của bản clone.

## 1. Kiểm tệp trước khi cài môi trường

```powershell
python scripts/verify_team_handoff.py --root .
```

Kết quả cần có: PASS và số tệp đã kiểm. Nếu hash khác, dừng bước dùng bằng
chứng đó. Kiểm xem đây là sửa đổi có chủ đích hay lỗi truyền tệp. Không sửa
FILES.json để che thay đổi. Giữ bản nhận nguyên vẹn trước khi phát triển.

## 2. Tạo môi trường CPU riêng

Môi trường đã dùng để kiểm cục bộ là Python 3.13. Không cài đè môi trường cá nhân.

```powershell
py -3.13 -m venv .venv
& ./.venv/Scripts/python.exe -m pip install -r docs/team_handoff/requirements-cpu.txt
& ./.venv/Scripts/python.exe -m pip install --no-deps -e .
& ./.venv/Scripts/python.exe -m pytest -q
```

Trên Linux, thay đường dẫn interpreter bằng `.venv/bin/python`.
Danh sách requirements ghi phiên bản trực tiếp đã quan sát. Đây không phải
lockfile đầy đủ của mọi dependency hoặc bằng chứng đã kiểm mọi hệ điều hành.
Lưu phiên bản và log của máy nhận. Một test bỏ qua phải có lý do trong log.
Bản bàn giao đã loại hai bộ test riêng cho công cụ vận hành cục bộ. Vì vậy
không yêu cầu số test bằng 214 của repository nguồn. Xem VALIDATION_DELIVERY.json
trong delivery để biết kết quả kiểm của bản xuất sạch.

## 3. Kiểm lại phân tích ba seed bằng score đã lưu

```powershell
& ./.venv/Scripts/python.exe scripts/analyze_round7.py --output outputs/analysis-recheck-01
```

Điều kiện đạt: corrected/new_errors lần lượt 6/0, 1/4, 2/1 ở seed 43/44/45.
Lệnh kiểm hash và membership rồi tạo output mới. Lệnh không chạy model.
Nếu output đã tồn tại, chọn tên mới. Không xóa lượt trước để chạy lại cùng tên.

## 4. Kiểm checkpoint và seed lịch sử

Checkpoint nằm trong `evidence/face-pad/runs/<run_id>/`.
Đối chiếu run ID trong JSON kết quả Lượt 5 hoặc Lượt 6. FILES.json kiểm byte
của mọi checkpoint đi kèm. Không dùng filename gần giống để thay mô hình.

Một số tệp best_stage và best.ckpt giống hệt nhau. Giữ cả hai tên vì bản khóa
tham chiếu cả hai. Git chỉ cần lưu một blob khi nội dung hai tệp giống nhau.
Không có smoke run trong danh sách model bàn giao.

## 5. Nhận bộ dữ liệu nếu cần dựng lại ảnh hoặc làm thí nghiệm

Đọc delivery/EXTERNAL_ASSETS.json. Nhận đúng archive từ chủ dữ liệu qua kênh
được phép. Việc có đường dẫn G: trong hồ sơ cũ không cấp quyền Drive cho máy mới.

Đặt `casia-fasd.zip` tại `evidence/face-pad/casia-fasd.zip`. Đặt archive depth
tại `evidence/face-pad/depth-checkpoints/casia-fasd-depth-checkpoint.tar`.
Kiểm SHA theo danh mục. Không dùng archive mới khác hash thay dữ liệu đã khóa.

Archive depth có target live. Một số target attack không nằm trong archive.
Pipeline khôi phục zero float32 và yêu cầu SHA bằng snapshot. Không chạy lại
3DDFA chỉ vì thiếu target attack. Thiếu target live phải dừng và phục hồi nguồn.

Manifest nguồn `data/manifests/casia_fasd_debug.csv` đã được khôi phục bằng
cách để trống depth_path trong manifest depth và ghi CSV với xuống dòng LF.
SHA khớp chính xác `58fffcc2fb29649af1b8424d78b85067eefbd0321fde6b27fbd0803ef0fd7192`.
Đây là phục hồi byte của tệp cũ, không phải chọn lại frame hoặc chia lại tập.
Trước train mới, cần giải nén toàn bộ dữ liệu và khôi phục đủ cache theo
manifest. Các tệp config cũ có đường dẫn Colab; cần tạo config mới cho máy nhận.
Không gọi việc chỉ đặt archive vào thư mục là đã sẵn sàng huấn luyện.

## 6. Dựng lại hình Lượt 7 khi đã đủ archive

```powershell
& ./.venv/Scripts/python.exe scripts/render_round7.py --drive evidence/face-pad --score-mode diagnostic --output outputs/figures-new-01 --artifacts outputs/figure-inputs-new-01
```

Đây là bounded inference trên các case đã định, không phải score lại cả test.
Chế độ diagnostic giữ tolerance cũ và ghi các ca không đạt. Không gọi hình mới
là tái lập chính xác CUDA. Chế độ strict sẽ dừng khi một frame không đạt tolerance.
Output có provenance, raw arrays và scale chung. Không thay hình lịch sử.

Để xem hình đã có, mở reports/round7/figures-attempt03. Không cần GPU hoặc dataset
để đọc PNG, CSV và raw arrays đã bàn giao.

## 7. Chạy webcam trên máy nhận

Không chạy camera khi người vận hành chưa sẵn sàng. Không cần bật lại camera
chỉ để kiểm score CSV. Thiết lập môi trường ở bước 2 đã có OpenCV 4.14.0.94.
Không cần chép môi trường cài sẵn từ máy nguồn.

```powershell
& ./.venv/Scripts/python.exe scripts/run_round7_webcam.py --drive evidence/face-pad --probe --no-preview --output outputs/camera-probe-01
& ./.venv/Scripts/python.exe scripts/run_round7_webcam.py --drive evidence/face-pad --scenario live --output outputs/webcam-live-01
```

1. Chọn cửa sổ camera khi có chữ READY.
2. Giữ mặt trong khung.
3. Nhấn Space để bắt đầu đo.
4. Đợi bộ đếm đủ 5/5 để có quyết định median đầu tiên.
5. Nếu kiểm reset, rời vùng nhìn đến khi buffer về 0/5.
6. Quay lại và đợi đủ 5/5 lần nữa.
7. Đợi kết thúc hoặc nhấn Q để dừng sớm.

`5/5` là năm frame, không phải năm giây. 15 giây chỉ là hướng dẫn giữ mặt
ổn định. `no_face` và `multiple_faces` là kết quả detector; không phải nhãn
ground truth về người trong ảnh. Không nhận live khi chưa đủ cửa sổ.

Chạy replay vào thư mục mới bằng `--scenario replay`. Dùng video trên điện
thoại, giữ điện thoại cố định, đưa mặt thật của người cầm ra ngoài vùng nhìn.
Chạy print bằng `--scenario print` khi đã có ảnh in trên giấy. Không gọi ảnh
hiển thị trên màn hình là print. Không tự đổi threshold để demo nhận đúng live.

Môi trường khác hoặc frontend khác phải có config mới, chốt trước lượt đo.
Giữ model/threshold khóa nếu mục tiêu là kiểm pipeline gốc. Ghi cả config cũ
và config mới nếu mục tiêu là nghiên cứu frontend.

## 8. Tiếp tục train bằng một thí nghiệm mới

1. Điền THI_NGHIEM_MOI_MAU.md vào tài liệu mới.
2. Chốt đối chứng, dữ liệu, budget và cách chọn mô hình trước khi chạy.
3. Tạo config mới, không dùng ID của lượt đã hoàn tất.
4. Đặt output tại `new_runs/<ma-thi-nghiem>/` hoặc kho riêng.
5. Sửa đường dẫn config theo máy nhận; giữ bản config đã chạy trong output.
6. Nếu lấy config đã đăng ký Lượt 6 làm mẫu, bỏ binding Lượt 6 khỏi bản mới.
7. Ghi source commit mới và hash checkpoint khởi tạo.
8. Chạy kiểm tra manifest, depth và test CPU trước khi cấp GPU.

Lệnh tổng quát là `python scripts/run_experiment.py <config-moi.yaml>`.
Không chạy lệnh này cho config đã hoàn tất để kiểm chức năng import.
Không tiếp tục đúng optimizer/RNG từ các checkpoint chỉ chứa trọng số.
Ngân sách 2–3 giờ A100 cũ không phải ngân sách được duyệt cho đợt mới.

## 9. Hoàn thiện tài liệu

Tạo phiên bản mới của Word/paper/slide. Giữ các file lịch sử.
Các builder có sẵn trong scripts. Chạy test tương ứng sau khi sửa nội dung.
Render Word thành PDF và kiểm từng trang. Kiểm mục lục, hình, bảng, font,
đơn vị và nguồn. Việc test nội dung đạt không chứng minh bố cục đã đạt.
