# QUY TẮC BIÊN TẬP HỌC THUẬT VÀ LOẠI BỎ NHẬT KÝ NỘI BỘ DÀNH CHO AI AGENT

## 1. NGUYÊN TẮC CỐT LÕI: MỤC ĐÍCH CỦA BÀI BÁO KHOA HỌC (PAPER) VÀ BÁO CÁO KỸ THUẬT (REPORT)

Khi viết hoặc biên tập một bài báo khoa học (Research Paper) hoặc báo cáo kỹ thuật (Technical Report) trong lĩnh vực Khoa học Máy tính và Trí tuệ Nhân tạo:
- **Mục đích duy nhất của tài liệu** là trình bày: (1) Định nghĩa bài toán và động cơ nghiên cứu, (2) Cơ sở lý thuyết và kiến trúc phương pháp, (3) Thiết lập thực nghiệm (dữ liệu, siêu tham số, chỉ số đánh giá) đủ để độc giả độc lập hiểu và tái lập về mặt toán học/thuật toán, và (4) Kết quả định lượng kèm phân tích bản chất khoa học.
- **Tài liệu khoa học KHÔNG PHẢI là nhật ký quản trị hệ thống (system administration log), biên bản kiểm toán tệp (file audit log) hay sổ tay vận hành mã nguồn (runbook).**
- Do đó, đối với mọi thông tin về việc lưu trữ tệp, đường dẫn thư mục, mã định danh lần chạy (`run ID`), mã băm tệp (`SHA-256`), tệp `.csv`/`.json` trung gian, hay trạng thái ổ đĩa: **TUYỆT ĐỐI KHÔNG viết lại cho mượt hơn mà phải XÓA BỎ HOÀN TOÀN** khỏi nội dung chính của bài báo và báo cáo (trừ khi người dùng yêu cầu giữ một phụ lục mã nguồn riêng biệt).

---

## 2. QUY TẮC LOẠI BỎ TRIỆT ĐỂ NHẬT KÝ VẬN HÀNH & GHI CHÚ NỘI BỘ CỦA AI (STRICT DE-LOGGING)

AI Agent phải tự động phát hiện và **xóa bỏ hoàn toàn** (không dịch, không viết lại) 6 nhóm thông tin nhiễu sau đây khỏi văn bản:

### 2.1. Nhật ký quản lý tệp, đường dẫn lưu trữ và kiểm toán mã băm (File & Storage Bookkeeping)
- **Xóa bỏ hoàn toàn** các câu mô tả nơi lưu trữ trọng số, nhật ký huấn luyện, tệp CSV điểm số, đường dẫn Colab/Drive (`/content/...`, `/drive/...`), tên tệp JSON kiểm toán (`RESEARCH_AUDIT...json`), hoặc việc đối khớp số dòng trong tệp CSV với tệp manifest.
  - ❌ *Sai (Giữ lại và viết văn hoa):* "Toàn bộ trọng số mô hình, nhật ký huấn luyện và tệp điểm số được lưu trữ tập trung theo mã định danh duy nhất của từng lần chạy."
  - ❌ *Sai (Báo cáo kiểm toán tệp):* "Đối chiếu lại 7.200 frame và 360 video của mỗi cấu hình khớp nhãn và mean score; các chỉ số tính lại khớp artifact lưu trong sai số $10^{-12}$."
  - ✅ *Quy tắc xử lý:* **Xóa bỏ hoàn toàn.** Trong bài báo khoa học, tính chính xác của phép tính là điều kiện mặc định của công cụ lập trình, không bao giờ đưa việc "tính lại từ file CSV thấy khớp" vào nội dung báo cáo.

### 2.2. Câu lệnh thực thi, kiểm thử phần mềm và quy trình dựng tài liệu (CLI, Test & Build Logs)
- **Xóa bỏ hoàn toàn** mọi câu lệnh terminal, lệnh chạy unittest (`python -m unittest...`), quy trình chạy thử (`preflight`, `smoke test`, `full run`), hoặc mô tả cách chuyển đổi định dạng văn bản (`Markdown sang Word`, `cập nhật mục lục trong Word`).

