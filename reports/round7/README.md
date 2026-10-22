# Lượt 7: phân tích lỗi, hình và webcam

Trạng thái 22/10/2026: [Results/Discussion và thực đo](ADDENDUM_RESULTS_DISCUSSION_2026-10-22.md).
Hình hoàn tất ở `figures-attempt03/`; attempt02 là lần strict dừng. Chưa chốt
toàn bộ Lượt 7: thiếu print, frontend/PAD còn lỗi và chưa ghép addendum Word.

Nguồn: Lượt 6 đã khóa, E1/E3 seed 43/44/45; ngưỡng riêng từ validation.
Không sửa benchmark, không train lại. Word/paper lịch sử được giữ nguyên.

Chạy CPU từ root bằng Python đã cài project:

```powershell
python scripts/analyze_round7.py
```

Output mới `analysis/`: paired_videos.csv, subgroups.csv (số lỗi/mẫu số;
mẫu số 0 để rate trống), case_index.csv, case_coverage.csv và analysis.json
ghi hash nguồn. Lệnh từ chối ghi đè thư mục output đã tồn tại.

Quy tắc trước khi xem RGB: trong mỗi seed/nhóm kết quả/attack_type, chọn
video đầu tiên theo thứ tự ID; chọn frame vị trí len//2 sau khi sắp thời gian
(frame thứ 11/20). Giữ corrected/new_errors/both_wrong/both_correct; nhóm
rỗng được ghi rõ. Không dùng score mới để thay kết quả video mean 20 frame.

Ba seed dùng lại 360 video, không tạo 1.080 quan sát độc lập. quality không
là phép đo ánh sáng hay blur. Phân tích ảnh là mô tả, không chứng minh nhân quả.
Phần figure và đo camera chỉ được ghi hoàn tất khi có artifact thực tế.

## Hình minh họa có giới hạn

Sau khi chốt case index, dùng output mới để giữ các lần chạy trước:

```powershell
python scripts/render_round7.py --score-mode diagnostic --output artifacts/round7/figure-reproduction-new --artifacts artifacts/round7/figure-inputs-new
```

Lệnh kiểm hash sáu checkpoint/config/snapshot; lấy riêng RGB từ ZIP và target
đã lưu trên Drive. Target phải khớp snapshot của cả hai model trong từng seed.
Không tạo lại 3DDFA hoặc tạo score CSV benchmark mới. New frame score chỉ để
đối chiếu đầu vào với saved frame score (atol=1e-5, rtol=1e-4 do CPU/CUDA).

`figures/` chứa PNG, selected manifest, bounded inference CSV và provenance.
Mảng prediction/target/absolute error và input trích xuất nằm riêng ở
`artifacts/round7/figures/` (Git-ignore). Tất cả panel dùng chung thang màu,
không clipping prediction. RGB hash mới ghi từ ZIP, không gọi đó là hash RGB
đăng ký trước train. MAE từng frame minh họa không thay depth metric toàn test.

Archive depth gốc không chứa các attack constant. Khi thiếu target attack,
khôi phục serialization zero float32 32² và chỉ chấp nhận nếu SHA khớp chính
xác snapshot đã khóa; ghi rõ cách khôi phục trong provenance. Thiếu target
live thì dừng, không chạy lại 3DDFA. Lần dựng hình đầu dừng do thiếu attack
target được giữ tại các thư mục `figures/` ban đầu; lần kế dùng output mới.

## Webcam

Xem [hướng dẫn từng bước](WEBCAM_GUIDE.md). Config được chốt trước đo tại
`configs/round7_webcam.json`; test clock/frame fixture không phải log camera.
Chỉ báo FPS/time-to-decision sau khi có `summary.json` và timestamps thực.

Đã có năm lượt video/timestamps: [kiểm toán log](WEBCAM_RESULTS.json).
`n/5` đếm frame, không đếm giây. `no_face` chỉ là detector không có box,
không chứng minh mặt vật lý đã rời khung. Lượt reset riêng khi quay lại mới
đạt 2/5 trước hết giờ; giữ mọi lượt lỗi và không tuyên bố hoàn tất chu trình.

## Chênh lệch số học khi dựng hình

Lần attempt02 dừng vì một frame E1_43 có score CPU 0,00155432755 so với saved
CUDA 0,00152643840. Kiểm một frame bằng CPU batch 1/2, tắt MKLDNN và float64
cho kết quả gần nhau; chưa xác định nguyên nhân với CUDA cũ (không ghi TF32).
Giữ diagnostic JSON tại `artifacts/round7/numeric-diagnostic.json` và receipt
thất bại attempt02. Source model/data/train không đổi so với source Lượt 6.

Chế độ mặc định `strict` vẫn dừng tại atol=1e-5, rtol=1e-4. Để xuất hình
minh họa CPU mà giữ mọi sai khác, dùng rõ `--score-mode diagnostic` và thư
mục mới. Không nới tolerance; CSV vẫn ghi `score_reproduction_passed=false`
cho mọi ca không đạt. Hình không được gọi là tái lập chính xác score CUDA.
Đây là inference minh họa mới từ checkpoint đã khóa, không phải score test
thay thế. Video decision hiển thị luôn dùng CSV cũ đã xác minh.
