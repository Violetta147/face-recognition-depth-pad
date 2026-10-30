# Kiểm tra độc lập APCER, BPCER và ACER của DeepFace-PAD

Ngày kiểm tra: 31/10/2026. Phạm vi: V01–V09, dữ liệu CASIA đã lưu. Không khảo sát dataset mới, train, chạy inference hoặc đổi threshold.

## 1. Kết luận theo từng loại vấn đề

| Hạng mục | Kết quả | Ý nghĩa |
| --- | --- | --- |
| Số học APCER/BPCER/ACER tại threshold đã khóa | Đạt trong 12 run đã kiểm | Số đếm độc lập khớp code và JSON báo cáo trong 10^-12 |
| Nhãn và chiều score | Đúng trong các CSV đã kiểm | Live=1, score cao nghiêng live; live khi score >= threshold |
| Mẫu số và đơn vị | Đúng trong các run đã kiểm | Mỗi run 270 attack, 90 live; chỉ số tính trên 360 video sau mean 20 frame/video |
| Độ đầy đủ so với manifest | Đạt trong phạm vi manifest test | Mỗi run có 7.200 sample ID duy nhất và 360 video, khớp manifest; không có score không hữu hạn |
| Từ chối threshold NaN/Inf | Chưa đạt về phòng vệ đầu vào | Thử NaN trả lỗi bằng 0 giả tạo; chưa thấy NaN trong threshold lịch sử |
| Kiểm nhãn trước ép kiểu | Chưa đạt về phòng vệ đầu vào | Nhãn phân số có thể bị ép thành 0/1 rồi được chấp nhận; CSV đã kiểm chỉ chứa 0/1 |
| Tương đương đầy đủ NIST/ISO | Chưa xác lập | Code gộp attack; không có đầu vào nonresponse hay xác nhận PAI species theo một đánh giá chuẩn |

Vì vậy, không kết luận các bảng lịch sử đã tính sai chỉ vì khác quy ước score của NIST hoặc có lỗi phòng vệ đầu vào. Hai lỗi phòng vệ là phát hiện thật cần sửa/test trước nhánh mới; chưa có bằng chứng chúng gây ra số liệu lịch sử đã kiểm.

Nguồn phương pháp và giới hạn chuẩn: [NGHIEN_CUU_NIST_PAD.md](NGHIEN_CUU_NIST_PAD.md). Số liệu/hash: [KIEM_TRA_SO_HOC.json](KIEM_TRA_SO_HOC.json).

## 2. Quy ước và công thức đã kiểm

Nguồn: [metrics.py](../../../../src/deepface_pad/metrics.py).

Với score s theo hướng live, hệ thống nhận live nếu s >= tau:

- APCER = số video attack có s >= tau / tổng video attack.
- BPCER = số video live có s < tau / tổng video live.
- ACER pooled = (APCER pooled + BPCER)/2.

Chỉ số trong JSON nằm trong [0,1]. Bảng phần trăm nhân 100 đúng một lần. Không dùng tổng 360 video làm mẫu số cho cả hai lỗi. Không lấy trung bình frame-error rồi gọi là video-error.

Khi score bằng threshold, code nhận live. Ví dụ một attack và một live cùng score=0,5, tau=0,5: APCER=1, BPCER=0, ACER=0,5. Đây là quy ước ranh giới nhất quán, không phải lỗi đảo nhãn.

Trong NIST IR 8491, score cao theo hướng attack. Phải đối chiếu sự kiện sai và ranh giới, không sao chép dấu bất đẳng thức một cách máy móc.

## 3. Cách tính độc lập từ bằng chứng đã lưu

1. Đọc test_frame_scores.csv, test_scores.csv và threshold.json của từng run đã khóa.
2. Đối chiếu sample ID/nhãn với manifest test; kiểm số lượng và tính duy nhất.
3. Kiểm mọi frame score hữu hạn, threshold hữu hạn và score video bằng mean đúng 20 frame trong dung sai 10^-12.
4. Đếm trực tiếp attack được cho qua và live bị từ chối; chia đúng mẫu số từng lớp.
5. Đối chiếu kết quả với hàm error_rates hiện tại và JSON báo cáo.
6. Kiểm threshold Lượt 6 trùng threshold validation đã ghi. Không tìm threshold tốt hơn trên test.

Tổng phạm vi: 12 run, 86.400 bản ghi frame và 4.320 bản ghi video. Đó là các lần chấm lặp lại trên cùng 360 video, không phải 4.320 video test độc lập. Lần kiểm này không chứng minh manifest đại diện đầy đủ archive gốc hoặc không có mọi dạng trùng nội dung ảnh.

## 4. Seed 42 — Lượt 5 và các mốc

| Mô hình | Attack lọt qua / 270 | Live bị từ chối / 90 | APCER (%) | BPCER (%) | ACER (%) |
| --- | ---: | ---: | ---: | ---: | ---: |
| E0 | 0 | 10 | 0 | 11,1111 | 5,5556 |
| E1 | 0 | 5 | 0 | 5,5556 | 2,7778 |
| E2 | 0 | 5 | 0 | 5,5556 | 2,7778 |
| E3 | 0 | 9 | 0 | 10,0000 | 5,0000 |
| E3b | 0 | 9 | 0 | 10,0000 | 5,0000 |
| E4 | 0 | 8 | 0 | 8,8889 | 4,4444 |

Nguồn lưu: [báo cáo test Lượt 5](../../../../reports/ROUND_5_TEST_RESULTS_2026-10-16.json) và artifacts/round5-test-audit-20261016. Mọi số trên khớp số đếm và báo cáo đã có.

