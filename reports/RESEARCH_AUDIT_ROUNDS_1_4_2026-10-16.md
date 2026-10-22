# Rà soát Lượt 1 đến 4 và điều kiện tiếp tục E3 E4

Ngày rà soát: 16/10/2026. Theo yêu cầu mới, tạm dừng điền báo cáo cuối kỳ và
tiếp tục nghiên cứu trên **chính bộ CASIA-FASD đã dùng cho Official E1/E2**.
Không đổi split, lấy thêm frame, tạo lại nhãn 3DDFA hoặc train lại run đã hoàn tất
chỉ để làm sạch lịch sử. E3/E4 chưa có kết quả trong các nơi đã kiểm tra.

## Phạm vi và nguồn kiểm tra

Đã kiểm kê thư mục repository, gồm mã nguồn, 18 script Python, 13 file test,
cấu hình, bốn notebook, báo cáo, sơ đồ, slide, bản thảo và artifact cục bộ.
16 module trong `src/`, toàn bộ script và test Python parse được. Notebook có
output được đọc như bằng chứng lịch sử, không chạy lại. Các thư mục môi trường,
cache và metadata Obsidian được nhận diện trong kiểm kê; không coi chúng là
kết quả nghiên cứu.

Đã truy cập trực tiếp Drive qua connector và `G:/My Drive/face-pad/`: có 9 thư
mục run và 3.183 file dưới `runs/`, `reports/`, `depth-checkpoints/`. Sao chép
123 file cấu hình, log, JSON, CSV và checkpoint, tổng 72.508.097 byte, vào
`artifacts/research-audit-20261016/drive-snapshot/`. Không sửa file trên Drive.
Danh mục và SHA-256 của bản sao ở `snapshot-manifest.json`; danh mục đầy đủ ở
`drive-inventory.json` và `local-inventory.json` cùng thư mục audit.

File ZIP dữ liệu 2.198.264.547 byte vẫn nằm trong `face-pad/`. Phiên này không
giải nén và đọc lại toàn bộ ảnh RGB trong ZIP. Phép kiểm tra mẫu và chia tập dựa
trên manifest đã lưu, đối chiếu nhãn của từng frame/video score với manifest.
Không gọi kiểm kê là đã đọc nội dung mọi file môi trường hoặc ảnh dữ liệu.

Kết quả số và kiểm tra checkpoint được lưu tại
`RESEARCH_AUDIT_ROUNDS_1_4_2026-10-16.json`. Script kiểm tra một lần và bản raw
nằm trong thư mục artifact được Git ignore; không commit weights, score CSV,
notebook có output hoặc ảnh sinh trắc học.

## Trạng thái thực tế Lượt 1 đến 4

| Lượt | Phần đã có bằng chứng | Phần cần ghi đúng phạm vi |
| --- | --- | --- |
| 1 | Đặc tả, câu hỏi nghiên cứu, literature matrix, khung protocol, sơ đồ và các phần slide liên quan | A/B là phân công dự kiến; chưa tự gán thành tích lịch sử cho Đạt/Quân. Không gọi công trình đã khảo sát là mới nhất hiện nay. |
| 2 | Manifest, validator, metric, E0 5 epoch, checkpoint và validation/test score đầy đủ | E0 là mô hình tham khảo. E0/E1 khác backbone, loss và tiền xử lý nên không cô lập riêng tác dụng của độ sâu. |
| 3 | Cache 3DDFA, provenance, QA, Official CDCN, run E1 30 epoch, checkpoint epoch 25 và raw score | Tái lập topology/loss theo mã CDCN trong protocol nhóm; chưa tái lập số benchmark của paper. Pilot được giữ như lịch sử. |
| 4 | E2 frozen head 10 epoch, checkpoint epoch 1, kiểm tra backbone, raw validation/test, paired errors, params và latency | E2 chưa cải thiện ACER. Latency chỉ là phép đo forward sơ bộ, không chứng minh E2 nhanh hơn. |

Lượt 1–4 đã có lõi thí nghiệm và minh chứng phục vụ báo cáo. Việc hai người đã
thuyết trình, tham dự, rehearsal hoặc nộp file đúng nơi không được suy ra chỉ từ
file kỹ thuật. Các mục đó cần xác nhận thực tế nếu dùng làm điều kiện nghiệm thu.

## Dữ liệu đã khóa

| Tập | Người | Video | Frame | Tấn công / thật theo video |
| --- | --- | --- | --- | --- |
| Train | 16 | 192 | 3.840 | 144 / 48 |
| Validation | 4 | 48 | 960 | 36 / 12 |
| Test phát triển | 30 | 360 | 7.200 | 270 / 90 |

