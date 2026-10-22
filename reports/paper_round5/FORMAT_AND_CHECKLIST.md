# Định dạng và bố cục bài báo nghiên cứu của nhóm

Đối chiếu ngày 16/10/2026. Không có một định dạng trang duy nhất cho mọi
paper. Mỗi tạp chí/hội nghị quy định mẫu riêng; cấu trúc khoa học và tính
trung thực của bằng chứng là phần phải giữ xuyên các mẫu.

## Mẫu phù hợp đã tìm được

Đề xuất tham khảo **UD-JST**, Tạp chí Khoa học và Công nghệ Đại học Đà Nẵng,
vì có hướng dẫn và mẫu Word cho bài tiếng Việt. Đây **chưa được xác nhận là
một trong hai mẫu thầy đã gửi**, cũng không đồng nghĩa nhóm đang gửi đăng tạp chí.

- [Hướng dẫn tác giả chính thức](https://jst-ud.vn/jst-ud/instruction/author-guideline).
- [Mẫu Word UD-JST được chính trang hướng dẫn liên kết](https://docs.google.com/document/d/1WDGtk8_8nepfbntp1u701Lhs-Yrrcg0c/edit).
- [Checklist nhận bản thảo Word của UD-JST](https://jst-ud.vn/jst-ud/about/submissions).

Các thông số công bố tại trang hướng dẫn:

| Thành phần | Quy định UD-JST |
|---|---|
| Tệp | Microsoft Word; dùng `.docx` cho bản của nhóm |
| Khổ giấy | 190 × 265 mm, không phải A4 |
| Lề | 10 mm cả bốn phía |
| Chữ nội dung | Times New Roman 10 pt |
| Dòng và đoạn | Single, cách đoạn 3 pt |
| Nội dung | Hai cột, cách nhau 5 mm |
| Độ dài | Tối đa 6 trang, gồm hình, bảng và tài liệu tham khảo |
| Tóm tắt Việt | 150–200 từ |
| Abstract Anh | 100–150 từ |
| Từ khóa | Chọn 5 cụm Việt và 5 cụm Anh; trang hướng dẫn và mẫu dùng cách diễn đạt min/max khác nhau, chọn 5 đáp ứng cả hai |
| Trích dẫn | Số trong ngoặc vuông, thứ tự xuất hiện; tài liệu tham khảo kiểu IEEE |
| Bài tiếng Việt | Hướng dẫn còn yêu cầu phụ lục tiếng Anh cho hình và bảng |

Mẫu Word được tải nguyên trạng để kiểm tra, không sửa bản gốc:
`artifacts/workspace-audit-20261016/Template_UD_JST_original.docx`.
Không giữ dòng ISSN/VOL/NO mẫu trong bài của sinh viên như thể đã được xuất bản.
Email tác giả liên hệ, thứ tự tác giả và thông tin bổ sung phải do nhóm xác nhận.

## Bố cục áp dụng cho nghiên cứu E0 đến E4

| Phần | Câu hỏi phải trả lời bằng nội dung thật |
|---|---|
| Tên bài và tác giả | Nghiên cứu đánh giá điều gì, trên dữ liệu nào? Chỉ ghi người thực sự đủ điều kiện tác giả. |
| Tóm tắt, Abstract và từ khóa | Bài toán, thiết kế, kết quả chính và giới hạn quan trọng là gì? |
| 1 Giới thiệu | Vì sao cần kiểm tra learned depth head; câu hỏi và đóng góp thực nghiệm cụ thể? |
| 2 Nghiên cứu liên quan | CDCN, pseudo-depth, classifier và Focal có tiền lệ nào; nhóm kế thừa gì? |
| 3 Phương pháp | E1 mean map, E2 frozen head, E3 joint, E3b staged BCE, E4 staged Focal khác nhau thế nào? |
| 4 Thiết lập thực nghiệm | Split theo người, nhãn, config, budget, seed, chọn checkpoint/ngưỡng, phần mềm và metric? |
| 5 Kết quả và thảo luận | Bảng test/validation, cặp ablation, paired error và depth MAE hỗ trợ kết luận nào? |
| 6 Giới hạn và kết luận | Bằng chứng chỉ tới đâu; điều gì chưa được đo; kết luận có trả lời câu hỏi ban đầu? |
| Tài liệu tham khảo | Mỗi công trình dẫn trong bài có nguồn gốc và thông tin thư mục kiểm tra được? |
| Phụ lục dịch hình/bảng nếu theo UD-JST | Bản tiếng Anh giữ cùng số liệu, đơn vị và định dạng? |

Bài báo không cần bìa “Báo cáo học phần”, lời mở đầu, mục lục hay nhiều chương
lý thuyết dài. Các phần này vẫn phù hợp với final report riêng. Bố cục paper
phải tập trung vào câu hỏi nghiên cứu và cách bằng chứng trả lời câu hỏi đó.

## Checklist nội dung nghiên cứu

Tham khảo các nhóm tiêu chí về claim, giới hạn và tái lập của
[NeurIPS Paper Checklist](https://neurips.cc/public/guides/PaperChecklist),
chuyển thành danh sách tự kiểm tra cho project này. **Không áp dụng quy định
nộp PDF của NeurIPS thay cho yêu cầu nộp Word của thầy.** Đây cũng không phải
chứng nhận bài đạt chuẩn NeurIPS hay đủ điều kiện xuất bản.

| Kiểm tra cho DeepFace-PAD | Trạng thái và nơi xử lý |
|---|---|
| Câu hỏi/đóng góp khớp kết quả | So sánh reader và chiến lược train; không gọi mọi nhánh là cải tiến thành công. |
| Kế thừa và tiền lệ rõ | CDCN/3DDFA/Focal/UCDCN có trích dẫn; head đọc depth không được tự nhận mới hoàn toàn. |
| Dataset/split/đơn vị rõ | 50 người, 600 video, 12.000 frame; train/val/test 16/4/30 người; chấm theo video. |
| Tách chọn mô hình khỏi test | E3 chọn bằng validation; threshold khóa riêng từng run. |
| Điều kiện so sánh rõ | E3–E3b so lịch; E3b–E4 so loss; E2–E3 khác budget/LR. |
| Số liệu có nguồn và mẫu số | Audit JSON/CSV; 270 attack/90 live test; không dùng smoke như full. |
| Độ ổn định thống kê | Chưa có nhiều seed/CI; công khai giới hạn, không tự điền mean ± SD. |
| Sai số depth đúng nghĩa | MAE validation với pseudo-depth, không phải cm và không phải accuracy test. |
| Lỗi và kết quả âm tính được giữ | E2 không sửa 5 lỗi; E3/E4 tạo thêm lỗi; không chọn riêng ca tốt. |
| Chi phí và môi trường | Báo params; chưa dùng latency cũ để chứng minh nhanh hơn; nêu cu128/cu130. |
| Hình có nguồn và phép biến đổi rõ | Hình pipeline từ code; không dựng ảnh giả thành thực nghiệm. |
| Dữ liệu và quyền sử dụng | Nêu bản CASIA từ Kaggle, giới hạn nguồn/license; không tự nhận đã xác minh quyền phân phối. |
| Tái lập và truy vết | Run ID/source commit/hash/config/score; hướng dẫn đọc artifact, không bắt train lại. |
| Tác giả chịu trách nhiệm | Hai thành viên đọc lại; xác nhận thứ tự tác giả, email, đóng góp, công bố dùng AI nếu môn yêu cầu. |
| Thông tin chưa có được giữ đúng trạng thái | Nhiều seed, benchmark độc lập, webcam và nhận diện danh tính không ghi thành kết quả đã làm. |

## Trước khi nộp thầy

1. Hai thành viên đọc toàn bộ bản Word, đối chiếu tên/tác giả và hiểu các bảng.
2. Nếu tìm lại được hai mẫu thầy gửi, so mẫu đó với UD-JST; mẫu môn học có ưu tiên.
3. Kiểm tra `.docx` mở được, không còn ô `[Điền]`, bảng/hình/nguồn đầy đủ,
   không nhầm bản khung báo cáo cuối kỳ với bài báo.
4. Đặt tên gợi nhớ nhóm và chủ đề. Chọn đúng thư mục Article mà thầy chỉ dẫn.
5. Nộp bản Word; PDF chỉ kèm thêm khi được yêu cầu. Tạo file tại máy chưa phải đã nộp.

Không cần chạy bù các thí nghiệm chưa có chỉ để che khoảng trống trước lúc
nhận xét. Bản nghiên cứu có kết quả âm tính và giới hạn rõ vẫn có thể dùng để
thầy nhận xét thiết kế, phương pháp và hướng bổ sung.
