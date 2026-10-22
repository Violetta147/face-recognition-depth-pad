# Bổ sung Results/Discussion Lượt 7 — 22/10/2026

Đã phân tích CSV sáu run, dựng 20 panel và đo webcam thật. Demo có median
window và timing thực, nhưng còn bỏ lỡ mặt và từ chối người thật. Chưa chốt
toàn bộ Lượt 7: thiếu cảnh print, chu trình quay lại đủ window và ghép addendum
vào Word/paper lịch sử. Các file lịch sử và kết quả Lượt 6 được giữ nguyên.

## Phân tích lỗi từ kết quả đã khóa

Nguồn: [Lượt 6](../ROUND_6_RESULTS_2026-10-22.md), CASIA development split
16/4/30 người; 360 video test (270 attack, 90 live), mean 20 frame/video.
CSV, freeze, registration và manifest được kiểm hash lại. Dùng threshold
validation riêng, không train hoặc score lại cả tập. Ba seed dùng cùng video,
không tạo 1.080 quan sát độc lập.

| Seed | E3 sửa lỗi E1 | E3 tạo lỗi mới | Cùng sai | Cùng đúng |
| --- | ---: | ---: | ---: | ---: |
| 43 | 6 | 0 | 6 | 348 |
| 44 | 1 | 4 | 4 | 351 |
| 45 | 2 | 1 | 5 | 352 |

Count khớp báo cáo đã khóa. False live là attack nhận nhầm live; false spoof
là người thật bị từ chối. E1 có false live 0/270, 1/270, 0/270 và false spoof
12/90, 4/90, 7/90. E3 có false live 0/270 cả ba seed và false spoof 6/90,
8/90, 6/90. Seed 44 sửa một replay nhưng tạo bốn false spoof mới.

Nhóm live có metadata quality=low: E1→E3 lần lượt 9→4, 3→6, 4→4 lỗi trên
30 video/seed. [Subgroups](analysis/subgroups.csv) giữ mẫu số theo attack_type,
quality và giao hai nhãn; mẫu số 0 để rate trống. Quality không phải phép đo
blur/ánh sáng và không chứng minh nguyên nhân lỗi.

ACER giữ nguyên: E1 4,3210 ± 2,1623%, E3 3,7037 ± 0,6415% (mean/sample SD,
ddof=1); paired delta −0,6173 ± 2,6857 điểm phần trăm. Chỉ tốt hơn 2/3 seed,
chưa chứng minh cải thiện ổn định. Training budget và weight decay còn khác,
không cô lập được tác dụng head.

## Case và hình có provenance

Quy tắc đã commit trước khi xem RGB: mỗi seed/role/attack_type chọn video đầu
theo ID; lấy frame thứ 11 sau khi sắp 20 frame theo thời gian. Được 6/7/7
case, tổng 20 panel và 40 forward CPU. Giữ cả nhóm rỗng và case bất lợi.
Đây là minh họa có chủ đích, không phải mẫu ngẫu nhiên ước lượng tỷ lệ lỗi.

Xem [case index](analysis/case_index.csv), [provenance](figures-attempt03/provenance.json)
và [inference CSV](figures-attempt03/bounded_inference.csv). Sáu checkpoint,
config/snapshot đúng SHA. Target từng case khớp snapshot; attack constant
thiếu trong archive được serialize zero float32 32² và bắt buộc khớp SHA cũ.
Không chạy lại 3DDFA. RGB lấy đúng ZIP member, ghi SHA mới; không tuyên bố có
hash từng RGB đăng ký trước train.

20 PNG đều 2080×1120, chung depth scale [0,1] và absolute-error scale
[0,0,9920669794], không clipping prediction. Đã kiểm 40 error arrays bằng
đúng abs(prediction-target). Raw arrays/input ở artifacts/round7/figures-attempt03;
NPZ SHA `eb4b5e8b70e509209e29ace3e0f07252606ca4086927dee38026b19f3509c11e`.

20/40 score frame CPU không đạt tolerance ban đầu atol=1e-5, rtol=1e-4 so
với saved CUDA; max chênh tuyệt đối khoảng 0,000684. Đã kiểm một frame bằng
CPU batch 1/2, tắt MKLDNN và float64; chưa xác định nguyên nhân khác CUDA,
trạng thái TF32 cũ chưa ghi đủ. Lượt strict dừng được giữ; lượt xuất hình dùng
rõ diagnostic, không nới tolerance và vẫn ghi cờ fail. Không gọi đây là tái
lập chính xác score CUDA. Video decision trên hình lấy từ CSV cũ; depth là
inference CPU mới của một frame, không phải mean depth của 20 frame.

Ở [replay seed 44](figures-attempt03/case_12_seed44_casia_s30_vHR_4.png),
E1 video score khoảng 0,1543 > threshold 0,1520; E3 khoảng 0,0312 < 0,4321,
sửa false live. Ở [live seed 44](figures-attempt03/case_13_seed44_casia_s31_v1.png),
E1 nhận đúng trong khi E3 từ chối. Target phủ vùng mặt đầy hơn, prediction
có vùng giữa mặt thấp và các vùng biên còn đáp ứng. Quan sát này không chứng
minh mạng dựa vào nền/viền để quyết định. MAE case không thay metric toàn test.