Đã kiểm tra 12.000 sample ID không trùng, 20 frame/video, không có người hoặc
video xuất hiện ở hai split. Validation gồm người 4, 9, 14, 19. Source manifest
được khôi phục từ manifest có depth bằng cách giữ nguyên mọi cột và bỏ giá trị
`depth_path`; checksum byte khớp source manifest đã ghi trong E0.

- Source manifest SHA-256: `58fffcc2fb29649af1b8424d78b85067eefbd0321fde6b27fbd0803ef0fd7192`.
- Manifest có depth SHA-256: `4c302c9039e48a8ea6baedf426b26e1b0a6663bc295c661bb71fefccdb9b37fd`.

Đã đọc 3.000 live map trong TAR cache và kiểm tra từng hash, shape, giá trị hữu
hạn, map không rỗng với `depth_input_snapshot.json` của E1: không lệch. Hash
TAR là `26cfa7f26d61e3a71372404008f5dc9dd696af931172850986a8642e440b3d80`.
9.000 hash attack map trong snapshot khớp byte của NPY zero 32×32 float32 do
NumPy tạo. Đây là đối chiếu mẫu zero được tái tạo, không phải đọc lại 9.000 file
attack vật lý trên Drive. Colab vẫn phải chạy QA trước run mới.

CASIA đang dùng là protocol phát triển do nhóm xác định. Test đã được quan sát
từ các lượt trước. Giữ dataset này là quyết định mới của người dùng; không tiếp
tục coi quyền truy cập OULU-NPU hoặc Replay-Attack là điều kiện chặn E3/E4.
So sánh với số paper khác protocol chỉ có vai trò đặt kết quả trong bối cảnh.

## Kết quả kiểm toán raw artifact

Đã tính lại metric từ video CSV tại **ngưỡng validation đã lưu**, không chọn lại
ngưỡng test. Đã kiểm tra điểm video bằng trung bình frame, nhãn và ID khớp
manifest, không trùng hàng. Sai khác metric và tổng hợp điểm đều dưới 10^-12.
Việc đọc lại score đã có không phải một lần score checkpoint trên test mới.

| Run chính | Epoch chạy / chọn | Ngưỡng đầy đủ | ACER test % | Lỗi attack / live |
| --- | --- | --- | --- | --- |
| E0 | 5 / 5 | 0,9900876432657242 | 5,5556 | 0/270 và 10/90 |
| Official E1 | 30 / 25 | 0,1916038803756237 | 2,7778 | 0/270 và 5/90 |
| E2 frozen head | 10 / 1 | 0,4117791514843702 | 2,7778 | 0/270 và 5/90 |

Validation của cả ba: APCER, BPCER, ACER, EER bằng 0; AUC bằng 1. E0 best loss
validation là 0,0028055237858400; E1 là 0,0171712230582083; E2 là
0,0314531230570234. Giá trị loss trong checkpoint khớp dòng minimum trong log;
loss E1 và loss E0/E2 có ý nghĩa khác nhau, không so độ lớn trực tiếp.

| Checkpoint | SHA-256 tính lại từ file |
| --- | --- |
| E0 best.ckpt | `b8057fc7f7b3cce74fca079377f09ece1277dc9c8bfd10bb25f78b507c83502c` |
| Official E1 best.ckpt | `679810c001e526cafed8685fe731a7d5c539fd3fb9c5a9fb31725b7dbdf57024` |
| E2 best.ckpt | `a49d7c717e4cde27eac075de2d848c8816df3d27fcb0c01ea76ef752e15ff1b5` |

E2 `initial_checkpoint.json` trỏ đúng hash E1. Các hash config, threshold,
checkpoint và manifest trong `comparison_freeze.json` E2 khớp file thực tế.
Toàn bộ 73 state tensor E1 bằng tensor tương ứng trong `backbone.*` của E2,
gồm weights và buffer BatchNorm. Phiên này không tính lại mọi depth map từ RGB.

Paired errors kiểm tra lại từ 360 video: cùng đúng 355, E2 sửa 0, tạo lỗi mới 0,
cùng sai 5. Danh sách cùng sai là `casia_s21_vHR_1`, `casia_s23_v2`,
`casia_s30_v2`, `casia_s31_v1`, `casia_s39_v1`. Chưa đọc ảnh của đúng năm video
này, nên chưa kết luận nguyên nhân thị giác.

E1 có 2.245.016 tham số; E2 có 2.246.281, thêm 1.265. CSV latency khớp báo cáo:
p50 E1 4,519156 ms, E2 4,242899 ms; chỉ đo forward batch 1 trên A100. Cần đo lặp,
đổi thứ tự và giữ điều kiện chung trước khi đưa ra kết luận về tốc độ.