Ở các run này, ba nhóm attack_type đều có APCER=0. Lấy max theo ba nhóm đó cũng ra 0; điều này không chứng minh pooled và worst-group là cùng phép tổng hợp trong trường hợp khác.

## 5. Seed 43–45 — Lượt 6

| Run | Attack lọt qua / 270 | Live bị từ chối / 90 | APCER (%) | BPCER (%) | ACER (%) |
| --- | ---: | ---: | ---: | ---: | ---: |
| E1, seed 43 | 0 | 12 | 0 | 13,3333 | 6,6667 |
| E3, seed 43 | 0 | 6 | 0 | 6,6667 | 3,3333 |
| E1, seed 44 | 1 | 4 | 0,3704 | 4,4444 | 2,4074 |
| E3, seed 44 | 0 | 8 | 0 | 8,8889 | 4,4444 |
| E1, seed 45 | 0 | 7 | 0 | 7,7778 | 3,8889 |
| E3, seed 45 | 0 | 6 | 0 | 6,6667 | 3,3333 |

Nguồn: [JSON Lượt 6](../../../../reports/ROUND_6_RESULTS_2026-10-22.json) và artifacts/round6-test-audit-20261022. Mọi số trên khớp số đếm và báo cáo đã có. Không khái quát APCER=0 ở seed 42 thành mọi seed đều không có attack lọt qua.

Ví dụ phân biệt phép gộp: lỗi attack duy nhất của E1 seed 44 thuộc video_replay. Pooled APCER là 1/270=0,3704%; APCER riêng video_replay là 1/90=1,1111%. Nếu tính max trên ba attack_type thì được 1,1111%, và trung bình với BPCER 4,4444% cho 2,7778% thay vì pooled ACER 2,4074%. Đây là phép tổng hợp bổ sung trên cùng dữ liệu, không phải sửa một phép chia sai, không thay bảng đã khóa và không tự mang tên đánh giá ISO.

## 6. Lỗi phòng vệ đầu vào đã tái hiện

### 6.1. Threshold NaN

Thử `labels=[0,1]`, `scores=[0.2,0.8]` và `threshold=NaN` (ký hiệu số theo Python). Trong Python/NumPy, cả so sánh >= NaN và < NaN đều False. error_rates trả (0,0,0), thay vì từ chối threshold không hợp lệ.

**Hệ quả:** API có thể báo hoàn hảo giả tạo nếu đầu vào threshold hỏng. Các threshold của 12 run kiểm lần này đều hữu hạn, nên chưa quan sát hệ quả này trong bảng lịch sử. Inf/-Inf cũng phải được xác định và từ chối theo hợp đồng đầu vào của nhánh mới; probe lần này chỉ tái hiện NaN.

### 6.2. Nhãn bị ép kiểu trước kiểm tra

Code thực hiện np.asarray(labels, dtype=int) trước np.isin(...,[0,1]). Thử `labels=[0.2,1.8]` bị đổi thành `[0,1]` rồi được chấp nhận (ký hiệu số theo Python).

**Hệ quả:** hàm không phát hiện một số nhãn thô không nhị phân. Tất cả nhãn CSV đã kiểm là 0/1 đúng manifest. Cần kiểm dữ liệu gốc trước ép kiểu; không coi điều này là bằng chứng nhãn CASIA bị đảo.

### 6.3. Kiểm thử đã chạy và còn thiếu

Ba test hiện có trong [test_metrics.py](../../../../tests/test_metrics.py) đạt: 3 passed. Test được chạy với interpreter Conda đã sửa và đường dẫn src của repository được thêm rõ ràng trong tiến trình test. Một lần khởi chạy trước đó không thu thập được test do package chưa được cài vào interpreter; lần chạy lại đúng đường dẫn đã đạt. Không cài thêm môi trường hoặc package trong phiên này.

Ba test cơ bản chưa bao phủ hai lỗi phòng vệ trên. Trước nhánh mới, EXP-03 phải thêm test cho: NaN/Inf threshold, nhãn phân số/ngoài miền, score không hữu hạn, thiếu lớp, shape, điểm bằng threshold và mẫu số hai lớp không bằng nhau. Chưa sửa evaluator hoặc thêm test vào repository trong đợt nghiên cứu này.

## 7. Các khác biệt protocol cần giữ riêng với lỗi số học

- Pooled APCER và APCER theo nhóm công cụ tấn công trả lời khác nhau. Cần báo tên phép gộp; không tự nhận mọi nhóm attack_type bằng PAI species của một chuẩn cụ thể.
- NIST IR 8491 không phải căn cứ để gọi ACER là chỉ số NIST bắt buộc. ACER có thể được dùng như tóm tắt của protocol dự án, kèm công thức rõ ràng.
- Benchmark hiện có score cho mọi sample trong manifest. Code error_rates không có trạng thái nonresponse. Đối với webcam thiếu detection/không đủ cửa sổ, không được mặc định có một quyết định PAD hợp lệ hoặc loại khỏi mẫu số mà không công khai.
- Threshold tối ưu validation không đồng nghĩa tối ưu test, hoặc mức rủi ro vận hành được bảo đảm. Không sửa threshold lịch sử theo test để làm đẹp kết quả.

## 8. Hành động theo kế hoạch

EXP-01d lưu kết quả nghiên cứu và tính lại; EXP-02 ghi đầy đủ quy ước evaluator; EXP-03 sửa/test lỗi phòng vệ trước chạy thí nghiệm mới. Giữ nguyên kết quả lịch sử nếu chưa có bằng chứng số học sai trên dữ liệu thật. Nếu đổi protocol tổng hợp hoặc xử lý nonresponse, tạo evaluator/đầu ra có phiên bản mới và giải thích phạm vi so sánh.
