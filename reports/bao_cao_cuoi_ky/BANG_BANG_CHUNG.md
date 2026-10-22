# Bảng bằng chứng cho kết quả E0 Official E1 và E2

**Cập nhật 16/10/2026:** phần dưới giữ lịch sử đối chiếu ngày 15/10. Các câu
“chưa tải CSV/checkpoint” và ngưỡng E2 chỉ có tám chữ số là trạng thái lúc đó.
Sau đó đã kiểm toán artifact E0/E1/E2 và full validation/test E3/E3b/E4.
Nguồn hiện hành là [kiểm toán lượt 1–4](../RESEARCH_AUDIT_ROUNDS_1_4_2026-10-16.json),
[full validation lượt 5](../ROUND_5_FULL_VALIDATION_2026-10-16.json) và
[test lượt 5](../ROUND_5_TEST_RESULTS_2026-10-16.json).
Metadata đầy đủ lấy từ các JSON này, không chép thêm chữ số từ ảnh.

Bản hoàn thiện dùng cả sáu cấu hình. ACER test E0/E1/E2/E3/E3b/E4 lần lượt
5,5556% / 2,7778% / 2,7778% / 5,0000% / 5,0000% / 4,4444%; đơn vị video,
270 attack và 90 live, seed 42. E3 vẫn chọn từ validation. Phép đối chiếu là
đọc/tính lại artifact đã lưu, không train mới.

Đối chiếu ngày 15/10/2026, phục vụ Khối 1 của báo cáo cuối kỳ. Các số dưới đây
được đọc từ output lưu trong ba notebook cục bộ và đối chiếu với báo cáo, cấu
hình, mã huấn luyện và mã đánh giá. Không chạy lại thí nghiệm trong lần kiểm tra
này. Chưa tải lại checkpoint, CSV dự đoán hoặc JSON kết quả từ Google Drive để
tính lại metric độc lập.

E0 là mô hình MobileNetV3-Small phân loại ảnh RGB trực tiếp. Official E1 là mạng
CDCN, tên đầy đủ Central Difference Convolutional Network, dùng trung bình bản
đồ độ sâu dự đoán làm điểm. E2 nạp checkpoint E1, giữ cố định mạng tạo độ sâu và
chỉ học bộ phân loại nhỏ đọc bản đồ đó. Phép so sánh chính là E1 với E2; E0 dùng
làm mô hình tham khảo. E1-Lite Pilot và các run smoke không nằm trong bảng chính.

## 1 Quy ước truy nguồn

Số cell trong tài liệu này **đếm từ 1, gồm cả cell Markdown và code**. Ký hiệu
`exec` là `execution_count` lưu trong notebook, không phải số cell. Không suy ra
thứ tự thực thi chỉ từ vị trí cell. Các đường dẫn sau tính từ gốc repository.

