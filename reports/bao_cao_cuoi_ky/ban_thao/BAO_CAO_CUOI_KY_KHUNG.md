<!-- Khung dự kiến 18 trang, tính cả bìa, mục lục, tài liệu tham khảo và phụ lục. -->
<!-- Các đoạn trong ngoặc vuông là hướng dẫn soạn thảo, cần thay bằng nội dung thật. -->
<!-- PAGE 01 | Bìa -->
# BÁO CÁO CUỐI KỲ

Học phần THỊ GIÁC MÁY TÍNH

## Hệ thống nhận diện khuôn mặt thời gian thực tích hợp chống giả mạo dựa trên bản đồ độ sâu

Trường Đại học Bách khoa, Đại học Đà Nẵng

Khoa [Điền tên khoa]

Nhóm 1

| Sinh viên | Mã số sinh viên |
| --- | --- |
| Trịnh Minh Đạt | 102230180 |
| Nguyễn Hữu Minh Quân | 102230208 |

Giảng viên hướng dẫn [Điền tên giảng viên]

Lớp học phần [Điền mã lớp học phần]

Đà Nẵng, tháng 10 năm 2026

<!-- PAGE 02 | Tóm tắt và đóng góp -->
# Tóm tắt đề tài

[Viết khoảng 150–200 từ. Giới thiệu chống giả mạo khuôn mặt, gọi tắt là PAD theo thuật ngữ Presentation Attack Detection. Nêu bài toán phân biệt khuôn mặt thật với ảnh in hoặc video phát lại. Tiếp theo, nêu dữ liệu sử dụng, phương pháp đọc bản đồ độ sâu, thí nghiệm đã hoàn thành, kết quả chính và một giới hạn quan trọng. Chỉ điền số liệu sau khi đối chiếu nguồn kết quả.]

Từ khóa [Điền 4–6 từ khóa và giải thích các thuật ngữ trong nội dung khi xuất hiện lần đầu.]

## Phân công và đóng góp của thành viên

Bảng 1 Công việc và minh chứng của từng thành viên

| Thành viên | Công việc đã thực hiện | Minh chứng |
| --- | --- | --- |
| Trịnh Minh Đạt | [Điền công việc thực tế] | [File, commit hoặc kết quả tương ứng] |
| Nguyễn Hữu Minh Quân | [Điền công việc thực tế] | [File, commit hoặc kết quả tương ứng] |

[Mỗi người xác nhận phần mình đã làm và có thể giải thích. Ghi cụ thể công việc dữ liệu, triển khai, huấn luyện, đánh giá hoặc viết báo cáo; chỉ ghi tỷ lệ đóng góp khi nhóm đã thống nhất.]

<!-- PAGE 03 | Mục lục -->
# Mục lục

[[TOC]]

## Danh mục hình và bảng

[Cập nhật số thứ tự, tên và trang của các hình, bảng sau khi điền nội dung. Dùng chức năng Insert Caption của Word để quản lý chú thích. Các vị trí chèn hình trong khung được đánh số tạm theo chương.]

[Hình dự kiến: quy trình xử lý; dữ liệu mẫu; nhãn độ sâu và bản đồ dự đoán; kiến trúc mô hình; đường học; phân bố điểm; trường hợp dự đoán sai.]

[Bảng dự kiến: phân công; nghiên cứu liên quan; chia dữ liệu; kiểm tra chất lượng nhãn; cấu hình; chỉ số đánh giá; kết quả; đối chiếu lỗi; chi phí suy luận.]

<!-- PAGE 04 | Chương 1 phần đầu -->
# Chương 1 Tổng quan bài toán và hướng nghiên cứu

## 1.1 Bối cảnh và bài toán chống giả mạo

[Giới thiệu tình huống camera quan sát khuôn mặt. Giải thích vì sao ảnh in hoặc video phát lại có thể đánh lừa hệ thống và PAD cần quyết định mẫu quan sát là thật hay giả mạo. Phân biệt nhiệm vụ này với nhận diện danh tính, tức xác định người trong ảnh là ai.]