## Run lịch sử và run chưa hoàn tất

| Nhóm | Run hoặc số lượng | Trạng thái |
| --- | --- | --- |
| Chính | E0 full, Official E1 full, Official E2 full | 3 run đầy đủ validation và test |
| Pilot | `CASIA_E1_CDCN_seed42_20260921T024300Z` | Có test, ACER 14,0741%; không dùng làm E1 chính |
| Smoke | E0, Official E1, E1-Lite và E2 | 4 run có validation; không dùng làm kết quả chính |
| Chưa đủ artifact | `CASIA_E1_SMOKE_seed42_20260921T023118Z` | Chỉ có 4 file metadata, chưa có log/checkpoint/metrics; không coi là run hoàn tất và không tự suy ra nguyên nhân |

Không xóa hoặc chạy lại run chưa hoàn tất để che lịch sử. Không có E3/E4 trong
thư mục run chính, và tìm kiếm Drive theo `CASIA_E3`/`CASIA_E4` không trả kết quả.
Điều này áp dụng cho những nơi đã kiểm tra, không khẳng định không thể có file
khác ở tài khoản hoặc thư mục ngoài phạm vi truy cập.

## Những điểm lệch giữa kế hoạch và hiện trạng

Notebook lịch sử được kiểm tra ở trạng thái lưu hiện tại:

| Notebook | Code cell có execution count / tổng cell | Error output còn giữ |
| --- | --- | --- |
| E0 | 26 / 49 cell | Cell 39 ghi ModuleNotFoundError cũ; artifact hoàn tất có sau đó |
| Official E1 Rerun | 27 / 33 cell | Cell 16 còn lỗi materialize cũ, có bước sửa và execution sau đó |
| Round4 Official Frozen Head | 13 / 18 cell | Không có error output |
| Official E1 Clean | 0 / 25 cell | Bản phân phối sạch, không phải bằng chứng đã chạy |

Số bên phải là tổng mọi cell, gồm Markdown; không coi các cell chưa chạy là
lỗi thí nghiệm. Output lỗi cũ được giữ làm lịch sử, còn trạng thái hoàn tất của
run dựa vào log, checkpoint và raw score đã đối chiếu trực tiếp. Hai notebook
người dùng đang sửa được giữ nguyên; bản clean mới tách riêng.

1. README và kế hoạch còn ghi slide đang hoãn, trong khi đã có deck 22 slide,
   speaker script, nguồn nội dung và test artifact. Cần cập nhật trạng thái kỹ thuật,
   vẫn để ngỏ việc đã trình bày hoặc nộp.
2. Checklist Lượt 4 chưa đánh dấu dù E2 đã có đủ bảng, paired errors và chi phí.
3. Mục Lượt 3 nói validation cases gồm cả đúng và sai. Validation E1 không có lỗi;
   các case đúng gần ngưỡng không được gọi là năm video test cùng sai.
4. Yêu cầu benchmark chính thức và hạn 27/09 là quyết định cũ. Phạm vi hiện tại
   chuyển sang CASIA cố định theo yêu cầu 16/10; không gọi đó là official protocol.
5. E3/E4 hiện chỉ là template chung `/content/data` và `all-with-depth.csv`,
   chưa phải config chạy tiếp CASIA. E3 chưa chỉ định init E1; E4 có stage head
   nhưng thiếu `init_checkpoint`, nên runner sẽ từ chối.
6. Runner chọn chung best validation loss giữa các stage. E4 dùng depth loss,
   classification loss rồi tổng loss; các trị số này không thể so như cùng một
   tiêu chí. Có thể nạp checkpoint head thay vì joint cuối. Cần sửa trước staged run.
7. Bộ test nền: **59 passed, 1 failed, 23 subtests passed**. Lỗi duy nhất là test
   bắt notebook E2 người dùng đã chạy phải không có output. Không xóa output để
   làm test xanh; cần tách bản clean để phân phối khỏi bản bằng chứng.
8. Chưa có depth MAE theo cùng mask, nhiều seed, đo latency lặp, bảng so paper
   tương thích hoặc webcam benchmark. Đây là việc còn lại, không gán là hoàn tất.

## Thứ tự tiếp tục

1. Giữ nguyên kết quả Lượt 1–4, cập nhật kế hoạch và trạng thái báo cáo tạm dừng.
2. Sửa chọn checkpoint theo từng stage; chọn đầu ra báo cáo ở stage cuối.
   Ghi stage và epoch trong checkpoint để truy nguồn. Kiểm thử tình huống loss
   stage trước thấp hơn stage sau để tránh hồi quy.
