# Rà soát hoàn thành Lượt 1–3

Ngày rà soát: 20 tháng 9 năm 2026. Phạm vi rà soát gồm đặc tả nghiên cứu,
kế hoạch theo lượt, quyết định dữ liệu, cấu hình, mã nguồn, unit test và bằng chứng
CASIA E0 do người dùng cung cấp. Slide không thuộc phạm vi hoàn thành hiện tại.

## Kết luận ngắn

| Lượt | Trạng thái | Kết luận |
|---|---|---|
| Lượt 1 | Gần hoàn tất | Framing, literature, kiến trúc, metric và protocol CASIA giữa kỳ đã có. Còn chờ quyền truy cập benchmark chính thức và một batch visualization thực tế. |
| Lượt 2 | Hoàn tất cho CASIA giữa kỳ | Manifest sạch, metric được test, E0 chạy xong, threshold khóa trên validation và test result đã đóng băng. Cần giữ nguyên artifact trên Drive. |
| Lượt 3 | Code hoàn tất, thực nghiệm chưa hoàn tất | 3DDFA queue/worker/QA, CDCN E1 và công cụ xuất bằng chứng đã sẵn sàng. Chưa có depth thật, failure rate, E1 run và predicted-depth cases vì các bước này phải chạy trong Colab có dataset/GPU. |

Toàn bộ test hiện tại: **38 passed**. Manifest CASIA đã kiểm tra: **12.000 frame,
600 video, 50 subject, 0 video leakage, 0 subject leakage, 0 sample ID trùng**.

## Lượt 1 — bài toán, literature và protocol

| Yêu cầu | Trạng thái | Bằng chứng / việc còn lại |
|---|---|---|
| Một câu hỏi nghiên cứu, một biến chính | Hoàn tất | Learned depth head là thay đổi chính; E2 cô lập thay đổi này. |
| Literature matrix và paper cốt lõi | Hoàn tất | `reports/LITERATURE_MATRIX.md`; có CDCN, Deep Spatial Gradient, DC-CDN, UCDCN và CASO-PAD. |
| Quy tắc direct/contextual comparison | Hoàn tất | Đã ghi trong đặc tả và literature matrix. |
| Kiến trúc E0–E4 và CDCN MT Lite | Hoàn tất | Đặc tả và config E0–E4 có trong repo. |
| Lịch A/B hai thành viên | Hoàn tất | Đã chốt trong kế hoạch theo lượt. |
| Repository skeleton | Hoàn tất | Package, scripts, configs và tests đã có. |
| Dataset/protocol giữa kỳ | Hoàn tất | CASIA-FASD tạm thời, 20 frame/video, validation subject 4/9/14/19, test giữ nguyên source test. |
| Dataset benchmark cuối có license/quyền truy cập | Chưa hoàn tất | OULU-NPU và Replay-Attack đang chờ duyệt. Hạn quyết định: 27/09/2026. Đây là phụ thuộc bên ngoài, không chặn báo cáo CASIA giữa kỳ. |
| Demo face crop hoặc batch dataset | Chưa có artifact thực tế | `scripts/visualize_manifest_batch.py` đã sẵn sàng; cần chạy nơi có dataset để tạo `casia-val-batch.png`. |
| Slide | Hoãn chủ động | Chỉ làm sau khi Lượt 3 có số và hình thật. |

## Lượt 2 — dữ liệu, metric và E0

| Yêu cầu | Trạng thái | Bằng chứng / ghi chú |
|---|---|---|
| Manifest theo protocol phát triển | Hoàn tất | `data/manifests/casia_fasd_debug.csv` tồn tại cục bộ nhưng bị Git ignore để tránh đẩy dữ liệu dẫn xuất ngoài ý muốn. |
| Không leakage | Hoàn tất | 0 video leakage, 0 subject leakage; validator và test cố tình tạo leakage đều có. |
| APCER/BPCER/ACER/EER/AUC | Hoàn tất | `src/deepface_pad/metrics.py`; có ví dụ tính tay trong test. |
| E0 MobileNetV3 | Hoàn tất | Run `CASIA_E0_BCE_5E_seed42_20260920T082941Z`, 5 epoch, A100. |
| Threshold chỉ chọn trên validation | Hoàn tất | Threshold khóa: `0.9900876432657242`. |
| Test đóng băng | Hoàn tất | APCER 0%, BPCER 11,11%, ACER 5,56%, EER 2,41%, AUC 0,99798. |
| Raw validation score/config/checkpoint | Hoàn tất ngoài Git | Nằm trong run directory trên Drive; không đưa checkpoint/dataset vào Git. |
| Error analysis | Hoàn tất bước đầu | 0/270 false accept và 10/90 false reject; lỗi tập trung ở bona fide subject chưa thấy. |
| Training curve, batch image và score plots dạng file | Chưa gom đủ | Train log/raw scores đang ở Drive; batch image phải chạy bằng script. Việc này không thay đổi kết quả E0 nhưng cần trước khi soạn slide. |