| Mã nguồn | File | Vị trí đã đọc |
| --- | --- | --- |
| N0 | `notebooks/E0.ipynb` | Cell 15, exec 8: chia tập; cell 33, exec 17: config full; cell 34, exec 18: run ID; cell 35, exec 19: log và validation; cell 43, exec 26: checkpoint, ngưỡng và test; cell 47, exec 29: lỗi test |
| N1 | `notebooks/Face_PAD_Official_CDCN_E1_Rerun.ipynb` | Cell 7, exec 6: verifier; cell 23, exec 20: run ID; cell 24, exec 21: validation, best epoch và ngưỡng; cell 28, exec 24: test; cell 29, exec 25: lỗi; cell 30, exec 26: bảng phần trăm; cell 32, exec 28: curve E0 và Official E1 |
| N2 | `notebooks/Face_PAD_Round4_Official_Frozen_Head.ipynb` | Cell 10, exec 7: config và SHA-256 E1; cell 11, exec 8: kiểm tra đối chứng; cell 12, exec 9: run full và backbone đóng băng; cell 13, exec 10: validation và best epoch; cell 15, exec 11: test; cell 16, exec 12: lỗi ghép cặp; cell 17, exec 13: chi phí |
| R0 | `reports/CASIA_E0_BCE_5E_seed42_summary.md` | Run ID, ngưỡng, validation, test và số lỗi; số thập phân trong bảng đã làm tròn |
| R1 | `reports/MIDTERM_ROUNDS_1_3_AUDIT.md` | Chỉ mục “Official-CDCN E1 correction” và phần protocol; bỏ các bảng E1-Lite khi chọn kết quả chính |
| R2 | `reports/CASIA_E2_OFFICIAL_HEAD_FROZEN_seed42_summary.md` | Đối chứng E1–E2, checkpoint chọn ở epoch 1, số lỗi và giới hạn |
| C0–C2 | `configs/casia_e0_bce_5e.yaml`; `configs/casia_e1_cdcn_official.yaml`; `configs/casia_e2_official_head_frozen.yaml` | Seed, số epoch, đầu vào, manifest, loss và khởi tạo |
| M | `src/deepface_pad/metrics.py` | Đơn vị, chiều điểm, tổng hợp video, ngưỡng và cách tính EER/AUC |
| T | `src/deepface_pad/train.py`; `scripts/score_checkpoint.py` | Lưu và nạp `best.ckpt`, chọn ngưỡng validation, giữ ngưỡng khi score test |

N0, N1, N2 đều có output thực thi được lưu. N0 cell 39 còn lỗi import cũ, sau đó
cell 40–41 nạp package thành công và cell 43 có kết quả test. N1 cell 16 còn lỗi
materialize cũ, exec 14; cell 15, exec 15 bổ sung zero-map và materialize thành
công, rồi cell 17, exec 16 xác nhận provenance, manifest và QA. Giữ nguyên các
lỗi lịch sử này. Không gọi notebook là bản đã chạy thẳng từ đầu đến cuối trong
phiên hiện tại.

## 2 Các run được dùng

Mỗi run là một lần huấn luyện có thư mục kết quả riêng. Cả ba run mang seed 42,
tức giá trị khởi tạo ngẫu nhiên được ghi trong cấu hình. Thư mục chung trên Colab
là `/content/drive/MyDrive/face-pad/runs/`; tên trong bảng nối vào sau đường dẫn này.

| Phương án | Run ID | Cấu hình đã đối chiếu |
| --- | --- | --- |
| E0 | `CASIA_E0_BCE_5E_seed42_20260920T082941Z` | C0; N0 cell 33–35 |
| Official E1 | `CASIA_E1_CDCN_OFFICIAL_seed42_20260921T114029Z` | C1; N1 cell 23–24; N2 cell 10 kiểm tra lại config E1 |
| E2 frozen head | `CASIA_E2_CDCN_OFFICIAL_HEAD_FROZEN_seed42_20261001T155213Z` | C2; N2 cell 10 và 12 |

E0 dùng `casia_fasd_debug.csv`; E1/E2 dùng bản thêm đường dẫn nhãn độ sâu
`casia_fasd_debug_with_depth.csv`. N2 cell 10 so checksum manifest với bản E1
đã lưu, cell 11 tái tạo điểm validation E1 và báo PASS. Đây là bằng chứng lưu
trong notebook; lần này chưa đọc manifest/CSV gốc để kiểm tra lại toàn bộ mẫu.

## 3 Tập dữ liệu và đơn vị đánh giá

Một video được lấy 20 frame; điểm video là trung bình điểm các frame. Nhãn 0
là tấn công, nhãn 1 là người thật. Điểm càng cao càng nghiêng về người thật;
video được chấp nhận là thật nếu điểm lớn hơn hoặc bằng ngưỡng. Bảng kết quả
dưới đây đều đánh giá theo video, không phải theo frame.

