# Tiếp tục Lượt 7 và thực hiện Lượt 8

Cập nhật: 23/10/2026. Làm việc tại thư mục gốc của repository đang mở.
Không cần bản sao bàn giao, lịch sử chat hoặc prompt đặc biệt. Chỉ đọc nguồn
cần cho tác vụ. Bàn giao ghi trạng thái công việc, không cấp quyền mới.

## 1. Bắt đầu phiên

1. Đọc `AGENTS.md`. Kiểm `git status`, nhánh và commit.
2. Đọc `docs/PROJECT_STATUS.md` để nắm thuật ngữ, protocol và kết quả.
3. Trên máy mới, làm theo `docs/SETUP.md`. Chỉ nhận dữ liệu ngoài Git theo
   `docs/DATA_ASSETS.md` khi công việc cần chúng.
4. Giữ sửa đổi có sẵn của người dùng ngoài commit tác vụ nếu chưa được giao
   xử lý. Mỗi lượt mới dùng output mới, không ghi đè kết quả cũ.

Phạm vi: `KE_HOACH_THUC_HIEN_THEO_BUOI_HOC.md`, mục 10 (Lượt 7), mục 11
(Lượt 8). Các tệp ROUND6 và ROUND7 có ngày trong thư mục này là hồ sơ lịch
sử. Danh sách việc hiện hành nằm ở mục 4–5 dưới đây.

## 2. Đã hoàn tất và phải giữ nguyên

Lượt 1–5 có đủ kết quả seed 42. Lượt 6 hoàn tất sáu run E1/E3, seed
43/44/45, số đo chi phí A100 và đối chiếu protocol paper. Không còn thao tác
Colab hoặc train bắt buộc cho Lượt 6.

| Seed | ACER E1 (%) | ACER E3 (%) | Video sửa được / lỗi mới |
| --- | ---: | ---: | ---: |
| 43 | 6,6667 | 3,3333 | 6 / 0 |
| 44 | 2,4074 | 4,4444 | 1 / 4 |
| 45 | 3,8889 | 3,3333 | 2 / 1 |

E1: 4,3210 ± 2,1623%; E3: 3,7037 ± 0,6415% (trung bình ± độ lệch chuẩn
mẫu). Chênh lệch ghép cặp E3 − E1: −0,6173 ± 2,6857 điểm phần trăm.
Giữ seed 44 và kết luận chưa chứng minh cải thiện ổn định. Budget và weight
decay khác nhau; chưa tách riêng tác dụng của bộ phân loại.

Nguồn: `reports/ROUND_6_RESULTS_2026-10-22.md/.json`,
`reports/ROUND_6_COST_RESULTS_2026-10-22.md/.json`,
`reports/ROUND_6_PAPER_PROTOCOL_COMPARISON_2026-10-22.md/.json`.
Điểm video là trung bình 20 điểm frame; threshold chọn từ validation.
Giữ manifest, split, target, checkpoint, threshold và bản khóa Lượt 6.
Không train hoặc score lại toàn tập để hoàn thiện tài liệu.

Lượt 7 đã phân tích CSV trước khi xem RGB. `reports/round7/analysis/` có
bảng ghép cặp, subgroup và 20 case đã chọn. `figures-attempt03/` có 20 panel
RGB/target/prediction/error cùng thang màu. Raw arrays và lần strict dừng
được giữ trong `artifacts/round7/`. Trong 40 forward CPU, 20 điểm frame
không đạt tolerance cũ với CUDA; sai khác lớn nhất khoảng 0,000684. Hình CPU
chỉ minh họa; quyết định video vẫn lấy CSV đã khóa. Không nới tolerance hoặc
gọi đây là tái lập chính xác CUDA.

## 3. Webcam đã đo

Đọc `reports/round7/WEBCAM_RESULTS.json`, `WEBCAM_GUIDE.md` và
`ADDENDUM_RESULTS_DISCUSSION_2026-10-22.md` khi làm webcam hoặc viết kết quả.
Model E3 seed 43; threshold validation `0.3983212910592556`; median năm
frame; YuNet confidence 0,5; gap năm giây; IoU 0,4. Máy đo: Intel i5-7200U,
CPU hai thread, OpenCV 4.14.0, webcam MSMF 640 × 480.