3. Chuẩn bị config CASIA cho E3 joint BCE, một nhánh staged BCE trung gian E3b,
   rồi E4 staged Focal. Cùng E1 initializer, manifest, input, augmentation,
   evaluator, ngân sách cập nhật và quy tắc chọn mô hình. E3–E3b trả lời về
   chiến lược; E3b–E4 trả lời về loss. Không dùng E3–E4 để quy riêng tác dụng Focal.
4. Chạy CPU preflight trước, kiểm tra GPU và checkpoint E1, rồi GPU smoke.
   Chỉ sau smoke mới full validation. Không tự chạy E0/E1/E2 cũ.
5. Khóa cấu hình theo validation, sau đó mới xem test phát triển của run mới.
   Giữ cả kết quả không cải thiện. Tăng seed cho E1 và cấu hình sửa đổi được chọn
   nếu tài nguyên cho phép; tất cả vẫn là bằng chứng CASIA phát triển.
6. Hoàn thành phân tích lỗi và chi phí rồi mới webcam, báo cáo/paper. ArcFace
   là phần mở rộng, không chặn thí nghiệm PAD.

Máy hiện tại dùng torch 2.11.0 CPU và không có CUDA. Việc train CASIA thật cần
người dùng mở Colab GPU. Mã kiểm tra và gói chạy sẽ được chuẩn bị tại máy này;
không tiêu hao GPU credit thay người dùng khi chưa đi qua cổng preflight/smoke.

## Khắc phục sau kiểm toán

Runner đã tách chọn checkpoint theo từng stage, khôi phục best của stage trước
trước khi vào stage sau, và chỉ báo checkpoint stage cuối. Metadata lưu stage,
epoch cục bộ và epoch toàn cục. Đã thêm kiểm thử mô phỏng trường hợp loss stage
đầu thấp hơn stage cuối; đây là test tính đúng của code, không phải kết quả CASIA.

Đã tạo `Face_PAD_Round4_Official_Frozen_Head_Clean.ipynb` riêng cho phân phối,
đổi builder/test sang file này, giữ nguyên hai notebook người dùng có output.
Nhóm test runner, loss và notebook sau sửa: **16 passed**. Kết quả kiểm thử nền
ở trên được giữ lại để thể hiện lỗi đã phát hiện, không thay lịch sử bằng số mới.
Toàn bộ bộ test sau sửa: **64 passed, 25 subtests passed** trên CPU.

Kiểm tra sâu đường xuất ảnh phát hiện `visualize_depth_cases.py` đảo chuẩn hóa
ImageNet ngay cả khi config dùng `cdcn_official`. Đã sửa để ảnh RGB dùng đúng
phép đảo theo config, thêm test bằng pixel có giá trị biết trước. Lỗi này ảnh
hưởng màu RGB của panel minh họa cũ, không thay input train, depth map hoặc
score đã lưu. Giữ nguyên ảnh lịch sử; ảnh mới dùng code đã sửa. Cần xuất lại
panel cũ trước khi dùng chúng để kết luận về ánh sáng hoặc màu da.

Đã thêm `scripts/evaluate_depth.py`: xuất MAE toàn ảnh theo lớp/frame/video,
và MAE trên mask target > 10^-6 cho live, đối chiếu cache đã lưu trước khi
inference. Không clamp prediction để che lỗi. Target là pseudo-depth sau tiền
xử lý, không phải đo 3D thật. Test thống kê MAE và đảo chuẩn hóa: **3 passed**.
Chưa chạy depth MAE CASIA trên máy CPU trong phiên này.

Đã chuẩn bị ba config CASIA, notebook Lượt 5 sạch và
`ROUND_5_CASIA_RUNBOOK.md`. Tiêu chí checkpoint mới dùng validation BCE chung
cho head/joint của E3/E3b/E4; `val_loss` vẫn ghi objective gốc. Test stage và
objective sau mở rộng: **16 passed**; test cấu hình và các cổng notebook:
**2 passed**. Đây là chuẩn bị chạy, chưa có GPU smoke hoặc số E3/E4.

Bộ test toàn repository sau các thay đổi: **71 passed, 26 subtests passed**,
21,24 giây trên CPU. Đã khai báo `python-docx` trong extra `dev` vì test scaffold
báo cáo cần thư viện này khi chạy toàn bộ tests ở môi trường Colab mới. Bản
Word/bản thảo không được điền thêm. Kiểm thử môi trường cục bộ không thay thế
preflight, GPU smoke hoặc train trên CASIA.
