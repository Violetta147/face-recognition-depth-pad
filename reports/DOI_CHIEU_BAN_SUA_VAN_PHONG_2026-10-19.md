# Đối chiếu hai bản Word sửa văn phong

Ngày 19/10/2026. Đã kiểm tra hai file `_Revised.docx` trong Downloads với bản
paper và báo cáo học phần trong repository. Sau khi được thông báo các điểm
sai/thiếu, người dùng chọn: sửa tối thiểu các điểm đó, giữ văn phong rồi thay
bản gốc. Hai file Downloads được giữ nguyên, kiểm tra bằng SHA-256.

## Kết quả đối chiếu

- Paper: cả tám bảng giống hoàn toàn bản gốc; hai hình giữ nguyên byte.
- Report: đủ 14 bảng và bốn hình. Mười bảng giữ nguyên toàn bộ nội dung;
  bốn bảng được viết lại phần diễn đạt về phân công, nghiên cứu liên quan,
  QA và kế hoạch. Các bảng kết quả, ngưỡng, MAE, paired counts, video lỗi,
  cấu hình và latency không đổi số liệu.
- Năm công thức của report giữ nguyên. Sáu tài liệu tham khảo của paper và
  bảy tài liệu tham khảo của report không bị mất hoặc đổi nội dung.
- ACER vẫn là E1/E2 2,7778%; E3/E3b 5,0000%; E4 4,4444%. E3 được chọn từ
  validation; không đổi sang E4 theo test. Không chạy lại GPU hoặc checkpoint.

## Những điểm cần sửa và đã sửa

| Vị trí | Vấn đề ở bản sửa | Cách xử lý tối thiểu |
| --- | --- | --- |
| Report, phân công | Đổi mục tiêu phân công 50%–50% thành sự phân bổ đã được xác nhận | Khôi phục tính đề xuất, chưa phải thống kê đóng góp lịch sử |
| Report, kết luận | Gán ACER tăng cho overfitting và dịch chuyển ngưỡng khi chưa kiểm chứng nguyên nhân | Ghi nhận mức tăng lỗi, giữ overfitting là giả thuyết cần kiểm tra |
| Report, kết luận | Gọi AUC E4 0,996626 là cao nhất dù E0 đạt 0,997984 | Giới hạn thứ hạng E4 trong ba nhánh lượt 5, nêu E0 cao hơn |
| Report, mục 4.8 | Gán chênh lệch latency cho xung nhịp và kết luận head hầu như không tăng độ trễ | Nêu phép đo sơ bộ theo thứ tự cố định; chưa xác định nguyên nhân hoặc chứng minh tốc độ |
| Report, mục 3.4 và kết luận | Khẳng định verifier chứng minh chính xác tuyệt đối | Giới hạn ở tensor/đầu ra và điều kiện đầu vào đã kiểm tra |
| Report, mục 3.8 | Gọi chung điểm đầu ra là xác suất | Làm rõ điểm trung bình độ sâu E1 không phải xác suất đã hiệu chuẩn, không chặn trên ở 1 |
| Report, mục 4.7 | Đoạn giải thích video lỗi và quality bị xóa | Khôi phục video được sửa/lỗi mới, số lỗi theo quality và giới hạn giải thích thị giác |
| Report, kế hoạch lượt 6 | Hứa thu được chênh lệch có ý nghĩa thống kê | Chuyển thành ước lượng và kiểm tra; không bảo đảm trước kết quả; ghi 138 epoch chưa chạy |
| Cả hai, nghiên cứu liên quan | “Mạng khung cố định” có thể bị hiểu là mọi cấu hình đều đóng băng trọng số | Dùng “cùng kiến trúc CDCN”; phần E2 vẫn nêu rõ đóng băng trọng số và BatchNorm |
| Paper, thảo luận | Rút bớt giới hạn một seed, quality, MAE và chi phí | Khôi phục giới hạn cần thiết; chưa có MAE E1/E2 cùng phép đo, MAE không phải centimet |
| Cả hai, metric và tái lập | Thiếu một số điều kiện tính EER, nguồn dữ liệu và ranh giới kiểm toán | Khôi phục EER rời rạc, APCER gộp, đường dẫn và điều kiện tái lập; không gọi kiểm toán là huấn luyện mới |
| Paper, tóm tắt Việt | 202 từ, vượt giới hạn tham chiếu 200 từ | Rút tối thiểu còn 196 từ; tóm tắt Anh 132 từ |

## Hình thức và nguồn nội dung

Paper vẫn **5 trang**. Report người dùng gửi xuất thành **35 trang** trong
Word. Sau khi bỏ các ngắt trang cũ bên trong chương, làm sạch đoạn trống,
tách phần phân công và cập nhật mục lục/danh mục, report còn **29 trang**.
Giữ cỡ chữ TNR 13 và giãn dòng 1,3 của báo cáo. Bản dài hơn ngân sách cũ
15–20 trang vì phần diễn giải đã mở rộng; chưa rút gọn lại nội dung để đạt
20 trang. Không ghi bản mới là đã đáp ứng ngân sách cũ.

Đã xem toàn bộ 29 trang report và 5 trang paper; các trang paper không đổi
được đối chiếu với lần render đã xem. Các bảng dài lặp hàng tiêu đề khi sang
trang; không thấy chữ bị cắt, hình chồng chữ hoặc field báo lỗi. Bổ sung số
trang ở chân trang chẵn của paper. PDF/PNG chỉ là tệp QA trong
`artifacts/revised-docx-review-20261019/`, không thay bản Word để nộp.

Nguồn Markdown đã được đồng bộ với nội dung Word mới. Caption và bảng paper
được builder điền từ `scripts/build_round5_paper.py` và audit JSON; không
phải nội dung còn thiếu trong Markdown. Builder report giữ 20 nhãn nội dung
`PAGE` lịch sử để định danh phần, nhưng chỉ ngắt ở phần lớn; 20 nhãn này không
đồng nghĩa 20 trang thực tế. Sau khi dựng lại phải cập nhật field trong Word.

Kết quả kiểm tra: 8/8 kiểm tra report và khung, 5/5 kiểm tra paper, 7/7 kiểm tra
slide. Có kiểm tra trực tiếp bảng của Word hiện tại với Markdown, không chỉ
kiểm tra builder. Notebook lịch sử được kiểm tra cú pháp, không chạy lại Colab.

## Lưu phiên bản

- `bb9d38a`: lưu công việc còn lại đến lượt 5 và giữ nguyên hai Word gốc trước
  khi thay thế. Bản gốc cũng có trong `c881de5`.
- `REVISION_PROVENANCE_2026-10-19.json`: hash bản gốc, bản Downloads, bản nhận,
  số trang, số bảng/hình và các bất biến đã kiểm tra.
- `.obsidian/` được giữ trên máy và bỏ qua trong Git vì là trạng thái giao diện
  cùng mã plugin. Dataset, checkpoint, cache và QA tiếp tục theo `.gitignore`;
  commit không phải bản sao toàn bộ Drive. Chưa push hoặc upload/nộp bài.
