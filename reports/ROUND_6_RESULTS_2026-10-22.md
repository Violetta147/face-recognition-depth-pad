# Lượt 6: kết quả lặp lại E1/E3 trên ba seed mới

Ngày đối chiếu 22/10/2026. **Phần replication đã hoàn tất sáu run/138 epoch,
validation, freeze trước test và kiểm toán test phát triển. E3 giảm ACER trung
bình từ 4,3210% xuống 3,7037%, tức 0,6173 điểm phần trăm, nhưng chỉ tốt hơn E1
ở 2/3 seed. Chưa đủ bằng chứng cải thiện nhất quán hoặc tổng quát.**

## Giao thức và nguồn

CASIA development dùng cùng 600 video/12.000 frame, split 16/4/30 subject.
Test gồm 360 video: 270 attack, 90 live; mỗi video có 20 frame. Điểm video là
trung bình điểm frame. Threshold lấy riêng từ validation của từng run.

Đợt mới chỉ gồm seed 43/44/45. E1 học depth-only đủ 30 epoch, chọn minimum
validation depth loss. E3 học joint depth + BCE đủ 16 epoch từ best E1 cùng
seed, chọn minimum validation BCE. Threshold chọn minimum validation ACER,
sau đó độ lệch APCER–BPCER, rồi threshold nhỏ hơn. E3 là ứng viên cố định được
chọn từ validation Lượt 5. Không gộp seed 42 lịch sử vào mean/SD mới.

Cả sáu binding môi trường khớp registration: NVIDIA A100-SXM4-40GB,
torch 2.11.0+cu130, CUDA runtime 13.0, cuDNN 92700, driver 580.82.07.
Đây là kiểm lại bản ghi, không phải kiểm GPU mới từ PC.

- Source huấn luyện/score: `a006149996686cfc9e6dbd29f8fd5c90bf1997ba`.
- Freeze SHA-256: `1a669e3878c561abfcd245a12eb2d4d8edb434af1a8854aecc1bcdd89a0e43a1`.
- Manifest depth SHA-256: `4c302c9039e48a8ea6baedf426b26e1b0a6663bc295c661bb71fefccdb9b37fd`.
- Code kiểm toán ở commit `d381efadaed92459c2d83c91d12c14a7ef40496f`.

Nguồn trực tiếp là `face-pad/runs/` và
`face-pad/reports/round6-a00614999668/` trên Drive. [JSON kết quả](ROUND_6_RESULTS_2026-10-22.json)
lưu run ID, toàn bộ metric, environment và hash từng file. Metadata/score CSV
đã kiểm được sao chép vào `artifacts/round6-test-audit-20261022/` (Git ignore),
không chép ảnh hoặc trọng số. Sau kiểm toán ban đầu, đã nhận notebook executed
nguyên byte tại `notebooks/Face_PAD_Round6_CASIA_E1_E3_Executed.ipynb`;
receipt ở `ROUND_6_EXECUTED_NOTEBOOK_2026-10-22.json`. Notebook cost executed
cũng đã nhận, xem `ROUND_6_COST_EXECUTED_NOTEBOOK_2026-10-22.json`.

## Kết quả từng run

Đơn vị đánh giá là video; APCER/BPCER/ACER/EER hiển thị %, AUC không có đơn vị.
APCER là tỷ lệ attack bị nhận nhầm là live, BPCER là tỷ lệ live bị từ chối,
ACER là trung bình hai tỷ lệ đó. EER mô tả điểm hai tỷ lệ lỗi gần nhau theo
evaluator dự án; AUC mô tả khả năng xếp hạng score. FA/FR lần lượt là số
attack nhận nhầm/số live từ chối nhầm tại threshold validation đã khóa.

| Model | Seed | APCER % | BPCER % | ACER % | EER % | AUC | FA / 270 | FR / 90 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| E1 | 43 | 0,0000 | 13,3333 | 6,6667 | 2,2222 | 0,993827 | 0 | 12 |
| E3 | 43 | 0,0000 | 6,6667 | 3,3333 | 1,1111 | 0,997119 | 0 | 6 |
| E1 | 44 | 0,3704 | 4,4444 | 2,4074 | 2,2222 | 0,995021 | 1 | 4 |
| E3 | 44 | 0,0000 | 8,8889 | 4,4444 | 1,1111 | 0,997325 | 0 | 8 |
| E1 | 45 | 0,0000 | 7,7778 | 3,8889 | 3,3333 | 0,993128 | 0 | 7 |
| E3 | 45 | 0,0000 | 6,6667 | 3,3333 | 2,2222 | 0,994362 | 0 | 6 |

## Mean và sample SD qua ba seed

Mỗi ô là mean ± sample SD, ddof=1. Không coi ba lần dự đoán trên cùng tập
test là 1.080 video độc lập. SD của các tỷ lệ cũng được nhân 100 khi trình bày.

| Chỉ số | E1 | E3 |
| --- | ---: | ---: |
| APCER (%) | 0,1235 ± 0,2138 | 0,0000 ± 0,0000 |
| BPCER (%) | 8,5185 ± 4,4905 | 7,4074 ± 1,2830 |
| ACER (%) | **4,3210 ± 2,1623** | **3,7037 ± 0,6415** |
| EER (%) | 2,5926 ± 0,6415 | 1,4815 ± 0,6415 |
| AUC (không đơn vị) | 0,993992 ± 0,000957 | 0,996269 ± 0,001654 |