Pseudo-depth không phải 3D đo thật. Target zero của attack là giả định theo
nhãn; ảnh uốn/replay vẫn có hình học/vật liệu vật lý. Error map không chứng
minh model đo bề mặt thật. Cần phép thử riêng để quy nguyên nhân cho nền,
viền, ánh sáng hay blur.

## Webcam thực đo

Intel Core i5-7200U @2,50 GHz, torch 2.11.0 CPU/hai thread; webcam laptop
index 0, MSMF, 640×480. E3_43 là seed đầu đã đăng ký, không chọn theo test.
Checkpoint SHA 9c7835ae…74e2ea4c; threshold đúng file validation là
0,3983212910592556. Không thay model/ngưỡng từ cảnh webcam.

Sau pilot Haar, trước lượt đo mới chốt YuNet 2023mar, confidence detector
0,5, median 5 frame, gap 5 giây, IoU 0,4 và OpenCV 4.14.0 cài riêng. Confidence
detector chọn từ pilot frontend, không từ score PAD. PAD crop/normalization
giữ nguyên. Warm-up 5 forward, 5 settle read và chờ Space ngoài timing.
Bốn lượt YuNet cuối dùng cùng config SHA fbd373d9…f1f877ef.

| Lượt | Giây đo | Frame đọc/PAD | FPS toàn vòng | Frame PAD/s | TTD episode đủ window (s) |
| --- | ---: | ---: | ---: | ---: | --- |
| live-02, Haar pilot | 30,399 | 450/2 | 14,803 | 0,066 | thiếu |
| live-03, YuNet | 45,224 | 738/12 | 16,319 | 0,265 | 10,378 |
| replay-01, YuNet | 46,338 | 108/26 | 2,331 | 0,561 | thiếu; tối đa 4/5 |
| replay-02, YuNet | 45,594 | 34/28 | 0,746 | 0,614 | 7,407; 8,606 |
| live-reset-01, YuNet | 45,750 | 166/25 | 3,628 | 0,546 | 7,174 |

FPS toàn vòng gồm cả frame không chạy PAD. Frame PAD/s chỉ đếm forward thật
chia cùng thời lượng; không gọi 16,319 FPS là tốc độ suy luận mặt. TTD từ
read-call đầu của đoạn một mặt đủ điều kiện đến quyết định median, gồm thời
gian gom window; không đo từ lúc mặt xuất hiện vật lý hoặc timestamp cảm biến.
Episode trong một clip không là trial độc lập, không dựng CI. Giữ vòng chậm
cuối khiến thời lượng có thể vượt 45 giây, không cắt để làm số đẹp hơn.

Live-03 có 2 output đủ window là attack; live-reset có 17 output đủ window
là attack: từ chối người thật trong cảnh người dùng khai báo live. Giữ làm
failure case. Replay-02 có 8 output đủ window là attack, còn 5 multiple_faces
và 1 no_face. Replay-01 không quyết định, không ghi thành phát hiện đúng.
Không tính ACER từ các frame demo hay thay CASIA bằng các cảnh này.

Người dùng xác nhận live-03 không chủ ý rời khung; 726 nhãn no_face nghĩa
không có detection, không chứng minh người đã rời đi. Ở lượt reset riêng,
log và frame kiểm tra cho thấy mặt mục tiêu ra khỏi vùng nhìn, buffer về 0;
khi quay lại đã gom mới nhưng hết lượt ở 2/5. Chưa có TTD thứ hai sau quay lại,
không tuyên bố đã xác minh toàn bộ tái nhận đủ window. Unit test kiểm riêng
mất/nhiều mặt, gap, box đổi và cửa sổ chưa đủ.

Năm video giải mã đủ frame, SHA khớp; state/median/TTD replay bằng clock CSV
và FPS tính lại khớp: [WEBCAM_RESULTS.json](WEBCAM_RESULTS.json). AVI mã hóa
10 FPS cố định; timestamps CSV là timing thật. Video/log ở artifacts/round7,
không đưa video cá nhân vào Git. Nhãn cảnh do người chạy khai báo, không phải
dataset ground truth được chứng thực.

## Trạng thái và giới hạn

Suite: 214 passed, 1 skipped, 68 subtests; 20 test Lượt 7 đạt riêng. Kiểm log
không chứng nhận PAD chính xác. Detector/crop còn chưa ổn định và live false
spoof rõ ràng; đây là prototype nghiên cứu, chưa có bằng chứng đáng tin cậy
để dùng như kiểm soát liveness thực tế. Webcam khác domain và median khác
mean 20 frame/video; threshold cũ chưa được hiệu chỉnh cho webcam.

Còn thiếu print vì người dùng không có mẫu giấy; ảnh tĩnh trên điện thoại
không thay print. Chu trình quay lại đủ window chưa hoàn tất. Nếu nghiên cứu
tiếp, đăng ký riêng frontend/domain và calibration/evaluation trước hiệu
chỉnh, không sửa threshold hoặc dữ liệu Lượt 6 đã mở test. Addendum chưa
ghép vào Word/paper, chưa upload/nộp. ArcFace chưa triển khai.