| Tập | Người | Video tấn công | Video thật | Tổng video | Tổng frame |
| --- | --- | --- | --- | --- | --- |
| Train | 16 | 144 | 48 | 192 | 3.840 |
| Validation | 4 | 36 | 12 | 48 | 960 |
| Test phát triển | 30 | 270 | 90 | 360 | 7.200 |
| Tổng | 50 | 450 | 150 | 600 | 12.000 |

Nguồn số video/frame: N0 cell 15. Số người: R1 và protocol trong
`data/README.md`; quy tắc chọn bốn người validation 4, 9, 14, 19 có ở
`scripts/prepare_casia_fasd.py` và N1 cell 10. Chưa đếm lại trên manifest gốc
trong phiên này. Validation dùng chọn checkpoint/ngưỡng; CASIA test đã được
quan sát từ giai đoạn E1 và là test phát triển khi so sánh E2, chưa phải phép
xác nhận độc lập hay đánh giá khác bộ dữ liệu.

## 4 Checkpoint và ngưỡng quyết định

Checkpoint là trạng thái trọng số được lưu. Mã T chỉ ghi `best.ckpt` khi loss
validation thấp hơn giá trị tốt nhất trước đó, sau đó nạp checkpoint này để
tạo điểm validation. Vì thế số epoch chạy và epoch được chọn là hai thông tin
khác nhau; không mặc định lấy epoch cuối.

| Phương án | Epoch chạy | Epoch chọn | Tiêu chí | Loss validation tốt nhất | Ngưỡng validation |
| --- | --- | --- | --- | --- | --- |
| E0 | 5 | 5 | BCE validation thấp nhất | 0,002806, số hiển thị 6 chữ số | 0,9900876432657242 |
| Official E1 | 30 | 25 | Official depth loss validation thấp nhất | 0,0171712230582083 | 0,1916038803756237 |
| E2 | 10 | 1 | BCE validation thấp nhất | Chưa có giá trị số được in trong output đã đọc | 0,41177915, số hiển thị 8 chữ số |

Binary Cross Entropy, viết tắt BCE, là loss phân loại nhị phân. E1 dùng loss độ
sâu nên không so trực tiếp độ lớn loss E1 với BCE của E0/E2. E0 epoch 5 được
suy ra từ minimum của đủ năm dòng log ở N0 cell 35 và quy tắc lưu checkpoint
trong T; chưa mở metadata của `best.ckpt` E0 để xác nhận độc lập. N1 cell 24 in
trực tiếp best epoch 25 và loss đầy đủ. N2 cell 13 in trực tiếp best epoch 1.

Checkpoint dùng để score của mỗi run là `<run>/best.ckpt`. N0 cell 43 và mã
`scripts/score_checkpoint.py` thể hiện việc nạp file này. E2 khởi tạo từ E1
`best.ckpt`; SHA-256 được in tại N2 cell 10 là:

`679810c001e526cafed8685fe731a7d5c539fd3fb9c5a9fb31725b7dbdf57024`.

Chưa tính lại hash checkpoint E1 trong phiên này. Hash checkpoint E0 và E2
không được in trong các output đã đọc; không thay chúng bằng hash notebook.
Ngưỡng E2 chỉ có độ chính xác hiển thị 8 chữ số, cần đọc `threshold.json` nếu
muốn dùng giá trị đầy đủ để score lại. Mỗi mô hình có ngưỡng riêng trên thang
điểm riêng; không dùng chung một ngưỡng cho E1/E2.

Theo mã M, ngưỡng được chọn trên validation bằng cách tối thiểu ACER; nếu hòa,
ưu tiên chênh lệch APCER/BPCER nhỏ hơn rồi ngưỡng nhỏ hơn. Khi score test, T
đọc ngưỡng đã lưu thay vì chọn lại trên test. Các output xác nhận các ngưỡng
đã dùng; lần này không chạy lại việc chọn ngưỡng.

## 5 Bảng validation