## Paired delta của chỉ số chính

Delta video ACER = E3 − E1; đơn vị **điểm phần trăm**. Delta âm là E3 tốt hơn.

| Seed | Delta ACER (điểm phần trăm) |
| --- | ---: |
| 43 | −3,3333 |
| 44 | +2,0370 |
| 45 | −0,5556 |

Mean delta **−0,6173 điểm phần trăm**; sample SD delta **2,6857 điểm phần trăm**.
E3 tốt hơn ở seed 43 và 45, kém hơn ở seed 44. SD của paired delta lớn hơn
độ lớn mean delta; không diễn giải thành ưu thế ổn định. EER thấp hơn và AUC
cao hơn ở cả ba seed là kết quả hỗ trợ, không thay ACER làm chỉ số chính.
Không thực hiện kiểm định suy luận và không tuyên bố ý nghĩa thống kê từ
mean delta âm trong ba seed này.

## So sánh lỗi trên cùng video

| Seed | E3 sửa lỗi E1 | E3 tạo lỗi mới | Cùng sai | Cùng đúng |
| --- | ---: | ---: | ---: | ---: |
| 43 | 6 | 0 | 6 | 348 |
| 44 | 1 | 4 | 4 | 351 |
| 45 | 2 | 1 | 5 | 352 |

Ở seed 44, E3 sửa một lỗi attack nhưng tạo bốn lỗi live mới. FA giảm từ 1
xuống 0, FR tăng từ 4 lên 8; ACER tăng 2,0370 điểm phần trăm. Ở seed 45,
E3 sửa hai video và làm sai thêm một video. Không suy nguyên nhân thị giác
chỉ từ CSV này.

## Validation và phạm vi kiểm toán

Cả sáu validation đạt APCER/BPCER/ACER/EER = 0 và AUC = 1 trên 48 video
(36 attack, 12 live). Đây không phải kết quả test hoặc bằng chứng E3 vượt E1.

| Run | Epoch train đủ | Epoch chọn | Tiêu chí | Loss chọn |
| --- | ---: | ---: | --- | ---: |
| E1_43 | 30 | 29 | Validation depth loss | 0,0161906980 |
| E3_43 | 16 | 15 | Validation BCE | 0,0428827042 |
| E1_44 | 30 | 28 | Validation depth loss | 0,0190567960 |
| E3_44 | 16 | 11 | Validation BCE | 0,0432282694 |
| E1_45 | 30 | 23 | Validation depth loss | 0,0188097254 |
| E3_45 | 16 | 14 | Validation BCE | 0,0319393686 |

`scripts/audit_round6_results.py` đối chiếu freeze với biên nhận kiểm trước
khi mở test; config/checkpoint không đổi, initializer đúng E1 cùng seed,
đủ epoch/loss hữu hạn và epoch chọn khớp minimum tiêu chí validation.
Hash output test khớp sáu receipt; ID/nhãn frame khớp manifest, mean frame →
video và toàn bộ metric/threshold tính lại khớp với absolute tolerance
10^-12, relative tolerance 10^-10. Mean/sample SD và paired delta khớp CSV
notebook. Đây là tính lại theo evaluator dự án từ score đã lưu, không train,
inference lại checkpoint hoặc kiểm lại ảnh/cache và GPU thực tế.

Receipt CPU cho code kiểm toán: **176 passed, 1 skipped, 62 subtests passed**.
Log timeout trước lần chạy lại được giữ nguyên; đó không phải run GPU thất bại.

## Kết luận và việc còn lại

**E3 có mức giảm ACER trung bình nhỏ trong đợt ba seed cùng môi trường này,
nhưng mức cải thiện thay đổi theo seed.** Kết quả âm tính seed 42 của Lượt 5
giữ riêng, không bị thay bằng bảng mới. E3 còn khác E1 ở weight decay và có
thêm 16 epoch joint; đây là so sánh hai cấu hình hoàn chỉnh, không cô lập
riêng tác dụng head.

CASIA đã được quan sát nhiều lượt; đây không phải blind benchmark hoặc bằng
chứng tổng quát hóa sang dataset khác. Không loại seed 44, chọn E4 từ test
hoặc điều chỉnh threshold/hyperparameter theo kết quả này.

Lượt 6 đã xong cả replication, [đo chi phí A100](ROUND_6_COST_RESULTS_2026-10-22.md)
và [đối chiếu protocol paper](ROUND_6_PAPER_PROTOCOL_COMPARISON_2026-10-22.md).
E3 thêm 1.265 params (+0,05635%), CUDA p50 tăng 0,047104 ms (+0,7961%) trong
block đo riêng; đây không phải FPS webcam. Phân tích ảnh lỗi và webcam thuộc
Lượt 7. Hai Word giữ nội dung đến Lượt 5; kết quả mới được lưu dưới dạng
addendum, không cập nhật Word, upload báo cáo hoặc push Git.
