# Đối chiếu định nghĩa và protocol đánh giá PAD

Ngày đối chiếu: 31/10/2026. Phạm vi: BPCER, APCER, ACER và các giới hạn liên quan trong V01–V09. Không bổ sung hoặc kiểm kê dataset.

## 1. Kết luận cần giữ

Chưa có căn cứ từ định nghĩa để kết luận các chỉ số lịch sử bị đảo hoặc tính sai. Cần tách ba câu hỏi:

1. Số đếm và phép chia có đúng với nhãn, score, threshold đã khóa không?
2. Phép gộp và đơn vị có đúng với protocol được công bố không?
3. Protocol đó có đủ để đưa ra kết luận an ninh hoặc khả năng tổng quát hóa đang muốn nói không?

Một phép tính có thể đúng số học nhưng chưa tương đương phép đánh giá theo một chuẩn khác. Không sửa công thức chỉ vì tài liệu ngoài dùng chiều score ngược dự án.

## 2. Những điều xác minh trực tiếp từ NIST IR 8491

Nguồn: [NIST IR 8491, bản PDF người dùng chỉ định](https://nvlpubs.nist.gov/nistpubs/ir/2023/NIST.IR.8491.pdf), [bản cùng báo cáo trên máy chủ xuất bản NIST](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=956456), [DOI](https://doi.org/10.6028/NIST.IR.8491).

Trang dưới đây là số trang in trên báo cáo; trang PDF là thứ tự tính từ 1.

| Nội dung xác minh | Vị trí |
| --- | --- |
| Score cao là attack; thấp là bona fide. | §3, trang 12; PDF 22 |
| APCER: attack bị phân loại bona fide. BPCER: bona fide bị phân loại attack. | §3.1–3.2, trang 12; PDF 22 |
| APNRR/BPNRR đo không phản hồi. Báo cáo gán lỗi xử lý thành attack khi tính error rate. | §3.3, trang 12; PDF 22 |
| Công thức lấy H(0)=1: attack khi score ≥ T; bona fide khi score < T. | §3.4, trang 13; PDF 23 |
| Phân biệt đánh giá ưu tiên sự thuận tiện và ưu tiên an ninh bằng hai chiều lỗi. | §3.4, trang 13–14; PDF 23–24 |
| Các bảng báo APCER tại BPCER cố định và chiều ngược lại. | Ví dụ bảng 24, trang 23–24; PDF 33–34 |
| Dấu ± biểu diễn khoảng phủ 95% các mẫu bootstrap điểm attack. | Đầu §5, trang 17; PDF 27 |

Toàn văn được phân tích không có kết quả tìm kiếm “ACER”. Không thể viện báo cáo này như nguồn bắt buộc dùng ACER=(APCER+BPCER)/2.

## 3. Dịch đúng sang quy ước của DeepFace-PAD

Code dự án trong [metrics.py](../../../../src/deepface_pad/metrics.py) dùng y=1 cho live, y=0 cho attack và score cao nghiêng live. Với quy tắc live khi s≥τ:

\[
APCER_{pooled}(\tau)=\frac{\#\{attack:s\geq\tau\}}{N_{attack}},\quad
BPCER(\tau)=\frac{\#\{live:s<\tau\}}{N_{live}}.
\]

Đây là diễn giải số đếm theo quyết định của chính hệ thống. Dấu so sánh hiện tại khớp quy tắc đó. Không thể chép dấu từ một hệ thống dùng score cao là attack mà giữ nguyên chiều score/nhãn của dự án.

**Tại đúng ngưỡng:** dự án cho qua khi s=τ. Nếu đổi score thành r=−s, quyết định tương đương là attack khi r>−τ. Đổi thành r≥−τ sẽ đổi quyết định ở các score bằng ngưỡng. Vì vậy, khác quy ước xử lý hòa không tự động là đảo nhãn; phải công bố và kiểm tra.

**APCER không chia tổng live+attack. BPCER cũng không chia tổng đó.** Tỷ lệ 1:3 không được dùng để nhân thêm ba vào ACER. Pooled ACER của dự án là trung bình hai tỷ lệ có mẫu số riêng. Nó khác tỷ lệ lỗi chung trên tất cả mẫu.

Các kiểm tra số học và CSV của dự án được trình bày trong hồ sơ kiểm toán đi kèm. Tài liệu này tập trung nguồn phương pháp, không tuyên bố đã chạy lại mô hình.

## 4. Pooled attack, PAI species và trường hợp xấu nhất

Nguồn trực tiếp của chuyên gia chuẩn hóa: [Busch và Thieme, NIST IBPC 2016](https://www.nist.gov/system/files/documents/2020/09/15/12_buschthieme-ibpc-pad-160504.pdf), slide 16–20. Tài liệu trình bày APCER theo PAI species và phép lấy max trong tập species thuộc một mức attack potential. Đây là bài trình bày năm 2016 về chuẩn đang phát triển lúc đó, không thay cho toàn văn ISO hiện hành.

Trong dự án, attack_type có warped_photo, cut_photo và video_replay. Ba nhãn này đủ để tính phân rã lỗi theo nhóm của manifest. Chúng chưa tự chứng minh là danh sách PAI species được lập theo một cuộc kiểm định chuẩn, có quy trình chế tạo, công cụ và attack potential tương ứng.

Nếu gọi nhóm attack là c, pooled APCER bằng tổng APCER_c với trọng số N_c/N_attack. Lấy max_c APCER_c là một phép tổng hợp khác. Khi một nhóm có lỗi cao và nhóm khác thấp, pooled có thể thấp hơn max. Khi mọi nhóm đều có 0 lỗi quan sát, cả hai đều bằng 0 trên mẫu đó; khác cách gộp không tự làm xuất hiện lỗi mới.

**Cách báo phù hợp:** giữ “pooled APCER trên video attack” cho bảng cũ; bổ sung từng attack_type khi cần, ghi mẫu số. Không tự đặt tên max ba attack_type là “APCER ISO đã chứng nhận”.

## 5. ACER và phát biểu tuân thủ chuẩn

ACER=(APCER+BPCER)/2 là phép tổng hợp số học mà dự án đã chọn. Phải ghi rõ APCER trong đó là pooled hay theo một nhóm/trường hợp xấu nhất. Hai ACER dùng APCER khác phép gộp không mặc nhiên so trực tiếp được.

[Trang chính thức ISO/IEC 30107-3:2023](https://committee.iso.org/standard/79520.html?browse=tc) xác nhận đây là bản Edition 2, xuất bản tháng 01/2023; bản 2017 đã được thay thế. Phạm vi bao gồm nguyên tắc đánh giá PAD, báo cáo và phân loại tấn công, không chuẩn hóa một thuật toán cụ thể hoặc toàn bộ an ninh hệ thống.

Phiên này không đọc được toàn văn hiện hành từ nguồn ISO chính thức miễn phí. Vì vậy không đưa ra kết luận đã xác minh từng điều khoản của bản 2023, hoặc khẳng định chỉ thêm ACER là tuân thủ chuẩn. Những đoạn toàn văn trên máy chủ bên thứ ba không được dùng làm căn cứ duy nhất cho một kết luận tuân thủ.

[FIDO Biometrics Requirements v1.1, §6.1.4](https://fidoalliance.org/specs/biometric/requirements/Biometrics-Requirements-v1.1-fd-20190606.html) yêu cầu hồ sơ thử có thông tin về người, công cụ, species/series, nguồn và số lượng; đánh giá cả hệ thống dùng các chỉ số liên quan hệ thống. Đây là ví dụ nguồn quy phạm cho thấy một vài metric không thay thế đầy đủ thiết kế kiểm định. Không khẳng định dự án thực hiện chứng nhận FIDO.

**Kết luận:** có thể giữ ACER như summary của protocol nghiên cứu. Đồng thời phải báo APCER/BPCER và không gắn nhãn toàn bộ đánh giá là “đạt NIST/ISO” nếu chưa có cơ sở tương ứng.

## 6. Ngưỡng, DET và diễn giải an ninh

Phân tích đường DET/ROC hoặc điểm tại một mức lỗi là mô tả hiệu năng trên một tập dữ liệu. Nó khác việc ấn định threshold để hệ thống vận hành trên dữ liệu mới.

Trong code dự án, select_threshold tối thiểu hóa ACER trên dữ liệu được truyền vào; evaluate_scores tự chọn threshold nếu đối số threshold bị bỏ trống. Do đó caller phải truyền threshold validation đã khóa khi chấm test. Nếu caller bỏ trống và dùng chính test để tối ưu, vấn đề là nguồn chọn ngưỡng, không phải phép chia APCER/BPCER.

Không suy rằng AUC chọn threshold. Cũng không suy zero APCER trên 270 attack bảo đảm không có attack nào lọt ngoài dữ liệu đó. Các video cùng người có thể phụ thuộc; cần xét đơn vị lấy mẫu khi báo bất định. Bốn người validation không trở thành 960 quan sát độc lập chỉ vì có 960 frame.

Nếu cần công bố mức APCER nhỏ, phải kiểm độ phân giải mẫu và bất định. Không ép một tập nhỏ chứng minh mức rủi ro vượt khả năng dữ liệu. Nhận xét này là hệ quả thống kê và thiết kế, không phải chứng nhận an ninh của dự án.

## 7. Không phản hồi và webcam

Code error_rates chỉ nhận score hữu hạn, không có đầu vào trạng thái “không phản hồi”. Trong benchmark CSV đủ score, điều đó có thể phù hợp với phạm vi đã xác minh. Trong webcam, no_face, thiếu cửa sổ, reset hoặc lỗi xử lý cần được đếm riêng; không được tự bỏ những tình huống khó khỏi mẫu số rồi chỉ báo các cửa sổ có quyết định.

Việc coi mọi thất bại xử lý là attack là một chính sách cụ thể trong báo cáo NIST nêu ở mục 2. Không suy rằng mọi tình huống no_face của demo đều tương đương một presentation đã bị từ chối. Cần định nghĩa một lần thử bắt đầu/kết thúc thế nào và có nhãn thật gì trước khi tính tỷ lệ.

Đề xuất cho V09: giữ kết quả frame/window như log kỹ thuật; muốn báo tỷ lệ PAD ở cấp lần thử thì đăng ký trước cách tính lần thử, không phản hồi và quyết định fail-closed. Không trộn mẫu số window với video benchmark.

## 8. Điều kiện kiểm toán cần đưa vào EXP-01/03

| Kiểm tra | Đạt khi | Phân loại nếu không đạt |
| --- | --- | --- |
| Chiều nhãn và score | live=1, s≥τ cho qua được dùng nhất quán | Lỗi hiện thực hoặc mapping |
| Mẫu số | Attack và live có mẫu số riêng; không thiếu/nhân đôi ID | Lỗi tính toán/đầu vào |
| Tại ngưỡng | Score đúng bằng τ tuân thủ quyết định đã công bố | Lỗi boundary hoặc khác quy ước cần ghi |
| Đầu vào | Nhãn nhị phân trước ép kiểu; threshold và score hữu hạn | Lỗi kiểm tra đầu vào |
| Gộp video | Đúng 20 frame/video hoặc ghi lý do thiếu; nhãn không mâu thuẫn | Lỗi dữ liệu/tổng hợp |
| Nguồn threshold | Test dùng threshold đã khóa từ validation | Lỗi protocol/lựa chọn |
| Phép gộp APCER | Báo pooled hoặc từng nhóm đúng như công bố | Sai phạm vi báo cáo nếu ghi khác |
| Không phản hồi | Có chính sách và mẫu số rõ cho đúng đơn vị lần thử | Đánh giá chưa đầy đủ |
| Tuyên bố chuẩn | Nêu đúng phiên bản, phạm vi và bằng chứng tuân thủ | Kết luận vượt bằng chứng |

Hai lỗi phòng vệ quan sát từ code hiện tại: threshold NaN chưa bị chặn; nhãn được ép int trước khi kiểm nhị phân. Chúng cần test/sửa riêng trong EXP-03, nhưng không tự chứng minh các kết quả lịch sử có nhãn 0/1 và threshold hữu hạn đã sai.

## 9. Giới hạn truy cập và phần chưa làm

- URL nvlpubs trực tiếp vượt giới hạn dung lượng của công cụ đọc. Đã đọc bản cùng tiêu đề/tác giả/NIST IR 8491 trên máy chủ xuất bản NIST, gồm 152 trang PDF.
- Đã đọc các đoạn metric, failure-to-process, DET và phần mô tả bất định; không tuyên bố đã kiểm mọi bảng kết quả của các thuật toán trong báo cáo.
- Chưa có toàn văn ISO 2023 từ nguồn chính thức để xác nhận mọi điều khoản.
- Chưa thay code, chạy huấn luyện, đổi threshold hoặc sửa kết quả lịch sử. Đây là nghiên cứu nguồn và đối chiếu tĩnh; số học thực tế phải được chứng minh từ CSV trong hồ sơ kiểm toán riêng.