[Nêu phạm vi của bản báo cáo hiện tại trong tên đề tài đã đăng ký. Chỉ mô tả khả năng nhận diện danh tính hoặc chạy thời gian thực như phần đã hoàn thành nếu có bằng chứng triển khai và đo kiểm.]

## 1.2 Động cơ sử dụng bản đồ độ sâu

[Giải thích bản đồ độ sâu là một ảnh mà mỗi điểm biểu diễn độ sâu tương đối. Trình bày lý do dùng tín hiệu hình học để hỗ trợ PAD và những trường hợp giả mạo khiến giả định này không đủ. Phân biệt độ sâu suy ra từ ảnh RGB với phép đo từ cảm biến độ sâu.]

## 1.3 Mục tiêu và phạm vi thực hiện

[Nêu mục tiêu tổng quát và các mục tiêu kiểm chứng được: chuẩn bị dữ liệu, triển khai mô hình đối chứng, thử bộ phân loại đọc bản đồ độ sâu, đánh giá lỗi và chi phí. Ghi rõ dataset, loại tấn công và các thành phần đã thực hiện.]

[Kết đoạn bằng phạm vi kết luận mà các thí nghiệm hiện tại có thể hỗ trợ.]

<!-- PAGE 05 | Chương 1 phần sau -->
## 1.4 Nghiên cứu liên quan và lựa chọn phương pháp đối chứng

[Giới thiệu các hướng phân loại trực tiếp từ ảnh RGB, học với nhãn độ sâu và các hướng kiến trúc khác. Sau đó giới thiệu mạng tích chập sai phân trung tâm, tên tiếng Anh Central Difference Convolutional Network, viết tắt CDCN. Giải thích vì sao nhóm chọn mô hình này làm đối chứng trong điều kiện hiện có.]

Bảng 1.1 Các công trình liên quan đến câu hỏi của nhóm

| Công trình | Ý tưởng liên quan | Điều kiện đánh giá | Vai trò trong báo cáo |
| --- | --- | --- | --- |
| [Tên, năm, tài liệu dẫn] | [Phương pháp] | [Dataset và protocol] | [Đối chứng đã chạy hoặc tài liệu khảo sát] |
| [Tên, năm, tài liệu dẫn] | [Phương pháp] | [Dataset và protocol] | [Vai trò] |
| [Tên, năm, tài liệu dẫn] | [Phương pháp] | [Dataset và protocol] | [Vai trò] |

[Phân biệt mô hình đã chạy với công trình mới khảo sát. Khi đề cập phương pháp mới hơn hoặc mạnh hơn, nêu nguồn và điều kiện so sánh. Xác định phần ý tưởng đã có tiền lệ.]

## 1.5 Câu hỏi nghiên cứu và cách trả lời

[Câu hỏi chính: khi giữ nguyên mô hình dự đoán độ sâu, bộ phân loại nhỏ học từ bản đồ dự đoán có giảm lỗi chống giả mạo so với lấy trung bình bản đồ hay không, và tăng bao nhiêu chi phí?]

[Nêu thiết kế trả lời: giữ nguyên dữ liệu, trọng số mô hình tạo độ sâu và cách tổng hợp theo video; chỉ thay bộ đọc bản đồ. Mỗi phương án được chọn ngưỡng bằng cùng quy tắc trên validation, tức tập dùng để chọn cấu hình và ngưỡng.]

<!-- PAGE 06 | Chương 2 dữ liệu và chia tập -->
# Chương 2 Dữ liệu và quy trình xử lý

## 2.1 Bộ dữ liệu và các loại mẫu

[Giới thiệu CASIA Face Anti-Spoofing Database, viết tắt CASIA-FASD, nguồn dữ liệu và phiên bản đang sử dụng. Mô tả mẫu thật, ảnh giả mạo, video phát lại, các mức chất lượng và đơn vị dữ liệu gốc. Dẫn tài liệu dataset.]

[CHÈN HÌNH 2.1: ảnh mẫu thật và các loại tấn công từ dữ liệu đã được phép sử dụng. Chú thích loại mẫu và nguồn.]

## 2.2 Chia dữ liệu để huấn luyện và đánh giá

[Giải thích train dùng để học trọng số, validation dùng để chọn mô hình/ngưỡng và test dùng để đánh giá. Nêu cách tách người tham gia và video để tránh các frame gần giống nhau xuất hiện ở nhiều tập.]