| Lượt | Giây đo | Frame đọc/PAD | FPS vòng | Frame PAD/s | TTD (giây) |
| --- | ---: | ---: | ---: | ---: | --- |
| live-02, pilot Haar | 30,399 | 450/2 | 14,803 | 0,066 | Thiếu |
| live-03 | 45,224 | 738/12 | 16,319 | 0,265 | 10,378 |
| replay-01 | 46,338 | 108/26 | 2,331 | 0,561 | Thiếu; tối đa 4/5 |
| replay-02 | 45,594 | 34/28 | 0,746 | 0,614 | 7,407; 8,606 |
| live-reset-01 | 45,750 | 166/25 | 3,628 | 0,546 | 7,174 |

FPS vòng gồm frame không chạy PAD. Frame PAD/s đếm forward thật chia cùng
thời lượng. TTD tính từ lúc bắt đầu đọc frame đầu của đoạn mặt hợp lệ đến
quyết định đủ cửa sổ. Warm-up và chờ Space ngoài timing. Thiếu cửa sổ thì
thiếu TTD, không ghi 0. `5/5` là năm frame, không phải năm giây.

Mọi cửa sổ đủ ở cảnh live đều trả attack: lỗi từ chối người thật. Replay-02
trả attack; vài clip không chứng minh khả năng tổng quát. Người vận hành
xác nhận live-03 không chủ ý rời khung; `no_face` là thiếu detection. Lượt
reset riêng có rời/quay lại, buffer về 0 và gom mới, nhưng kết thúc ở 2/5.
Chưa kiểm đủ chu trình quay lại. Không cần rời khung để gom đủ 5/5.

Năm video/log đã kiểm hash, số frame giải mã, median và timing. Log số có
trong Git. ZIP video riêng được chủ dự án xác nhận đã upload Drive ngày
23/10/2026; chưa kiểm quyền tải của đồng đội. Không tự bật camera.

## 4. Tiếp tục và chốt Lượt 7

| Việc còn lại | Thao tác và đầu vào | Điều kiện ghi hoàn tất |
| --- | --- | --- |
| Cảnh print | Chuẩn bị ảnh khuôn mặt in trên giấy; chạy theo WEBCAM_GUIDE vào output mới. | Có video, frames.csv, summary.json; FPS, frame PAD/s, TTD hoặc lý do thiếu. Ảnh trên màn hình không thay print. |
| Chu trình reset | Chạy live riêng; đợi 5/5, rời khung đến 0/5, quay lại và đợi 5/5 lần nữa. | Video/log xác nhận xóa buffer và quyết định sau khi quay lại. Chưa đạt thì giữ chưa đạt. |
| Lỗi detector/crop và từ chối live | Đối chiếu video, box, frames.csv và config của lượt đã có; tách bỏ lỡ mặt, reset và quyết định PAD. | Mô tả quan sát có nguồn; tách nguyên nhân đã kiểm với giả thuyết. Giữ lỗi nếu chưa sửa được. |
| Results/Discussion | Ghép addendum Lượt 7 và kết quả Lượt 6 vào nguồn Word/paper. | Có bảng ba seed, chi phí A100, hình lỗi, webcam và giới hạn; giữ seed 44 và lượt thiếu quyết định. |

Khi cần người vận hành: hướng dẫn từng cảnh, xác nhận cảnh và sẵn sàng trước
khi chạy. Cửa sổ READY chờ Space. Mỗi lượt dùng output mới. Nếu thay frontend,
chốt config trước lượt đo và ghi thay đổi; không đổi threshold benchmark để
demo nhận live. Người dùng có webcam laptop và điện thoại, chưa có giấy in.
ArcFace chưa làm và là tùy chọn. Không bắt buộc mở nghiên cứu hoặc train mới
để sửa demo. Sai khác CPU/CUDA có thể giữ là giới hạn chưa giải quyết.