### 2.3. Lịch sử lỗi mã nguồn và quá trình gỡ lỗi trong Notebook (Debugging & Historical Run Artifacts)
- **Xóa bỏ hoàn toàn** các ghi chú về việc ô lệnh (cell) trong Jupyter/Colab bị lỗi rồi được sửa ở ô sau, sự khác biệt với các bản chạy nháp cũ (`pilot cũ`, `E1-Lite`, `smoke`), hoặc việc thiếu dữ liệu lịch sử do chưa chạy lại.
  - ❌ *Sai:* "Không dùng loss L1 của pilot cũ để mô tả các run Official E1–E4. Các bảng chính loại smoke và E1-Lite Pilot."
  - ✅ *Quy tắc xử lý:* **Xóa bỏ hoàn toàn.** Chỉ trình bày phương pháp và kết quả của các cấu hình chính thức có mặt trong bài.

### 2.4. Các câu "tự răn đe" dạng mệnh lệnh nội bộ của AI (Self-Guardrail Imperatives)
- Các mô hình AI thường chép nguyên các quy tắc ràng buộc trong prompt (dạng *"Không được..."*, *"Không dùng..."*, *"Không suy ra..."*, *"Không gọi..."*) vào cuối mỗi đoạn văn như một lời tự nhắc nhở.
- **Quy tắc xử lý:**
  - Nếu câu mệnh lệnh đó là quy tắc kiểm soát nội bộ hiển nhiên (ví dụ: *"Không lấy epoch cuối theo mặc định"*, *"Không dùng màu ảnh hiển thị để suy luận nguyên nhân lỗi"*, *"Không gọi kết quả này là hệ thống bảo mật đã kiểm định"*, *"Sơ đồ được dựng từ triển khai, không phải hình chứng minh hiệu quả"*): **Xóa bỏ hoàn toàn.**
  - Nếu câu mệnh lệnh đó chứa thông tin phương pháp luận thực sự (ví dụ: quy tắc khóa ngưỡng quyết định trên tập kiểm định): **Chuyển thành câu mô tả phương pháp ở thể khẳng định/bị động khách quan** (Ví dụ: *"Ngưỡng quyết định được xác lập cố định trên tập kiểm định và áp dụng trực tiếp trên tập kiểm tra"*).

### 2.5. Ghi chú hành chính về tài nguyên tính toán, bản quyền thứ cấp và tiến độ cá nhân
- **Xóa bỏ hoàn toàn** các lời nhắc kiểm tra ngân sách GPU (`compute budget`), xác nhận quyền phân phối lại ảnh khuôn mặt từ nguồn thứ cấp (Kaggle), hoặc quy tắc báo cáo khi chạy thiếu số lượng hạt giống ngẫu nhiên (*"Nếu chỉ hoàn thành một cặp thì báo đúng một cặp, không gọi là đủ ba seed"*).

### 2.6. Lời thoại giao tiếp của AI (Conversational Meta-Text)
- Tuyệt đối không chèn lời chào, lời dẫn, giải thích thao tác sửa file hay câu hỏi gợi ý của AI vào bên trong tài liệu đầu ra.

---

## 3. QUY TẮC KHẮC PHỤC LỐI VIẾT NÉN CỰC ĐOAN, ĐA NGHĨA VÀ MƠ HỒ CỦA MÔ HÌNH GPT

Các mô hình ngôn ngữ dòng GPT khi tóm tắt kỹ thuật thường có xu hướng **nén câu cực đoan (telegraphic compression)**, lược bỏ hư từ/quan hệ từ và dùng **một từ đơn lẻ để gánh nhiều tầng ý nghĩa khác nhau (lexical ambiguity / polysemy)**, khiến câu văn tiếng Việt trở nên tối nghĩa, cộc lốc và thiếu tính học thuật. Agent bắt buộc phải nhận diện và sửa triệt để các lỗi sau:

### 3.1. Lỗi dùng một từ đa nghĩa hoặc rút gọn quá mức gây mơ hồ (Lexical Ambiguity)