Bảng 2.1 Số lượng dữ liệu theo từng tập

| Tập | Người tham gia | Video | Frame | Quy tắc chọn |
| --- | --- | --- | --- | --- |
| Train | [Điền] | [Điền] | [Điền] | [Điền] |
| Validation | [Điền] | [Điền] | [Điền] | [Điền] |
| Test | [Điền] | [Điền] | [Điền] | [Điền] |

[Ghi rõ đây là protocol nào và có khác protocol công bố hay không. Nếu test đã được xem trong quá trình phát triển, nêu đúng vai trò hiện tại của tập đó.]

<!-- PAGE 07 | Chương 2 tiền xử lý và nhãn -->
## 2.3 Lấy frame và tiền xử lý ảnh

[Mô tả lần lượt cách lấy frame từ video, xử lý vùng khuôn mặt nếu có, thay đổi kích thước và chuẩn hóa ảnh. Nêu số frame/video và cách xử lý mẫu lỗi. Nếu các mô hình dùng kích thước hoặc chuẩn hóa khác nhau, ghi rõ từng trường hợp.]

[CHÈN HÌNH 2.2: luồng video đến frame đầu vào. Ghi kích thước ảnh ở từng bước.]

## 2.4 Tạo nhãn độ sâu để huấn luyện

[Giới thiệu 3DDFA V2 là công cụ ước lượng hình học khuôn mặt từ ảnh. Giải thích cách nhóm dùng công cụ để tạo nhãn độ sâu suy ra, còn gọi là pseudo-depth, cho mẫu thật; mô tả nhãn bản đồ bằng không cho mẫu tấn công theo thiết kế.]

[Phân biệt nhãn độ sâu dùng để huấn luyện với bản đồ độ sâu do mô hình PAD dự đoán. Nêu mask, tức vùng điểm ảnh được chọn khi tạo nhãn hoặc tính loss, nếu triển khai sử dụng. Giải thích vì sao bước tạo nhãn được thực hiện trước huấn luyện và có cần chạy khi suy luận hay không.]

[CHÈN HÌNH 2.3: RGB, nhãn độ sâu, mask và bản đồ dự đoán của cùng một mẫu. Ghi rõ mẫu thuộc train, validation hay test và nguồn tạo từng ảnh.]

<!-- PAGE 08 | Chương 2 kiểm tra dữ liệu -->
## 2.5 Kiểm tra chất lượng ảnh và nhãn độ sâu

[Nêu tiêu chí kiểm tra file tồn tại, đọc được, đúng kích thước, giá trị hữu hạn, nhãn mẫu thật hợp lệ và nhãn mẫu tấn công đúng quy tắc. Trình bày các mẫu thiếu hoặc lỗi và cách xử lý.]

Bảng 2.2 Kết quả kiểm tra dữ liệu và nhãn

| Hạng mục | Tổng kiểm tra | Hợp lệ | Lỗi hoặc thiếu | Cách xử lý |
| --- | --- | --- | --- | --- |
| Ảnh RGB | [Điền] | [Điền] | [Điền] | [Điền] |
| Nhãn mẫu thật | [Điền] | [Điền] | [Điền] | [Điền] |
| Nhãn mẫu tấn công | [Điền] | [Điền] | [Điền] | [Điền] |

## 2.6 Lưu danh sách mẫu và kiểm tra tính nhất quán

[Giới thiệu manifest là file liệt kê từng mẫu, đường dẫn, nhãn, video và tập dữ liệu. Nêu cách kiểm tra không trùng người/video giữa các tập và cách xác nhận các phương án dùng cùng danh sách mẫu.]

[Ghi vị trí manifest, báo cáo kiểm tra dữ liệu và phiên bản mã nguồn. Với file trên Google Drive hoặc Colab, phân biệt đường dẫn trong phiên chạy với đường dẫn lưu lâu dài.]

[Nêu các hạn chế còn lại của nhãn suy ra và dữ liệu, chẳng hạn sai hình học ở góc mặt khó hoặc thiếu dữ liệu ngoài miền.]