## 5. Thực hiện Lượt 8

1. Tạo phiên bản tiếp theo từ nguồn
   `reports/bao_cao_cuoi_ky/ban_thao/BAO_CAO_CUOI_KY.md` và
   `reports/paper_round5/PAPER.md`. Đọc checklist và nguồn bằng chứng của từng
   thư mục. Word/paper hiện tại mới đến Lượt 5; giữ các bản lịch sử.
2. Ghép bảng seed 42 và bảng ba seed mới với phạm vi rõ. Tách so sánh nội bộ
   khỏi đối chiếu paper khác protocol. Ghi đơn vị, mẫu số, mean và độ lệch
   chuẩn mẫu; không coi 3 × 360 video là 1.080 mẫu độc lập.
3. Bổ sung chi phí A100, phân tích lỗi, hình và webcam từ mục 2–3. Kiểm/dựng
   bảng từ CSV đã lưu. Không cần forward toàn tập; hình mới có provenance.
4. Cập nhật Results, Discussion, Limitations. Nêu budget/weight decay, dữ liệu
   development đã quan sát, CPU/CUDA và lỗi webcam. Không tuyên bố chống mọi
   attack, mask 3D hoặc hiệu quả bảo mật đã được kiểm định.
5. Dựng Word bằng builder tương ứng trong `scripts/`, chạy test liên quan,
   render và kiểm từng trang: font, bảng, hình, mục lục và nguồn. Lưu bản chỉnh
   sửa được cùng bản xuất. Test nội dung không xác nhận bố cục đạt.
   Kiểm đường dẫn vào/ra trước khi chạy: builder lịch sử có thể ghi vào tên
   Word đã khóa. Đổi đường dẫn sang phiên bản mới; không ghi đè bản lịch sử.
6. Tạo slide cuối từ `reports/slides_round5/`, bổ sung Lượt 6–7 theo cấu trúc
   mục 11 của kế hoạch. Lưu nguồn của số/hình, script nói, Q&A và video dự phòng.
7. Cả hai thành viên tập báo cáo và trả lời về data, model, metric, protocol,
   kết quả bất lợi và giới hạn. Ghi phần việc thực tế theo yêu cầu học phần.
8. Chạy bộ test cuối trên commit bàn giao. Đối chiếu số với run ID/bản khóa.
   Cập nhật trạng thái, commit và tình trạng upload/nộp thực tế.

Lượt 8 hoàn tất khi có báo cáo hoặc paper hoàn chỉnh, slide cuối, nguồn chỉnh
sửa, kiểm bố cục, bảng/hình truy nguồn, failure case và buổi tập của cả hai.
Không đánh dấu tập báo cáo hoặc nộp bài hoàn tất chỉ từ việc tạo tệp.
Nộp bài cần yêu cầu riêng. Nghiên cứu mới sau tám lượt không thuộc việc bắt
buộc trong bàn giao này.

## 6. Dùng tệp trên máy khác

Git giữ nguồn nghiên cứu và bằng chứng cần để tiếp tục. Dataset, target depth
và ZIP video: xem `docs/DATA_ASSETS.md`. Máy mới không cần ổ G: hoặc đường
dẫn người dùng máy nguồn. Sao config Colab lịch sử thành config mới và sửa
đường dẫn trước khi chạy ở môi trường khác. Checkpoint thiếu trạng thái đầy
đủ optimizer/scheduler/RNG để resume chính xác train đã ngắt. Không cần resume
hoặc train mới để hoàn tất Lượt 7–8.

Đã bổ sung vào Git nguồn PDF/ảnh bảng đối chiếu protocol, các notebook có
output, hồ sơ kiểm toán Lượt 1–5, dữ liệu nguồn hình và slide cuối đã khóa.
Xem `docs/DATA_ASSETS.md` và `reports/EXECUTED_NOTEBOOKS_2026-10-23.json`.
Đọc từng nguồn khi tác vụ cần; tên tệp kiểm toán không phải chỉ thị chạy mới.