APCER (Attack Presentation Classification Error Rate) là tỷ lệ video tấn công
bị chấp nhận là người thật; BPCER (Bona Fide Presentation Classification Error
Rate) là tỷ lệ video thật bị từ chối. ACER (Average Classification Error Rate)
là trung bình hai tỷ lệ này. EER (Equal Error Rate) tóm tắt điểm gần cân bằng
hai loại lỗi khi quét ngưỡng. AUC (Area Under the Curve) là diện tích dưới
đường ROC (Receiver Operating Characteristic), đường biểu diễn khả năng chấp
nhận đúng và sai khi thay đổi ngưỡng. Bốn cột lỗi ghi phần trăm; AUC giữ thang 0–1.

| Phương án | APCER % | BPCER % | ACER % | EER % | AUC |
| --- | --- | --- | --- | --- | --- |
| E0 | 0,0000 | 0,0000 | 0,0000 | 0,0000 | 1,000000 |
| Official E1 | 0,0000 | 0,0000 | 0,0000 | 0,0000 | 1,000000 |
| E2 frozen head | 0,0000 | 0,0000 | 0,0000 | 0,0000 | 1,000000 |

Mỗi dòng: 36 video tấn công, 12 video thật, 48 video tổng; 0 chấp nhận sai,
0 từ chối sai tại ngưỡng riêng trong mục 4. Số lỗi được suy ra từ tỷ lệ 0 và
mẫu số video. N0 cell 35 in metric thô và số video; N1 cell 24 in validation;
N2 cell 13 in bảng HTML validation E1/E2. Không dùng bảng validation này làm
bảng test hoặc bằng chứng tổng quát hóa.

## 6 Bảng test phát triển tại ngưỡng đã khóa

| Phương án | APCER % | BPCER % | ACER % | EER % | AUC |
| --- | --- | --- | --- | --- | --- |
| E0 tham khảo | 0,0000 | 11,1111 | 5,5556 | 2,4074 | 0,997984 |
| Official E1 | 0,0000 | 5,5556 | 2,7778 | 2,2222 | 0,994444 |
| E2 frozen head | 0,0000 | 5,5556 | 2,7778 | 2,2222 | 0,994321 |

Mỗi dòng: 270 video tấn công, 90 video thật, 360 video tổng, seed 42. N0 cell
43 in dictionary test đầy đủ; N1 cell 28 in bảng thô làm tròn, cell 30 in
phần trăm; N2 cell 15 in bảng HTML phần trăm và AUC 6 chữ số. R0/R1/R2 khớp
kết quả ở độ chính xác trình bày tương ứng. Không suy ra chữ số bổ sung của
AUC E1/E2 từ các bảng đã làm tròn.

| Phương án | Chấp nhận sai / tấn công | Từ chối sai / thật | Đúng / tổng |
| --- | --- | --- | --- |
| E0 | 0 / 270 | 10 / 90 | 350 / 360 |
| Official E1 | 0 / 270 | 5 / 90 | 355 / 360 |
| E2 | 0 / 270 | 5 / 90 | 355 / 360 |

Nguồn: N0 cell 47, N1 cell 29, N2 cell 16. Kiểm tra số học:
E0 BPCER = 100 × 10/90 = 11,1111%; ACER = (0 + 11,1111…)/2 = 5,5556%.
E1/E2 BPCER = 100 × 5/90 = 5,5556%; ACER = 2,7778%. Các phép tính dùng phân
số gốc rồi mới làm tròn, không lấy số đã làm tròn để tính tiếp.

### Đối chiếu quyết định E1 và E2

| Trạng thái trên cùng video | Số video | Nguồn |
| --- | --- | --- |
| Cùng đúng | 355 | N2 cell 16: 270 tấn công và 85 thật |
| E1 sai, E2 đúng | 0 | N2 cell 16 chỉ có hai nhóm cùng đúng và cùng sai |
| E1 đúng, E2 sai | 0 | N2 cell 16 chỉ có hai nhóm cùng đúng và cùng sai |
| Cùng sai | 5 | N2 cell 16, khớp N1 cell 29 |
| Tổng | 360 | 355 + 0 + 0 + 5 |

