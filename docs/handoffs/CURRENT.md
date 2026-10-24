# Bàn giao sau khi hoàn thành báo cáo và paper Lượt 8

Cập nhật: 24/10/2026. Làm việc tại thư mục gốc của repository đang mở.
Không cần bản sao bàn giao, lịch sử chat hoặc prompt đặc biệt. Chỉ đọc nguồn
cần cho tác vụ. Bàn giao ghi trạng thái công việc, không cấp quyền mới.

## 1. Bắt đầu phiên

1. Đọc `AGENTS.md`. Kiểm `git status`, nhánh và commit.
2. Đọc `docs/PROJECT_STATUS.md` để nắm thuật ngữ, protocol và kết quả; đọc
   `reports/round8_documents_20261023/README.md` để tìm hai tài liệu mới.
3. Trên máy mới, làm theo `docs/SETUP.md`. Chỉ nhận dữ liệu ngoài Git theo
   `docs/DATA_ASSETS.md` khi công việc cần chúng.
4. Giữ sửa đổi có sẵn của người dùng ngoài commit tác vụ nếu chưa được giao
   xử lý. Mỗi lượt mới dùng output mới, không ghi đè kết quả cũ.

Phiên vừa hoàn tất chỉ tạo mới báo cáo và paper từ bằng chứng đã có, không
ghi đè tài liệu lịch sử. Không làm webcam, slide hoặc train mới. Yêu cầu
hiện tại là cập nhật bàn giao; các phần còn lại của kế hoạch không tự trở
thành việc được phép chạy trong phiên mới. Nếu chưa có nhiệm vụ mới, đọc
trạng thái và chờ người dùng giao việc.

Kế hoạch tám lượt ở `KE_HOACH_THUC_HIEN_THEO_BUOI_HOC.md`, mục 10–11. Các tệp
ROUND6 và ROUND7 có ngày trong thư mục này là hồ sơ lịch sử. Phần tài liệu
đã hoàn thành ở mục 5; mục 4 ghi việc webcam còn thiếu khi được giao tiếp.

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

## 4. Việc Lượt 7 còn thiếu, chưa thực hiện trong phiên tài liệu

| Việc còn lại | Thao tác và đầu vào | Điều kiện ghi hoàn tất |
| --- | --- | --- |
| Cảnh print | Chuẩn bị ảnh khuôn mặt in trên giấy; chạy theo WEBCAM_GUIDE vào output mới. | Có video, frames.csv, summary.json; FPS, frame PAD/s, TTD hoặc lý do thiếu. Ảnh trên màn hình không thay print. |
| Chu trình reset | Chạy live riêng; đợi 5/5, rời khung đến 0/5, quay lại và đợi 5/5 lần nữa. | Video/log xác nhận xóa buffer và quyết định sau khi quay lại. Chưa đạt thì giữ chưa đạt. |
| Lỗi detector/crop và từ chối live | Đối chiếu video, box, frames.csv và config của lượt đã có; tách bỏ lỡ mặt, reset và quyết định PAD. | Mô tả quan sát có nguồn; tách nguyên nhân đã kiểm với giả thuyết. Giữ lỗi nếu chưa sửa được. |

Khi cần người vận hành: hướng dẫn từng cảnh, xác nhận cảnh và sẵn sàng trước
khi chạy. Cửa sổ READY chờ Space. Mỗi lượt dùng output mới. Nếu thay frontend,
chốt config trước lượt đo và ghi thay đổi; không đổi threshold benchmark để
demo nhận live. Người dùng có webcam laptop và điện thoại, chưa có giấy in.
ArcFace chưa làm và là tùy chọn. Không bắt buộc mở nghiên cứu hoặc train mới
để sửa demo. Sai khác CPU/CUDA có thể giữ là giới hạn chưa giải quyết.

## 5. Lượt 8: báo cáo và paper đã hoàn thành

Gói hiện hành: [reports/round8_documents_20261023](../../reports/round8_documents_20261023/README.md).
Hai tài liệu và nguồn Markdown mới đã tích hợp kết quả đến Lượt 7, gồm
Results, Discussion và Limitations. Các bản ở `reports/bao_cao_cuoi_ky/` và
`reports/paper_round5/` được giữ nguyên để truy lịch sử, không phải bản mới nhất.

