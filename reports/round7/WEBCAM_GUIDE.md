# Đo webcam Lượt 7 trên Windows

Chạy từ repository. Model E3 seed 43 là seed đầu tiên đã đăng ký; không chọn
seed từ test. Config `configs/round7_webcam.json` khóa ngưỡng validation,
median 5 frame, warm-up 5 forward, 5 camera settle reads; CPU 2 thread.
Detector hiện tại YuNet 2023mar, confidence 0,5; OpenCV 4.14.0 cô lập. Crop
đúng rectangle không margin, RGB resize 256² và official normalization. API:
[FaceDetectorYN](https://docs.opencv.org/4.13.0/df/d20/classcv_1_1FaceDetectorYN.html).

Không có mặt/nhiều mặt/score lỗi: xóa buffer và không nhận live. Mất liên tục
quá 5 giây hoặc IoU box <0,4 cũng reset. IoU chỉ là heuristic về vị trí,
không chứng minh cùng danh tính nếu đổi người ngay tại cùng vị trí. Cửa sổ
chưa đủ: collecting. Quyết định dùng median >= threshold; không chỉnh ngưỡng.

1. Đóng Teams/Zoom/Camera nếu đang chiếm webcam. Mở PowerShell tại root.
2. Thiết lập môi trường và kiểm camera:

```powershell
$env:PYTHONPATH = ((Join-Path (Get-Location) 'artifacts/round7/demo-runtime') + ';' + (Join-Path (Get-Location) 'src'))
python scripts/run_round7_webcam.py --probe --no-preview --output artifacts/round7/camera-probe-user-01
```

3. Khi camera đọc được, chạy cảnh người thật 45 giây. Nhìn thẳng, quay nhẹ,
rời khỏi khung hình rồi quay lại để kiểm reset. Cửa sổ hiển thị trạng thái;
nhấn Q nếu cần dừng sớm. `n/5` đếm frame hợp lệ, không đếm giây. Đủ 5 frame
thì quyết định ngay; giữ mặt 15 giây chỉ là hướng dẫn để quan sát ổn định.
`no_face` nghĩa detector không tìm thấy box, không khẳng định mặt không có
trong ảnh. Rời/quay lại là bài kiểm reset riêng, không cần rời để lên 5/5.

```powershell
python scripts/run_round7_webcam.py --scenario live --output artifacts/round7/webcam-live-01
```

4. Chạy riêng cảnh ảnh in khuôn mặt trên giấy, rồi cảnh video khuôn mặt trên
điện thoại. Đưa khuôn mặt của người cầm ra ngoài ảnh; tránh hai mặt đồng thời.
Mỗi lệnh mở phiên mới, không mang buffer từ cảnh trước.

```powershell
python scripts/run_round7_webcam.py --scenario print --output artifacts/round7/webcam-print-01
python scripts/run_round7_webcam.py --scenario replay --output artifacts/round7/webcam-replay-01
```

5. Nếu tái hiện được lỗi, ghi thêm `--scenario failure` vào thư mục mới.
Không bắt buộc dựng một lỗi giả. Sau mỗi lần chạy gửi đường dẫn `summary.json`
để đối chiếu với `frames.csv` và `backup.avi`. Không xóa lần chạy lỗi; đổi hậu
tố thư mục cho lần sau. Camera khác index 0: tạo bản config riêng bằng
`--config`, giữ model/threshold/window và ghi rõ thay đổi thiết bị.

Log lưu tại output bạn chọn (Git-ignore). `delivered_loop_fps` đo vòng serial
read→detect→crop→PAD→median→ghi video/preview, kể cả frame không có mặt;
`model_processed_fps` chỉ tính số forward thật chia cùng thời lượng. Không
gọi số thứ nhất là tốc độ cảm biến camera. Warm-up/settle và flush file cuối
được loại khỏi timing. Time-to-decision tính từ lúc bắt đầu đọc frame đầu
tiên của đoạn một mặt liên tục đến quyết định đủ median window; không đo từ
lúc mặt xuất hiện vật lý trước camera. Mỗi episode ghi một first decision.
Nếu không đủ window thì không có TTD, không ghi 0 thay cho thiếu dữ liệu.

AVI mã hóa cố định 10 FPS để dự phòng; timestamps CSV mới là thời gian thực.
Nhãn live/print/replay do người chạy khai báo, không phải benchmark được
chứng thực. Demo khác domain và khác cách tổng hợp mean 20 frame/video CASIA;
ngưỡng cũ chưa được hiệu chỉnh cho webcam. Không dùng demo thay kết quả Lượt 6.

Thiết bị người dùng hiện có: webcam laptop và điện thoại, chưa có giấy in.
Có thể chạy live và replay. Ảnh tĩnh hiển thị trên điện thoại phải ghi riêng
`--scenario screen_photo`, không thay cho print. Cảnh print để thiếu cho đến
khi có mẫu giấy; không đánh dấu tiêu chí print hoàn tất.

Ngưỡng được chép đúng từ `threshold.json` đã kiểm SHA: 0.3983212910592556.
Lượt `webcam-live-01` bị guard chặn trước camera vì bản config ban đầu dùng
0.39832129105925557 từ trường validation của báo cáo (lệch 1 ULP). Giữ log
thất bại đó; bản sửa không chọn hay điều chỉnh threshold từ test/webcam.

## Cấu hình sau pilot Haar

Lượt Haar live-02 có 450 frame/30,399 giây nhưng chỉ 2 forward, không đủ
median window; giữ là detector failure, không báo TTD bằng 0. Forward thực
1,74–2,23 giây vượt gap cũ 1 giây. Trước lượt tiếp theo đổi gap lên 5 giây,
thời lượng lên 45 giây và dùng YuNet 2023mar từ OpenCV Zoo, SHA và source
commit ghi trong config. Không đổi PAD checkpoint, ngưỡng hay window 5.
Mô hình detector dùng input 320² cố định (phù hợp ONNX static trên OpenCV 5);
box được scale về camera gốc, PAD crop vẫn từ frame gốc. Xem [nguồn YuNet](https://github.com/opencv/opencv_zoo/blob/48b10fa505aeb51fbd127fc60a5c660040e823b7/models/face_detection_yunet/README.md).

Mặc định cửa sổ READY chờ Space (tối đa 180 giây), chỉ bắt đầu timing sau khi
người dùng nhấn Space. Chọn cửa sổ camera, nhấn Space khi mặt đã ở trong khung;
giữ mặt ít nhất 15 giây trước khi thử rời khung 2 giây rồi quay lại. Nếu thuận
tiện, xoay hướng để mặt nhận ánh sáng từ phía trước. Chờ READY không vào FPS.
Chế độ không preview cần `--start-mode automatic` rõ ràng. Không cần tham số
mới cho các lệnh live/replay ở trên; mặc định đã chờ Space và đo 45 giây.

Kiểm detector offline trên hai frame pilot có mặt: cutoff mặc định 0,9 loại
hết, confidence cao nhất tương ứng khoảng 0,871/0,607 trên OpenCV 4.14.0.
Chọn confidence detector 0,5 trước lượt đo mới; đây là sửa frontend từ pilot,
không dùng score PAD để chọn và không thay PAD threshold 0,3983212910592556.
Kiểm ONNX Runtime trên OpenCV 5 báo build không có ORT; không kết luận đó là
nguyên nhân duy nhất của bỏ lỡ mặt. Runtime 4.14.0 được cài riêng ở artifacts,
không thay package OpenCV 5 của môi trường gốc. Nếu chuyển máy:

```powershell
python -m pip install --no-deps --target artifacts/round7/demo-runtime opencv-python==4.14.0.94
```

Khôi phục ONNX từ `detector_source` trong config vào `detector_model`, đối
chiếu `detector_model_sha256` trước chạy. Không tải lại hoặc ghi đè file
đã có nếu chưa kiểm hash. Phiên này đã tải đúng file và hash nguồn OpenCV Zoo.