| Video thật cùng bị từ chối | Chất lượng | Điểm E1 | Điểm E2 |
| --- | --- | --- | --- |
| `casia_s21_vHR_1` | high | 0,086989 | 0,043982 |
| `casia_s23_v2` | low | 0,110922 | 0,083687 |
| `casia_s30_v2` | low | 0,008739 | 0,002988 |
| `casia_s31_v1` | normal | 0,173621 | 0,311878 |
| `casia_s39_v1` | normal | 0,179061 | 0,385063 |

Điểm trong bảng là số hiển thị 6 chữ số từ N2 cell 16. Tất cả thấp hơn ngưỡng
tương ứng ở mục 4. Chưa xem RGB/depth của đúng năm video này, nên chưa quy lỗi
cho ánh sáng, góc mặt hoặc chất lượng hình. Trong điều kiện đã chạy, E2 chưa
giảm ACER và chưa đổi quyết định của video nào. AUC thấp hơn 0,000123 theo
hai giá trị hiển thị; chưa có nhiều seed hay khoảng tin cậy để kết luận ý nghĩa
thống kê. Không suy rộng rằng mọi bộ phân loại đọc độ sâu đều không hiệu quả.

## 7 Quy đổi đơn vị và cách tính metric

Trong mã M, `apcer`, `bpcer`, `acer`, `eer`, `auc` được lưu ở thang 0–1. Khi đưa
lên bảng báo cáo, nhân 100 cho bốn tỷ lệ lỗi, giữ nguyên AUC. Ngưỡng là điểm
quyết định, không phải phần trăm và không nhân 100.

N0 cell 43 có BPCER thô `0.1111111111111111`, ACER
`0.05555555555555555`, EER `0.024074074074074074` và AUC
`0.9979835390946502`. Chúng tương ứng với dòng E0 ở mục 6. Bảng R0 ghi BPCER
`0.1111`, ACER `0.0556`, EER `0.0241`; đây là các số thô đã làm tròn, không
phải 0,1111%, 0,0556% hay 0,0241%. Khi cần độ chính xác, dùng output N0 trước
khi nhân 100, không nhân các số bốn chữ số đã làm tròn của R0.

Mã `equal_error_rate` hiện chọn cặp APCER/BPCER có chênh lệch nhỏ nhất trên các
ngưỡng rời rạc rồi lấy trung bình; **không nội suy** để ép hai lỗi bằng nhau.
EER và AUC trên test mô tả điểm số khi quét ngưỡng hoặc so xếp hạng; ACER trong
bảng dùng ngưỡng validation đã khóa. Không dùng EER test để chọn lại ngưỡng.

## 8 Nguồn đường học và hình

| Hình | Nguồn notebook, đếm cell từ 1 | Nguồn dữ liệu đã ghi trong code |
| --- | --- | --- |
| Curve E0 và Official E1 | N1 cell 32, exec 28 | `train_log.csv` của đúng hai run ở mục 2; gọi `scripts/plot_frozen_comparison.py` |
| Curve riêng Official E1 | N1 cell 24, exec 21 | `train_log.csv` E1; in best epoch 25 |
| BCE curve E2 | N2 cell 13, exec 10 | `train_log.csv` E2; in best epoch 1 |
| Histogram E1/E2 | N2 cell 16, exec 12 | `test_scores.csv` từng run; ghép cùng video |

Các bản hình cục bộ: `hinh_anh/notebook/e0-e1-curves.png`,
`hinh_anh/notebook/e2-bce-curve.png`,
`hinh_anh/notebook/e1-e2-score-histograms.png`, tính từ thư mục báo cáo.
Đã đối chiếu pixel ảnh trích với output notebook trong lần kiểm tra này.
Không dựng lại curve từ các giá trị suy đoán. E0 có đủ năm dòng log in ở N0
cell 35; E1 chỉ in 10 dòng cuối ở N1 cell 24 và có ảnh curve toàn run; E2 có
ảnh curve nhưng chưa in bảng số log trong output đã đọc. Chưa có cơ sở để
chép thêm loss từng epoch E2 hoặc chữ số đầy đủ của minimum E0.