| Tệp trong gói mới | Nội dung đã hoàn thành |
| --- | --- |
| `Nhom1_Bao_cao_DeepFace_PAD_20261023.docx`, `BAO_CAO.md` | Báo cáo tiếng Việt đúng ba chương; có tổng quan và ưu/nhược nghiên cứu, giải pháp, đánh giá. |
| `Nhom1_Paper_CDCN_IEEE_VI_20261023.docx`, `PAPER.md` | Paper tiếng Việt, tóm tắt tiếng Việt, không abstract tiếng Anh; cấu trúc bài nghiên cứu, A4 hai cột 10 pt tham chiếu IEEE conference. |
| `SOURCES.md`, `SOURCE_RECHECK.json`, hai tệp `.provenance.json` | Truy nguồn bảng/hình/đầu vào, hash và kiểm số học từ CSV đã lưu. |
| `VALIDATION.md`, `DOCUMENTS_QA.json` | Biên bản kiểm nội dung, số trang, bố cục và hash hai Word cuối. |

Giới hạn thầy giao: phần chính tổng không quá 50 trang; chương 1 không quá
15, chương 2 không quá 25, chương 3 không quá 20. Không cộng ba giới hạn riêng
thành giới hạn tổng 60 trang. Bản Word đã render:

| Phần | Trang vật lý | Số trang / giới hạn |
| --- | --- | --- |
| Chương 1 | 7–11 | 5 / 15 |
| Chương 2 | 12–21 | 10 / 25 |
| Chương 3 | 22–32 | 11 / 20 |
| Phần chính kể cả kết luận | 7–33 | 27 / 50 |
| Toàn bộ báo cáo | 1–35 | 35 trang gồm phần đầu, tham khảo và phụ lục |
| Paper | 1–6 | 6 trang; chưa có giới hạn riêng của nơi nộp |

Từ khóa đã thống nhất: Face anti-spoofing; Presentation attack detection;
Central difference convolution; Pseudo-depth; Auxiliary supervision.
Chưa chọn hội nghị/tạp chí. Đây là bố cục tham chiếu IEEE conference, chưa
phải xác nhận dùng nguyên template chính thức hoặc đạt yêu cầu một nơi nộp.

Đã đối chiếu lại sáu run seed 43/44/45 từ 43.200 bản ghi frame và 2.160 bản
ghi dự đoán video trên cùng 360 video; kiểm 3.600 mẫu timing đã lưu và hash
sáu hình sao chép. Seed 42 và webcam kế thừa kiểm toán trước, không phải đo
lại trong phiên này. Giữ kết quả bất lợi seed 44, khác biệt budget/weight
decay, sai khác CPU/CUDA và lỗi webcam; không đổi score hoặc threshold.

Builder mới: `scripts/build_round8_documents.py`; render:
`scripts/render_round8_documents.ps1`; bốn test tại
`tests/test_round8_documents.py`. Chỉ dựng lại khi thực sự sửa tài liệu:
chạy builder, chờ hoàn tất, render vào attempt mới, kiểm trang đổi và chạy
test trước commit. Không dùng builder lịch sử để ghi đè Word đã khóa.
Chờ dựng/render/test/commit kết thúc trước lần sửa tiếp để receipt gắn đúng
trạng thái tệp.

Hồ sơ kiểm trước commit tài liệu `ee3f270`: 218 passed, 1 skipped,
34 subtests passed. Log:
`artifacts/project-hooks/validation/c5b243203a444d3bb9c2156189b6deaf.log`.
Đã kiểm 35 trang báo cáo và sáu trang paper bằng Word COM ẩn và Poppler;
QA ở `artifacts/round8-documents-20261023/attempt06/`. Kiểm phần mềm không
thay cho kiểm bố cục hoặc xác nhận hiệu quả PAD.

Hai commit tài liệu đã lưu: `4fdcb55` (nguồn báo cáo ba chương), `ee3f270`
(gói Word/paper đã kiểm). Đây là commit local; phiên tài liệu chưa push,
upload Drive hoặc nộp bài. Bàn giao lần này chỉ đồng bộ tài liệu trạng thái.

Kiểm lại khi bàn giao ngày 24/10: hash hai Word khớp `DOCUMENTS_QA.json`,
21 liên kết Markdown cục bộ ở bốn tệp trạng thái hợp lệ. Bộ kiểm thử cuối
đạt 218 tests; log `artifacts/project-hooks/validation/14de58f8fef645319d5853f7ad862172.log`.
Các lượt timeout 180 giây trước đó được giữ trong log; không sửa hoặc bỏ
test, không tăng ngưỡng timeout để đạt. Không dựng hoặc render lại Word
trong lần cập nhật bàn giao này.

Lượt 8 tổng thể chưa hoàn tất: slide mới, luyện trình bày/Q&A của cả hai và
xác nhận phần việc thực tế còn chờ; webcam còn thiếu như mục 4. Chỉ thực
hiện phần nào khi người dùng giao tiếp. Không tự đánh dấu luyện báo cáo,
upload hoặc nộp bài hoàn tất từ việc đã tạo tài liệu.

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