<!-- PAGE 09 | Chương 3 tổng thể và E0 -->
# Chương 3 Phương pháp và triển khai

## 3.1 Quy trình xử lý và các phương án thực nghiệm

[Giới thiệu ba ký hiệu dùng xuyên suốt phần thực nghiệm: E0 là mô hình phân loại trực tiếp từ RGB; E1 là CDCN với điểm trung bình bản đồ độ sâu; E2 là CDCN với bộ phân loại nhỏ học từ bản đồ độ sâu. Bộ phân loại này được gọi là learned depth head.]

[CHÈN HÌNH 3.1: luồng RGB đến quyết định thật/giả mạo của ba phương án. Đánh dấu phần học từ dữ liệu và phần giữ cố định.]

## 3.2 Mô hình phân loại RGB E0

[Giới thiệu MobileNetV3-Small là mạng trích xuất đặc trưng ảnh dùng cho E0. Mô tả trọng số tiền huấn luyện nếu có, đầu phân loại nhị phân, kích thước ảnh đầu vào và cách tạo điểm dự đoán.]

[Giải thích logit là giá trị đầu ra trước khi đổi thành điểm trong khoảng 0–1; sigmoid là phép đổi dùng trong phân loại nhị phân. Nêu loss huấn luyện và vai trò tham khảo của E0.]

[Giải thích các yếu tố khác nhau giữa E0 và E1. Chỉ kết luận tác động riêng của depth khi thiết kế thực nghiệm thực sự cô lập được yếu tố đó.]

<!-- PAGE 10 | Chương 3 E1 -->
## 3.3 Mô hình CDCN với điểm trung bình độ sâu E1

[Giải thích phép tích chập sai phân trung tâm, vai trò hệ số theta, cách hợp nhất đặc trưng nhiều tỉ lệ và đầu ra bản đồ độ sâu. Giới thiệu backbone là phần mạng tạo ra đặc trưng và bản đồ độ sâu trước bộ đọc điểm.]

[CHÈN HÌNH 3.2: sơ đồ CDCN thực tế, kèm kích thước tensor chính. Giải thích tensor là mảng số nhiều chiều. Đối chiếu sơ đồ với mã nguồn trước khi chèn.]

[Nêu công thức lấy trung bình bản đồ thành điểm frame. Ghi rõ có dùng mask khi chấm điểm hay không và phạm vi giá trị thực tế của đầu ra.]

## 3.4 Kiểm chứng triển khai theo mã tác giả

[Nêu nguồn mã tác giả, commit được khóa và cách đối chiếu kiến trúc, trọng số hoặc đầu ra. Điền kết quả verifier từ log, kèm điều kiện của phép kiểm tra.]

[Phân biệt phần giữ theo tác giả với phần nhóm thay đổi: dữ liệu, công cụ tạo nhãn, tiền xử lý, lịch huấn luyện và cách tính điểm. Phạm vi tuyên bố tái lập phải phù hợp với các kiểm tra đã thực hiện.]

<!-- PAGE 11 | Chương 3 E2 và loss -->
## 3.5 Bộ phân loại học từ bản đồ độ sâu E2

[Mô tả E2 nhận bản đồ dự đoán từ checkpoint E1. Giải thích checkpoint là trạng thái mô hình được lưu sau một mốc huấn luyện. Trình bày các lớp của head, kích thước đầu vào/đầu ra và số tham số bổ sung.]

[CHÈN HÌNH 3.3: backbone giữ cố định, bản đồ độ sâu và learned depth head. Nối rõ chiều truyền dữ liệu.]

[Giải thích đóng băng trọng số và giữ cố định thống kê Batch Normalization, tức các thống kê chuẩn hóa trong mạng. Nêu cách kiểm tra tensor backbone và bản đồ dự đoán không đổi sau khi học head.]

## 3.6 Hàm mất mát của từng phương án

[Giải thích loss là đại lượng đo sai lệch được tối ưu khi huấn luyện. Giới thiệu Binary Cross Entropy, viết tắt BCE, cho phân loại nhị phân; Mean Squared Error, viết tắt MSE, cho hồi quy độ sâu. Sau đó trình bày các thành phần loss độ sâu tuyệt đối và sai phân cục bộ đang thực sự sử dụng.]