Ảnh `validation-depth-case.png` thuộc N1 cell 25, tức index 24 khi đếm từ 0;
là mẫu validation `casia_s14_v2_f000055`, không thuộc năm video test cùng sai.
Danh mục nguồn trước đây dùng index từ 0 cho một số hình; mục này ghi rõ cách
đếm để tránh lệch một cell khi tìm lại nguồn.

## 9 Dấu vết của bản nguồn cục bộ

SHA-256 là dấu kiểm tra nội dung file. Ngày 15/10, ba notebook gốc và bản sao
trong `nguon/notebooks/` khớp từng byte. Các hash sau cũng khớp với hồ sơ sao
chép `nguon/NGUON_CUC_BO.json`:

- N0: `49e540f744631a711d4e23e79a9bfd1b54db6bb954fac772532775d26edb0266`.
- N1: `b78e73136f7249d8f7fd219d3aa639844b71e2e6d245782e34459606e9e79857`.
- N2: `5b9679062bbb569754dd80e1deff483281ac07fef8d13c5bcc11dca13d7363e8`.

Ba config gốc cũng khớp từng byte với `nguon/cau_hinh/`. Đây là kiểm tra nội
dung bản sao tại thời điểm đọc, không chứng minh các cell đã sửa từng được chạy
lại đúng với source hiện tại. Không thay đổi notebook gốc hoặc bản sao.

N1 cell 7 lưu verifier thành công: 73 state tensors khớp, sai khác đầu ra tối đa
0,0, upstream commit `fd8370e8f32bdd090a3552f5a1fe4c301fa99f2b`. Phạm vi là
đối chiếu triển khai trong điều kiện verifier, không phải tái lập kết quả
benchmark gốc. N2 cell 11–12 lưu kiểm tra manifest, trọng số, depth trên batch
validation và toàn bộ state backbone ở checkpoint E2; không mở rộng kiểm tra
batch đó thành so từng depth map của toàn bộ dataset trong phiên này.

## 10 Điểm còn cần nguồn bổ sung

Các bảng trên đủ để viết Chương 4 ở độ chính xác đã trình bày. Những mục sau
cần artifact gốc nếu muốn kiểm toán sâu hơn, không được ghi là đã xác minh:

- Metadata và hash `best.ckpt` E0/E2; tính lại hash checkpoint E1.
- Giá trị đầy đủ của ngưỡng E2, validation loss E2 và validation loss E0.
- Checksum manifest thực tế và toàn bộ frame/video score CSV của ba run.
- Tính lại EER/AUC từ score gốc; khoảng tin cậy hoặc độ biến động nhiều seed.
- Ảnh RGB/depth của đúng năm video test cùng sai và đo latency lặp lại.

Trong mỗi thư mục run, nguồn cần giữ gồm `config.yaml`, `best.ckpt`,
`train_log.csv`, `manifest_checksum.json`, `threshold.json`, `metrics.json`,
`val_scores.csv`, `test_scores.csv`, `test_metrics.json`. E2 có thêm
`initial_checkpoint.json` và `comparison_freeze.json`. Code notebook ghi việc
lưu các file này; phiên hiện tại chỉ kiểm tra output và các file cục bộ đã nêu.

Khối 1 chốt nguồn số liệu; phần diễn giải đầy đủ, hình thực nghiệm và phân tích
chi phí vẫn thuộc Khối 4. Bản thảo Word/Markdown đã điền bảng test 4.2, ghi
validation riêng bằng lời và ghi nguồn phụ lục; chưa gọi toàn báo cáo là hoàn chỉnh.