| Từ viết tắt / Mơ hồ (Thường gặp ở GPT) | Tại sao sai / Mơ hồ trong văn cảnh học thuật? | Cách viết chuẩn xác (Phân biệt rõ theo ngữ cảnh) |
| :--- | :--- | :--- |
| **"bộ phân loại học từ bản đồ"** | Từ *"học"* đứng sau *"bộ phân loại"* bị đọc nhầm thành danh từ ghép *"phân loại học"* (taxonomy) hoặc động từ không rõ chủ ngữ. | - *Nếu chỉ bản chất có tham số:* **"nhánh phân loại có huấn luyện"** hoặc **"bộ phân loại học sâu trên bản đồ độ sâu"**.<br>- *Nếu chỉ hành động:* **"bộ phân loại được huấn luyện trực tiếp từ bản đồ độ sâu"**. |
| **"bộ đọc" / "cách đọc"** | Từ *"đọc"* quá khẩu ngữ, vừa có nghĩa là đọc tệp từ ổ cứng (`file read`), vừa bị GPT dùng để chỉ tầng đầu ra của mạng (`readout layer / classification head`). | - *Với E1:* **"phương pháp tính điểm bằng trung bình không gian"**.<br>- *Với E2–E4:* **"nhánh phân loại đầu ra (classification head)"** hoặc **"cơ chế trích xuất điểm phân loại"**. |
| **"bản"** (*bản frame, bản nguồn, bản dẫn xuất, bản sao*) | Một từ *"bản"* bị dùng lặp lại để chỉ cả tập dữ liệu, tệp danh mục (manifest), phiên bản tiền xử lý lẫn ảnh đã cắt. | Phân tách rõ: **"phiên bản tập dữ liệu"**, **"tệp danh mục gốc"**, **"các tệp ảnh đã qua xử lý hậu kỳ"**. |
| **"mẫu"** (*mẫu trước camera, 3.000 mẫu, cùng mẫu*) | Không phân biệt được *"mẫu"* là chủ thể (subject), đoạn video (video clip) hay khung hình đơn lẻ (frame). | Ghi rõ đơn vị: **"đối tượng trước camera"**, **"3.000 khung hình (frames)"**, **"360 video kiểm tra"**, **"50 chủ thể (subjects)"**. |
| **"nhãn suy ra" / "target suy ra"** | Từ *"suy ra"* mang nghĩa suy diễn logic chung chung, không phản ánh bản chất ước lượng 3D ngoại tuyến. | Dùng thống nhất: **"bản đồ giả độ sâu (pseudo-depth map)"** hoặc **"nhãn độ sâu ước lượng ngoại tuyến"**. |
| **"điểm"** (*điểm của bản đồ vs. điểm người thật*) | Trộn lẫn giữa "điểm ảnh / phần tử ma trận" (pixel / element) và "điểm số phân loại" (prediction score). | Phân biệt rõ: **"giá trị các phần tử (điểm ảnh) trên bản đồ độ sâu"** và **"điểm số dự đoán người thật (liveness score)"**. |
| **"lịch" / "lịch học"** | Nghe giống "thời khóa biểu môn học" của sinh viên hơn là thuật ngữ học máy. | Dùng: **"lịch trình huấn luyện (training schedule)"** hoặc **"chiến lược huấn luyện theo giai đoạn"**. |
| **"tách người"** | Khẩu ngữ, thiếu tính trang trọng. | Dùng: **"phân chia dữ liệu độc lập theo chủ thể (subject-disjoint split)"**. |
| **"ghép quyết định" / "ghép video"** | Tối nghĩa, người đọc không hiểu là nối video lại với nhau hay so sánh kết quả trên cùng một video. | Dùng: **"đối chiếu kết quả phân loại trên từng cặp video tương ứng (paired video-level comparison)"**. |
| **"đổi một lỗi theo mỗi chiều"** | Quá vắn tắt, khó hình dung mối quan hệ giữa hai mô hình A và B. | Dùng: **"mỗi cấu hình khắc phục được 1 video lỗi của cấu hình kia nhưng đồng thời phát sinh 1 lỗi mới ở chiều ngược lại"**. |
| **"chênh nhỏ nhất"** | Thiếu danh từ trung tâm (chênh lệch của cái gì?). | Dùng: **"độ chênh lệch tuyệt đối giữa hai tỷ lệ lỗi APCER và BPCER đạt giá trị nhỏ nhất"**. |
| **"bỏ freeze" / "khóa"** | Trộn từ Anh–Việt hoặc dùng từ *"khóa"* cho cả khóa phiên bản code, khóa ngưỡng lẫn đóng băng trọng số mạng. | Phân biệt rõ: **"đóng băng (freeze) / mở khóa (unfreeze) trọng số mạng khung"** và **"cố định (lock/fix) ngưỡng quyết định"**. |

### 3.2. Lỗi nén mệnh đề quan hệ nhân quả thành cụm danh từ cụt (Collapsed Causal Clauses)
GPT thường cắt bỏ toàn bộ liên từ (*mặc dù, tuy nhiên, do đó, dẫn đến việc...*) và ghép các ký hiệu kỹ thuật sát nhau làm người đọc phải tự đoán mối quan hệ logic.