[Điền công thức, trọng số và tập tham số được cập nhật cho E0, E1, E2. Với E2 frozen head, nêu rõ loss nào được tắt và vì sao backbone không được cập nhật.]

<!-- PAGE 12 | Chương 3 train và inference -->
## 3.7 Cấu hình và quy trình huấn luyện

Bảng 3.1 Cấu hình của các phương án đã chạy

| Thiết lập | E0 | E1 | E2 |
| --- | --- | --- | --- |
| Đầu vào và chuẩn hóa | [Điền] | [Điền] | [Điền] |
| Khởi tạo mô hình | [Điền] | [Điền] | [Điền checkpoint] |
| Phần được cập nhật | [Điền] | [Điền] | [Điền] |
| Loss | [Điền] | [Điền] | [Điền] |
| Optimizer và learning rate | [Điền] | [Điền] | [Điền] |
| Batch size và số epoch | [Điền] | [Điền] | [Điền] |
| Tiêu chí chọn checkpoint | [Điền] | [Điền] | [Điền] |

[Giải thích optimizer là thuật toán cập nhật trọng số; learning rate là mức cập nhật; batch size là số mẫu mỗi bước; epoch là một lượt qua tập train. Điền seed, phiên bản thư viện và cơ chế lưu kết quả.]

## 3.8 Suy luận và quyết định theo video

[Mô tả cách nhận điểm từng frame, tổng hợp thành điểm video và so với ngưỡng quyết định. Nêu chiều điểm: giá trị cao biểu thị mẫu thật hay mẫu giả.]

[Giải thích quy tắc chọn ngưỡng trên validation và cách giữ ngưỡng đó khi đánh giá test. Ghi rõ lý do mỗi mô hình có ngưỡng riêng khi thang điểm khác nhau.]

<!-- PAGE 13 | Chương 4 thiết lập và metric -->
# Chương 4 Thực nghiệm và đánh giá

## 4.1 Thiết lập thực nghiệm và điều kiện so sánh

[Nêu phần cứng, phần mềm, các run đã hoàn thành, seed và đơn vị đánh giá. Ghi rõ phép so sánh chính E1–E2 sử dụng những thành phần chung nào và chỉ thay đổi thành phần nào. Đưa đường dẫn run đầy đủ vào phụ lục.]

## 4.2 Chỉ số đánh giá

Bảng 4.1 Các chỉ số dùng trong báo cáo

| Chỉ số | Nội dung cần giải thích | Chiều tốt hơn |
| --- | --- | --- |
| APCER | Tỷ lệ mẫu tấn công bị chấp nhận thành mẫu thật | Thấp hơn |
| BPCER | Tỷ lệ mẫu thật bị từ chối thành mẫu tấn công | Thấp hơn |
| ACER | Trung bình APCER và BPCER | Thấp hơn |
| EER | Lỗi gần điểm cân bằng APCER và BPCER | Thấp hơn |
| AUC | Diện tích dưới đường ROC khi thay đổi ngưỡng | Cao hơn |

[Viết tên đầy đủ của từng chữ viết tắt khi trình bày. Giải thích ROC biểu diễn tỷ lệ chấp nhận đúng và chấp nhận sai theo ngưỡng. Điền công thức, mẫu số, đơn vị phần trăm hay 0–1 và cách nội suy EER nếu có.]

[Phân biệt ACER tại ngưỡng validation đã khóa với các chỉ số mô tả khi quét ngưỡng.]

<!-- PAGE 14 | Chương 4 bảng kết quả và đối chứng -->
## 4.3 Kết quả của các phương án đã thực hiện

Bảng 4.2 Kết quả theo video trên CASIA test phát triển

| Phương án | APCER % | BPCER % | ACER % | EER % | AUC |
| --- | --- | --- | --- | --- | --- |
| E0 phân loại RGB | 0,0000 | 11,1111 | 5,5556 | 2,4074 | 0,997984 |
| E1 trung bình độ sâu | 0,0000 | 5,5556 | 2,7778 | 2,2222 | 0,994444 |
| E2 learned depth head | 0,0000 | 5,5556 | 2,7778 | 2,2222 | 0,994321 |