## Lượt 3 — pseudo-depth và CDCN E1

### Phần đã hoàn tất trong code

- Queue và ledger có thể resume; trạng thái được ghi atomically sau từng frame.
- Attack dùng zero target; failure bona fide không bao giờ bị thay bằng zero map.
- Worker tích hợp checkout 3DDFA V2 chính thức, chọn face lớn nhất và hỗ trợ GPU/CPU/ONNX.
- Materialization tạo manifest dẫn xuất, không sửa source manifest.
- Provenance sidecar và preflight khóa checksum của manifest, ledger và từng depth artifact.
- QA từ chối map thiếu, hỏng, NaN/Inf, live all-zero hoặc attack non-zero.
- CDCN E1, absolute loss và contrastive depth loss tám hướng đã có.
- Config smoke một epoch và full 30 epoch đã có.
- `score_checkpoint.py` xuất frame/video score và metric test bằng threshold validation đã khóa.
- `visualize_depth_targets.py` tạo RGB–target–mask–histogram cho smoke gate.
- `visualize_depth_cases.py` tạo ít nhất mười RGB–target–mask–prediction case sau E1.

### Phần chưa thể đánh dấu cho đến khi chạy Colab

| Tiêu chí Lượt 3 | Trạng thái hiện tại | Điều kiện để đánh dấu |
|---|---|---|
| Không có NaN/map live rỗng không được ghi nhận | Chưa có bằng chứng runtime | `casia-depth-qa.json` phải `valid: true`. |
| Failure rate 3DDFA được báo cáo | Chưa có số | Hoàn tất ledger và audit; ghi failure rate theo split. |
| RGB/depth thẳng hàng | Chưa kiểm tra trên ảnh thật | Duyệt `casia-depth-smoke.png`; nếu sai thì dừng, không train E1. |
| E1 raw score frame/video | Chưa có run | E1 smoke và E1 full phải hoàn tất; run dir có `val_frame_scores.csv`, `val_scores.csv`, `test_frame_scores.csv`, `test_scores.csv`. |
| Ít nhất 10 predicted-depth case đúng/sai | Chưa có checkpoint E1 | Chạy `visualize_depth_cases.py`; nếu model không có lỗi validation thì báo 0 lỗi và dùng các case đúng sát threshold, không bịa failure case. |
| Validation/test metric E1 | Chưa có | Threshold chọn trên validation; chỉ sau đó mới chạy frozen test. |
| So sánh E0–E1 | Chưa thể làm | Cùng CASIA manifest, sampling, input convention và video aggregation; chỉ khác model/supervision. |
| Slide cập nhật số thật | Hoãn | Chỉ làm sau tất cả các dòng trên. |

## Quyết định preprocessing cần giữ nhất quán

E0 CASIA hiện dùng full frame được resize. Để so sánh E0–E1 có kiểm soát, E1 giữa kỳ
giữ cùng input convention; 3DDFA render depth thẳng hàng trên frame và QA tạo mask
từ pixel depth khác zero. Smoke gate phải xác nhận face đủ lớn và alignment hợp lý.

Khi benchmark cuối được chốt, nếu official protocol yêu cầu persistent face crop,
nhóm phải áp dụng cùng một crop rule và chạy lại cả E0 lẫn E1. Không được crop riêng
E1 rồi so với E0 full-frame.

## Trình tự hoàn tất trước khi làm slide

1. Đưa các thay đổi code hiện tại vào Colab; không đưa raw data/depth/checkpoint lên Git.
2. Chạy unit test và `visualize_manifest_batch.py` trên CPU.
3. Chạy 3DDFA smoke 50 bona fide frame trên A100, tạo `casia-depth-smoke.png` và duyệt bằng mắt.
4. Nếu smoke pass, chạy hết queue; review/retry failure có lý do.
5. Materialize manifest, verify provenance, validate và audit; chỉ tiếp tục khi `valid: true`.
6. Chạy E1 smoke; nếu loss hữu hạn và predicted depth không sụp thành hằng số, chạy E1 full.
7. Xuất 10 depth cases trên validation, khóa threshold, rồi mới score test bằng `score_checkpoint.py`.
8. Gửi lại các artifact được liệt kê trong `reports/MIDTERM_ROUNDS_1_3_HANDOFF.md` để rà số lần cuối.
9. Chỉ sau bước 8 mới bắt đầu làm slide.

Các command chính xác nằm trong mục **Consolidated CASIA midterm run** của `COLAB.md`.