- **Ví dụ 1 (Nén quá mức):**
  - ❌ *Thô:* "E2–E3 cũng khác budget/LR nên không cô lập riêng tác động bỏ freeze."
  - ✅ *Chuẩn:* "Ngoài ra, do hai cấu hình E2 và E3 khác nhau đồng thời về số chu kỳ huấn luyện (epoch budget) và tốc độ học (learning rate), phép so sánh giữa chúng phản ánh hiệu quả tổng hợp của toàn bộ thiết lập huấn luyện thay vì chỉ cô lập riêng tác động của việc mở khóa (unfreeze) mạng khung."

- **Ví dụ 2 (Liệt kê không đồng đẳng):**
  - ❌ *Thô:* "Chúng tôi so sánh CDCN lấy trung bình bản đồ, nhánh phân loại với backbone cố định, huấn luyện đồng thời, huấn luyện theo giai đoạn và Focal loss." *(Lỗi: Đánh đồng kiến trúc mạng, chiến lược huấn luyện và hàm mất mát vào chung một danh sách ngang hàng).*
  - ✅ *Chuẩn:* "Chúng tôi đối sánh phương pháp tính điểm bằng trung bình không gian của CDCN đối chứng với nhánh phân loại học sâu dưới bốn thiết lập: đóng băng mạng khung, huấn luyện đồng thời với hàm mất mát BCE, huấn luyện theo giai đoạn với hàm BCE và huấn luyện theo giai đoạn với hàm mất mát Focal."

- **Ví dụ 3 (Viết tắt điều kiện toán học gây khó hiểu):**
  - ❌ *Thô:* "Target được resize về $32 \times 32$; nếu cực đại lớn hơn 1 thì chia theo cực đại."
  - ✅ *Chuẩn:* "Bản đồ độ sâu mục tiêu được thay đổi kích thước về $32 \times 32$; trong trường hợp giá trị cực đại trên bản đồ vượt quá $1$, toàn bộ bản đồ được chuẩn hóa về đoạn $[0, 1]$ bằng cách chia mỗi phần tử cho giá trị cực đại đó."

- **Ví dụ 4 (Nén giải thích chỉ số đánh giá):**
  - ❌ *Thô:* "E4 có AUC 0,996626, cao hơn E1 0,994444, song ACER tại ngưỡng đã khóa lại cao hơn. Đây là khác biệt giữa khả năng xếp hạng qua các ngưỡng và lỗi tại một điểm vận hành."
  - ✅ *Chuẩn:* "Mặc dù cấu hình E4 đạt chỉ số AUC trên tập kiểm tra cao hơn E1 ($0,996626$ so với $0,994444$), tỷ lệ lỗi ACER của nó tại ngưỡng quyết định cố định lại cao hơn. Hiện tượng này phản ánh sự khác biệt bản chất giữa năng lực xếp hạng phân tách tổng thể xuyên suốt mọi mức ngưỡng (đo bằng AUC) và tỷ lệ lỗi thực tế tại một điểm vận hành cụ thể (đo bằng ACER tại ngưỡng cố định)."

---

## 4. QUY TẮC BẢO TOÀN ĐỊNH DẠNG GỐC VÀ SỐ LIỆU KHI CẬP NHẬT TÀI LIỆU WORD (`.DOCX`)

1. **Bảo toàn tuyệt đối số liệu thực nghiệm:** Giữ nguyên 100% các giá trị số học (tỷ lệ lỗi, chỉ số AUC/MAE, số lượng mẫu, siêu tham số, số lượng tham số mô hình) và công thức toán học.
2. **Chỉnh sửa trực tiếp trên cấu trúc DOM/XML của tệp gốc:**
   - Không tạo tệp `.docx` trắng mới làm mất hệ thống định dạng (`Styles`), lề trang, bố cục đa cột (multi-column layout), khung bảng biểu và hình ảnh nhúng (`<a:blip>`).
   - Khi thay thế văn bản trong một đoạn (`paragraph`), chỉ cập nhật thuộc tính `.text` trên `Run` chứa chữ đầu tiên và **tuyệt đối không xóa các `Run` chứa thẻ ngắt cột/ngắt trang ẩn (`<w:br w:type="column"/>`, `<w:br w:type="page"/>`)** hoặc hình ảnh.
   - Kiểm soát độ dài văn bản sau biên tập tương đương với độ dài đoạn gốc để không làm tràn dòng hoặc phá vỡ bố cục trang của bài báo hai cột.