CASIA test phát triển gồm 270 video tấn công và 90 video thật, seed 42; điểm video là trung bình điểm frame. Ngưỡng chọn trên validation: E0 0,9900876432657242; E1 0,1916038803756237; E2 0,41177915 (số hiển thị 8 chữ số). Số video thật bị từ chối sai lần lượt là 10, 5 và 5; cả ba không chấp nhận sai video tấn công nào.

Trên validation riêng gồm 36 video tấn công và 12 video thật, cả ba có APCER, BPCER, ACER, EER bằng 0% và AUC bằng 1. Nguồn test: notebook E0 cell 43, Official E1 cell 28 và E2 cell 15; validation: lần lượt cell 35, 24 và 13, đếm từ 1 gồm cả cell Markdown. Đây là output đã lưu, chưa tính lại metric từ CSV gốc.

## 4.4 So sánh chính giữa E1 và E2

[Đối chiếu lỗi tại ngưỡng đã khóa, chất lượng xếp hạng và chi phí bổ sung. Nêu chính xác chỉ số nào tốt hơn, bằng nhau hoặc kém hơn; phân biệt thay đổi điểm số với thay đổi quyết định.]

[Trả lời câu hỏi nghiên cứu bằng kết quả hiện có. Nếu chưa thấy cải thiện, trình bày đó là kết quả của cấu hình và điều kiện đã thử. Phân biệt việc head đã học được trọng số/điểm với việc head cải thiện khả năng phân loại.]

[Khi liên hệ với paper CDCN, nêu rõ đây là đối chứng triển khai trong điều kiện nhóm; chỉ so số công bố trực tiếp nếu metric và protocol tương thích.]

<!-- PAGE 15 | Chương 4 đường học và định tính -->
## 4.5 Diễn biến huấn luyện và chọn checkpoint

[CHÈN HÌNH 4.1: đường train/validation loss, đánh dấu checkpoint được chọn. Dùng lịch sử của đúng run và đúng mô hình.]

E0 chạy 5 epoch, chọn epoch 5 theo BCE validation thấp nhất trong log; Official E1 chạy 30 epoch, chọn epoch 25 theo loss độ sâu validation; E2 chạy 10 epoch, chọn epoch 1 theo BCE validation. Epoch là một lượt qua tập huấn luyện; Binary Cross Entropy, viết tắt BCE, là hàm mất mát phân loại nhị phân. Các kết quả sử dụng best.ckpt của từng run, không mặc định dùng epoch cuối. Nguồn: notebook E0 cell 35, Official E1 cell 24, E2 cell 13 và quy tắc lưu checkpoint trong src/deepface_pad/train.py.

[CHÈN HÌNH 4.2: phân bố điểm mẫu thật/tấn công và ngưỡng validation của E1, E2. Giữ trục và thang điểm riêng nếu khác nhau.]

## 4.6 Đánh giá bản đồ độ sâu dự đoán

[CHÈN HÌNH 4.3: RGB, nhãn độ sâu và bản đồ dự đoán của các mẫu đại diện. Chú thích đúng split, nhãn và quyết định.]

[Mô tả những gì nhìn thấy như hình dạng vùng mặt, độ trơn, vùng bị mất hoặc nhiễu. Phân biệt nhận xét từ hình minh họa với kết luận định lượng. Dùng cùng mẫu khi so sánh hai bộ đọc của cùng backbone.]

<!-- PAGE 16 | Chương 4 lỗi chi phí giới hạn -->
## 4.7 Đối chiếu các trường hợp dự đoán sai

Bảng 4.3 So sánh quyết định của E1 và E2 trên cùng video

| Trạng thái | Số video | Nhận xét |
| --- | --- | --- |
| Cùng đúng | [Điền] | [Điền] |
| E1 sai và E2 đúng | [Điền] | [Điền] |
| E1 đúng và E2 sai | [Điền] | [Điền] |
| Cùng sai | [Điền] | [Điền] |

[Liệt kê mã video lỗi, nhãn, điểm và ngưỡng tương ứng. Chỉ giải thích nguyên nhân về ánh sáng, góc mặt hoặc dữ liệu sau khi xem đúng mẫu lỗi.]

