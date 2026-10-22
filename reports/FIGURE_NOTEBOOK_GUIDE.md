# Notebook xuất hình E0–E4 cho báo cáo và slides

## Chạy trên Colab

1. Upload `notebooks/Face_PAD_Export_All_Figures_E0_E4.ipynb` vào Colab.
2. Chọn GPU (A100/T4 đang có sẵn), rồi **Run all** và cho phép mount đúng Drive.
3. Source ZIP `DeepFace-PAD-Figures-source.zip` tự lấy từ
   `face-pad/handoffs/figures-e0-e4-20261016/`; nếu không thấy, cell 0.2 yêu cầu upload.
4. Đợi `FIGURES_COMPLETE: 31 hình`. Notebook lưu output timestamp mới trong
   `face-pad/reports/figures-e0-e4-<UTC>/` và tự tải ZIP về máy.

Không cần chạy lại notebook training. Mỗi lần xuất tạo thư mục mới; giữ các
output cũ để đối chiếu. Nếu runtime thiếu dữ liệu, phần restore chỉ trích các
frame/target cần dùng từ archive hiện có. Runtime hiện tại còn dataset sẽ nhanh hơn.
Thời gian tùy GPU và Drive; cell xuất in tiến độ liên tục.

## Bộ hình và cách dùng

Có 20 hình thống kê + 1 MAE đủ năm depth model + 1 RGB overview + 7 case depth/
error map + 2 efficiency = **31 hình**, mỗi hình ba định dạng. Tổng 93 file hình,
chưa tính CSV/JSON/caption. `png/` dùng chèn Word/slides; `pdf/`/`svg/` để phóng lớn.
`INDEX.html` xem bộ hình sau giải nén, `CAPTIONS.csv` chọn caption đúng ngữ cảnh.

Cho slides ngắn, ưu tiên 01 pipeline, 03 split, 05 test metrics, 06 error rates,
12 paired errors, 13 quality, 15 depth MAE, một case 17 và 18 efficiency common256.
ROC, confusion matrix, các curve và case còn lại phù hợp phần giải thích/phụ lục.
Hình nhiều panel và bảng rộng nên dùng trang ngang trong báo cáo, hoặc để đủ
chiều rộng slide; không thu nhỏ đến mức chữ/caption khó đọc.

## Nguyên tắc bằng chứng

Phạm vi: đọc sáu run seed 42 đã hoàn tất E0, Official E1, E2, E3, E3b và E4.
Không train, không đổi threshold hoặc chọn lại model từ test. E1-Lite/smoke
không vào bảng chính. Báo cáo Word và những file người dùng đang sửa được giữ nguyên.

Input phải khớp hash đã kiểm toán: manifest, checkpoints, raw score và freeze
trước test. Mọi phép vẽ dùng số thực tế, đơn vị frame/video tách rõ. Một seed
không có error bar giả của nhiều seed. MAE là sai lệch với pseudo-depth.

Module `figure_data.py` kiểm tra input và chọn case định trước theo nhóm kết
quả, một frame giữa video. Khôi phục riêng RGB/target cần dùng từ ZIP/TAR cũ
nếu runtime mới thiếu file; map được đối chiếu hash E1. Không sinh lại 3DDFA,
không ghi đè file dữ liệu khác hash. Ảnh minh họa không phải mẫu ngẫu nhiên.

Các hình thống kê gồm pipeline, lịch train, số người/video/frame theo split,
depth QA, bảng validation/test, APCER/BPCER/ACER, ROC đầy đủ và zoom, phân bố
score, confusion matrix, sáu đường học riêng theo stage, chọn checkpoint BCE,
paired errors, subgroup quality và ma trận các video sai. Không nối các loss
khác objective qua ranh giới stage. Histogram có 25 bin chung, chuẩn hóa trong
từng lớp; E1 depth score và sigmoid head được ghi rõ khác thang ý nghĩa.

Mỗi hình xuất PNG 300 dpi, PDF, SVG và CSV nguồn, caption. Trục bar bắt đầu
từ zero, không thêm CI/SD giả cho một seed. Bộ xuất từ chối ghi đè hình đã có;
chạy lại dùng một thư mục output mới. `INDEX.html` và `figure_manifest.json`
ghi danh sách, caption, kích thước và checksum để kiểm tra kết quả.

Phần GPU xuất thêm MAE validation E1/E2/E3/E3b/E4 trên cùng target, gallery RGB,
bảy panel case gồm RGB/target/mask/prediction/error map, và hai hình hiệu năng.
Mỗi case dùng **quyết định video đã lưu**, không gán lỗi frame cho toàn video.
Depth/error dùng thang màu chung toàn bộ case/model; không chuẩn hóa lại từng
ảnh, không clamp prediction. RGB đảo đúng normalization của model.

MAE baseline E1/E2 là phép đo inference bổ sung trong phiên xuất hình, ghi riêng
ở output; không sửa `depth_val_metrics.json` trong run cũ. Score validation
reproduced được đối chiếu score đã lưu, tolerance tuyệt đối 10^-3 cho khác backend;
diff được ghi rõ và vượt ngưỡng sẽ dừng. MAE ba nhánh mới cũng được đối chiếu.

Benchmark cùng GPU/session, FP32 batch 1: năm vòng đổi thứ tự model, 20 warm-up
và 50 lần đo mỗi vòng. Báo p50/p95, không gọi là CI. Có cả input native (E0 224,
CDCN 256) và input chung 256 để tách ảnh hưởng kích thước. Chỉ đo dispatch +
forward có CUDA synchronize; không gồm crop, đọc file, transfer hoặc webcam.

CLI `scripts/export_report_figures.py --phase numeric` chạy CPU để vẽ số liệu;
`--phase all` cần GPU để chạy inference/timing có giới hạn. Không gọi train,
không đánh giá lại toàn test và không sửa original run. Thư mục output phải
nằm ngoài `runs/`. Toàn bộ pixel/weights vẫn ở artifact riêng của người dùng.

## Kiểm tra trước bàn giao

Đã chạy xuất **20 hình thống kê thật** từ các run trên Drive, đối chiếu metric,
xem trực tiếp các hình pipeline/bảng/quality và kiểm tra PNG/PDF/SVG. Đã suy
luận thử **một case thật bằng cả năm depth model trên CPU**, score khác score
đã lưu dưới 10^-3; đã xem panel RGB/target/mask/prediction/error map.

Kiểm thử cục bộ: **80 passed, 31 subtests passed**. Test benchmark dùng model
nhân tạo và timing CPU giả lập trong thư mục test tạm để kiểm tra số lượt,
thứ tự và kích thước input; đó không phải số latency nghiên cứu. Full MAE
validation E1/E2 và benchmark GPU sẽ được đo thật khi người dùng Run all trên
Colab. Chưa khẳng định đã chạy trọn phần GPU tại máy cục bộ không có CUDA.