## 4.8 Chi phí mô hình và thời gian suy luận

[Điền bảng số tham số, tham số bổ sung, độ trễ và phần cứng. Giải thích p50/p95 là các phân vị độ trễ; FPS là số frame xử lý mỗi giây. Ghi ranh giới đo, batch size, số lượt làm nóng và đo lặp. Phân biệt thời gian chạy riêng mô hình với toàn bộ camera pipeline.]

## 4.9 Giới hạn của kết quả

[Nêu số seed, phạm vi dataset và loại tấn công, tình trạng test đã quan sát, độ tin cậy của nhãn suy ra và các đối chứng chưa chạy. Giải thích mỗi giới hạn ảnh hưởng đến kết luận nào.]

<!-- PAGE 17 | Kết luận -->
# Kết luận và hướng phát triển

## Kết luận từ các thí nghiệm đã hoàn thành

[Tóm tắt bài toán, phương pháp, phần triển khai đã kiểm chứng và kết quả trả lời câu hỏi nghiên cứu. Nêu vai trò E0, đối chứng E1 và phép thử E2. Chỉ sử dụng các số đã xuất hiện ở phần kết quả.]

[Nêu phần nhóm đã tự thực hiện và phần kế thừa mã, kiến trúc hoặc ý tưởng từ nghiên cứu trước. Giới hạn kết luận trong dữ liệu và điều kiện đã thử.]

## Công việc tiếp theo

[Ưu tiên việc cần làm từ các lỗi và giới hạn đã nêu. Nếu đề cập E3 hoặc E4, định nghĩa từng phương án trước và ghi rõ trạng thái chưa thực nghiệm khi chưa có kết quả.]

Bảng K1 Công việc còn lại và bằng chứng cần thu

| Công việc | Mục đích | Bằng chứng cần có |
| --- | --- | --- |
| [Điền ưu tiên 1] | [Câu hỏi cần trả lời] | [Log, metric hoặc hình] |
| [Điền ưu tiên 2] | [Câu hỏi cần trả lời] | [Log, metric hoặc hình] |
| [Điền ưu tiên 3] | [Câu hỏi cần trả lời] | [Log, metric hoặc hình] |

<!-- PAGE 18 | Tài liệu tham khảo và phụ lục -->
# Tài liệu tham khảo

[Điền tài liệu thực sự được dẫn trong nội dung, đánh số nhất quán. Mỗi mục gồm tác giả, tên công trình, nơi công bố, năm và DOI hoặc URL. Kiểm tra nguồn gốc cho dataset, CDCN, 3DDFA V2 và các phương pháp liên quan.]

[1] [Tác giả, tên công trình, nơi công bố, năm, DOI hoặc URL.]

[2] [Tài liệu nguồn bộ dữ liệu.]

[3] [Mã nguồn tác giả và commit được dùng.]

# Phụ lục minh chứng và tái lập

## A Danh sách nguồn kết quả

Bảng bằng chứng kèm báo cáo, BANG_BANG_CHUNG.md, ghi run ID, cấu hình, checkpoint, ngưỡng, split, đơn vị và vị trí output của E0, Official E1 và E2. Ba notebook gốc khớp từng byte với bản sao cục bộ khi đối chiếu ngày 15/10/2026. Raw CSV/JSON và checkpoint trên Drive chưa được tải lại để kiểm toán độc lập; ngưỡng E2 hiện chỉ được xác nhận ở 8 chữ số hiển thị.

[Các nguồn cần đối chiếu trong repository: notebooks/E0.ipynb; notebooks/Face_PAD_Official_CDCN_E1_Rerun.ipynb; notebooks/Face_PAD_Round4_Official_Frozen_Head.ipynb. Bổ sung đúng run đang báo cáo nếu có thay đổi.]

## B Hướng dẫn chạy và kiểm tra

[Ghi phiên bản mã, môi trường, lệnh tạo nhãn, huấn luyện và đánh giá. Nêu nơi lưu artifact. Đưa cấu hình dài và bảng chi tiết vào phụ lục riêng nếu dung lượng cho phép, đồng thời giữ tổng báo cáo trong 15–20 trang.]
