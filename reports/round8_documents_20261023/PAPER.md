# Đánh giá nhánh phân loại độ sâu và độ ổn định của CDCN trên CASIA FASD

::author:: Trịnh Minh Đạt và Nguyễn Hữu Minh Quân

::author:: Khoa Công nghệ thông tin, Trường Đại học Bách khoa, Đại học Đà Nẵng, Việt Nam

<!-- columns -->

::abstract:: Tóm tắt

Nghiên cứu đánh giá nhánh phân loại trên bản đồ giả độ sâu cho phát hiện tấn công trình diện khuôn mặt. CDCN tính điểm bằng trung bình không gian được đối sánh với nhánh phân loại dưới các thiết lập đóng băng, huấn luyện đồng thời, huấn luyện theo giai đoạn và thay BCE bằng Focal. Trên phân chia CASIA-FASD độc lập theo chủ thể, seed 42 cho thấy nhánh đóng băng giữ nguyên tỷ lệ lỗi phân loại trung bình (Average Classification Error Rate, ACER) 2,7778% của đối chứng, còn các cấu hình tinh chỉnh đạt 4,4444–5,0000%. E3 được chọn bằng validation để đánh giá trên ba seed mới 43–45. E1 đạt ACER 4,3210 ± 2,1623%, E3 đạt 3,7037 ± 0,6415%; chênh lệch ghép cặp là −0,6173 ± 2,6857 điểm phần trăm. E3 kém hơn tại seed 44 nên chưa xác nhận cải thiện ổn định. Nhánh phân loại thêm 1.265 tham số và tăng CUDA p50 khoảng 0,7961% trong phép đo A100 batch 1. Phân tích hình lỗi giữ sai khác số học CPU/CUDA; webcam đã đo bộc lộ lỗi từ chối người thật. Bằng chứng giới hạn ở giao thức development đã quan sát, chưa chứng minh khả năng tổng quát hóa hoặc hiệu quả xác thực thực tế.

::keywords:: Từ khóa: Face anti-spoofing; Presentation attack detection; Central difference convolution; Pseudo-depth; Auxiliary supervision.

## 1 Giới thiệu

Phát hiện tấn công trình diện (Presentation Attack Detection – PAD), còn gọi là chống giả mạo khuôn mặt, phân biệt khuôn mặt người thật với các phương tiện giả mạo như ảnh in hoặc video phát lại. Tác vụ này khác với nhận diện danh tính. Giám sát bằng bản đồ độ sâu cung cấp mục tiêu học tại từng điểm ảnh từ đầu vào RGB. Hiệu quả của biểu diễn này phụ thuộc cả kiến trúc dự đoán độ sâu, cơ chế trích xuất điểm phân loại và chiến lược huấn luyện.

Mạng tích chập sai phân trung tâm (Central Difference Convolutional Network – CDCN) kết hợp thông tin cường độ và chênh lệch cục bộ để dự đoán bản đồ độ sâu [1]. Đối chứng E1 tính điểm người thật bằng trung bình không gian của bản đồ. Phép tính này không phân biệt vị trí của các giá trị độ sâu. Nghiên cứu kiểm tra liệu nhánh phân loại được huấn luyện trên cùng bản đồ có giảm tỷ lệ lỗi hay không, sau đó đánh giá ảnh hưởng của huấn luyện đồng thời, huấn luyện theo giai đoạn và hàm mất mát phân loại.

Nghiên cứu cung cấp phép đối sánh giữa trung bình không gian và nhánh phân loại học sâu trên cùng mạng khung CDCN, cùng các đối chứng về chiến lược huấn luyện và hàm mất mát. Phân tích kết hợp chỉ số phân loại cấp video, thay đổi quyết định trên từng video tương ứng và sai số bản đồ giả độ sâu (pseudo-depth). Phạm vi đóng góp là đánh giá thực nghiệm các thiết lập trên kiến trúc có sẵn trong giao thức phát triển CASIA-FASD.

## 2 Nghiên cứu liên quan

Kiến trúc CDCN và biến thể CDCN++ được giới thiệu trong [1]. Nghiên cứu này sử dụng CDCN tiêu chuẩn làm mạng khung dự đoán độ sâu. Quy trình phân chia dữ liệu, công cụ sinh nhãn độ sâu và lịch trình huấn luyện được thiết lập cho phép đối sánh nội bộ; kết quả vì vậy được diễn giải theo giao thức phát triển đang xét.

Mô hình 3DDFA V2 ước lượng hình học khuôn mặt 3D từ ảnh 2D [2] và được chúng tôi sử dụng để sinh nhãn giả độ sâu ngoại tuyến trước khi huấn luyện. Trước đó, kiến trúc UCDCN cũng đã kết hợp mạng dự đoán độ sâu với bộ phân loại và áp dụng cơ chế giám sát tương tự cho mẫu thật/giả [3]. Do đó, bài báo này tập trung đánh giá có kiểm soát các phương án huấn luyện trên cùng kiến trúc CDCN. Ngoài ra, mạng MobileNetV3-Small [4] được dùng làm đối chứng RGB tham khảo, và hàm mất mát Focal [5] được sử dụng để giảm trọng số của các mẫu dễ đã phân loại với độ tự tin cao. UCDCN chưa được chạy làm đối chứng trực tiếp trong nghiên cứu này. Mã nguồn CDCN gốc [6] được dùng làm tham chiếu kiến trúc. CASO-PAD [7] kết hợp MobileNetV3 với toán tử không gian thích ứng theo nội dung, cung cấp bối cảnh cho các hướng PAD từ RGB một khung hình. Khác biệt backbone, dữ liệu và quy tắc đánh giá giới hạn phép đối chiếu trực tiếp giữa các công trình.

## 3 Phương pháp

### 3.1 Bản đồ độ sâu và nhánh phân loại

Mạng CDCN tiếp nhận ảnh RGB 256 × 256, sử dụng hệ số sai phân trung tâm θ = 0,7 và hợp nhất đặc trưng đa tỷ lệ để sinh bản đồ độ sâu một kênh kích thước 32 × 32. Cấu hình E1 lấy giá trị trung bình cộng toàn bản đồ làm điểm số người thật. Cấu hình E2 thay thế phép tính trung bình bằng hai lớp tích chập 1→8→16 kèm ReLU, gộp trung bình toàn cục (global average pooling) và lớp tuyến tính 16→1 với hàm Sigmoid ở đầu ra. Nhánh phân loại này bổ sung 1.265 tham số, nâng tổng số tham số từ 2.245.016 lên 2.246.281.

Cấu hình E2 khởi tạo bằng trọng số E1 được chọn trên tập kiểm định và cố định cả tham số mạng khung lẫn thống kê BatchNorm trong suốt quá trình huấn luyện. Do đó, E1 và E2 sử dụng cùng biểu diễn độ sâu, chỉ khác cơ chế trích xuất điểm phân loại. Điểm số video là trung bình điểm của 20 khung hình; giá trị cao hơn biểu thị dự đoán nghiêng về lớp người thật. Mô hình 3DDFA V2 và bản đồ độ sâu mục tiêu chỉ phục vụ giám sát khi huấn luyện, không tham gia suy luận PAD.

### 3.2 Hàm mất mát và lịch trình huấn luyện

Hàm mất mát độ sâu (depth loss) của Official CDCN là tổng sai số bình phương trung bình (MSE) toàn bản đồ và MSE tương phản của tám hướng sai phân lân cận (với trọng số đều bằng 1). Cấu hình E2 chỉ huấn luyện nhánh phân loại bằng hàm entropy chéo nhị phân (BCE). Trong khi đó, cấu hình E3 huấn luyện đồng thời cả mạng khung và nhánh phân loại với tổng hàm mất mát độ sâu và BCE (trọng số phân loại bằng 1).

Cấu hình E3b chia quá trình huấn luyện thành ba giai đoạn (stages): giai đoạn depth chỉ cập nhật mạng khung, giai đoạn head chỉ cập nhật nhánh phân loại, và giai đoạn joint tinh chỉnh đồng thời cả hai. Cấu hình E4 giữ nguyên lịch trình của E3b nhưng thay hàm BCE bằng hàm mất mát Focal (với α = 0,25 cho lớp người thật, 1 − α cho lớp tấn công và γ = 2). Ở đầu mỗi giai đoạn, bộ tối ưu hóa được khởi tạo lại và nạp lại trọng số tốt nhất của giai đoạn liền trước, giúp E3–E3b đánh giá toàn diện chiến lược phân tách giai đoạn.

## 4 Thiết lập thực nghiệm

### 4.1 Dữ liệu và nhãn giả độ sâu

Nghiên cứu sử dụng phiên bản khung hình CASIA-FASD từ Kaggle (immada/casia-fasd), với nhãn video được xác định theo quy ước của bộ dữ liệu gốc [8]. Dữ liệu gồm 50 chủ thể và 600 video người thật, ảnh in uốn cong, ảnh in cắt mắt và video phát lại. Các ảnh đã xử lý hậu kỳ mang tiền tố bs/fs được loại bỏ; chuỗi HR_1 được gán nhãn người thật. Mỗi video lấy cách đều 20 khung hình. Các chủ thể 4, 9, 14 và 19 được tách từ tập huấn luyện gốc để lập tập kiểm định; tập kiểm tra gồm 30 chủ thể còn lại. Chủ thể và video tách biệt giữa các phân tập.

Bảng 1 Thống kê dữ liệu theo từng phân tập

| Tập | Người | Video | Frame |
| --- | --- | --- | --- |
| Train | 16 | 192 | 3840 |
| Val | 4 | 48 | 960 |
| Test | 30 | 360 | 7200 |

Các phép đối sánh sử dụng giao thức phát triển nội bộ của CASIA-FASD, khác với giao thức đánh giá trong [1]. Tập kiểm tra đã được sử dụng qua nhiều vòng phát triển mô hình, nên kết quả phản ánh hiệu năng trên phân chia hiện tại thay vì khả năng tổng quát hóa trên một tập xác nhận độc lập mới.

Mô hình 3DDFA V2 sinh bản đồ giả độ sâu cho 3.000 khung hình người thật; 9.000 khung hình tấn công được gán bản đồ bằng không theo quy ước giám sát. Toàn bộ 12.000 bản đồ có giá trị hữu hạn; bản đồ người thật chứa giá trị khác không. Mỗi bản đồ được đổi kích thước về 32 × 32 và chia cho giá trị cực đại của chính nó khi cực đại đó lớn hơn 1. Ảnh RGB được chuẩn hóa với trung bình 0,5 và độ lệch chuẩn 128/255. Trong huấn luyện, phép lật ngang ngẫu nhiên xác suất 0,5 được áp dụng đồng bộ cho ảnh và bản đồ mục tiêu.

### 4.2 Cấu hình huấn luyện và lựa chọn mô hình

Cấu hình E0 sử dụng mạng MobileNetV3-Small với đầu vào 224 × 224 và chuẩn hóa ImageNet, trong khi các nhánh độ sâu sử dụng đầu vào 256 × 256. Các mô hình E0, E1 và E2 được huấn luyện lần lượt trong 5, 30 và 10 epoch (E2 dùng tốc độ học LR = 10⁻³). Ba nhánh E3, E3b và E4 cùng sử dụng bộ tối ưu hóa Adam, LR = 10⁻⁴, weight decay 10⁻⁴, kích thước lô bằng 8 và ngân sách 16 epoch, đồng thời khởi tạo từ cùng trọng số E1 (seed 42).

Bảng 2 Số chu kỳ huấn luyện và chu kỳ được chọn

| Model | Số chu kỳ | Loss | Best |
| --- | --- | --- | --- |
| E0 | 5 | BCE | 5 |
| E1 | 30 | Depth | 25 |
| E2 | 10 head | BCE | 1 |
| E3 | 16 joint | Depth+BCE | 10 |
| E3b | 4+4+8 | Depth+BCE | 10 |
| E4 | 4+4+8 | Depth+Focal | 14 |

Mô hình E1 lựa chọn trọng số (checkpoint) theo hàm mất mát độ sâu trên tập kiểm định. Cấu hình E2 cùng các giai đoạn head và joint của E3, E3b, E4 lựa chọn trọng số theo hàm mất mát phân loại BCE trên tập kiểm định (kể cả khi huấn luyện bằng Focal loss); riêng giai đoạn depth chọn theo hàm mất mát độ sâu. Với mỗi cấu hình, ngưỡng quyết định cấp độ video được xác lập trên tập kiểm định để tối thiểu hóa ACER (ưu tiên chênh lệch |APCER − BPCER| nhỏ hơn rồi ngưỡng nhỏ hơn nếu hòa).

Trên 48 video kiểm định, E3, E3b và E4 cùng đạt ACER = 0%, EER = 0% và AUC = 1. Quy tắc lựa chọn ưu tiên lần lượt ACER, EER, AUC và BCE; E3 được chọn do BCE thấp nhất, đạt 0,010902 so với 0,014566 của E3b và 0,087385 của E4. Trong đợt seed 42, các ngưỡng quyết định của E1, E2, E3, E3b và E4 lần lượt là 0,191604; 0,411779; 0,849619; 0,751813 và 0,418625. Trọng số và ngưỡng được xác lập trên tập kiểm định, sau đó áp dụng trực tiếp lên tập kiểm tra.

Các cấu hình E3, E3b và E4 được huấn luyện trên NVIDIA A100-SXM4-40GB với PyTorch 2.11.0+cu130; E1 được huấn luyện với cu128. Khác biệt môi trường thực thi giới hạn khả năng tách riêng ảnh hưởng của chiến lược huấn luyện. E2 và E3 còn khác số chu kỳ và tốc độ học, nên phép so sánh giữa chúng phản ánh tác động tổng hợp của các thiết lập này.

### 4.3 Chỉ số đánh giá

APCER là tỷ lệ video tấn công được phân loại nhầm thành người thật; BPCER là tỷ lệ video người thật bị từ chối sai; ACER là trung bình cộng của hai tỷ lệ này. APCER được tính gộp trên các loại tấn công trong dữ liệu. AUC đo năng lực xếp hạng phân tách hai lớp trên toàn bộ dải ngưỡng. EER được xấp xỉ bằng trung bình APCER và BPCER tại ngưỡng ứng viên rời rạc có độ chênh lệch tuyệt đối giữa hai tỷ lệ nhỏ nhất, thay vì nội suy liên tục. ACER trên tập kiểm tra được tính tại ngưỡng chọn từ tập kiểm định.


### 4.4 Thiết kế đánh giá bổ sung

Đợt lặp chỉ xét E1/E3 ở seed 43, 44 và 45 trên cùng split và nhãn. Mỗi E1 huấn luyện 30 epoch, chọn minimum validation depth loss; E3 khởi tạo từ E1 cùng seed và tinh chỉnh 16 epoch, chọn minimum validation BCE. Cả sáu lần dùng A100-SXM4-40GB, PyTorch 2.11.0+cu130, CUDA 13.0 và cuDNN 92700. E1 có weight decay 5×10⁻⁵, còn E3 là 10⁻⁴; LR 10⁻⁴ và batch 8 được giữ. Đây là phép so sánh cấu hình hoàn chỉnh, chưa cô lập riêng tác dụng head vì khác cả số epoch và weight decay. Seed 42 thuộc đợt khảo sát trước và được giữ riêng, không tham gia trung bình ba seed mới.

Mỗi lần có ngưỡng validation riêng. Trung bình và độ lệch chuẩn mẫu được tính qua ba seed với mẫu số n−1. Chênh lệch ACER E3 − E1 được tính trong từng seed trước khi tổng hợp. Ba lần đánh giá cùng 360 video không tạo thành 1.080 video độc lập. Nghiên cứu báo thống kê mô tả và không thực hiện kiểm định suy luận từ ba seed.

Chi phí E1/E3 seed 43 và E4 seed 42 được đo trong một phiên A100 riêng với float32, batch 1, RGB 256 × 256, hai tensor validation luân phiên. Sáu hoán vị thứ tự được sử dụng; mỗi lượt có 50 forward khởi động và 200 forward có đo, tổng 1.200 giá trị mỗi mô hình. Toàn bộ mẫu chậm được giữ. CUDA event đo forward GPU; host đo cùng forward có đồng bộ. Decode, chuẩn hóa, transfer, detector và crop nằm ngoài timing. Không autocast, TF32, compile hoặc CUDA Graph. p50/p95 dùng nội suy tuyến tính trên toàn bộ giá trị mỗi mô hình.

Phân tích lỗi đối chiếu video theo seed, nhãn và kết quả. Trong mỗi nhóm kết quả/loại tấn công, video đầu theo định danh được chọn trước khi xem RGB; khung hình thứ 11 trong 20 đại diện mỗi video. Có 20 trường hợp, là minh họa có chủ đích. Dự đoán CPU một khung hình được trình bày cùng quyết định video từ trung bình 20 điểm CUDA đã cố định.

Nguyên mẫu webcam đã đo dùng E3 seed 43 và ngưỡng validation 0,3983212910592556 trên Intel Core i5-7200U, hai thread CPU, PyTorch 2.11.0 CPU và webcam MSMF 640 × 480. Sau lượt thăm dò Haar, bốn lượt dùng YuNet 2023mar, confidence 0,5, OpenCV 4.14.0, trung vị 5 frame, gap 5 giây và IoU 0,4. Warm-up năm forward, năm settle read và chờ bắt đầu nằm ngoài timing. Tốc độ vòng lặp đếm mọi frame đọc được; tốc độ PAD đếm forward thật trong cùng thời lượng. TTD tính từ read-call đầu tiên của đoạn mặt hợp lệ đến quyết định đủ cửa sổ, gồm thời gian gom frame.

## 5 Kết quả

### 5.1 So sánh hiệu năng trên tập kiểm tra phát triển

Bảng 3 Kết quả trên video kiểm tra (tỷ lệ lỗi: %)

| Model | APCER | BPCER | ACER | EER | AUC |
| --- | --- | --- | --- | --- | --- |
| E0 | 0,0000 | 11,1111 | 5,5556 | 2,4074 | 0,997984 |
| E1 | 0,0000 | 5,5556 | 2,7778 | 2,2222 | 0,994444 |
| E2 | 0,0000 | 5,5556 | 2,7778 | 2,2222 | 0,994321 |
| E3 | 0,0000 | 10,0000 | 5,0000 | 2,2222 | 0,994198 |
| E3b | 0,0000 | 10,0000 | 5,0000 | 3,3333 | 0,992551 |
| E4 | 0,0000 | 8,8889 | 4,4444 | 2,2222 | 0,996626 |

Tập kiểm tra bao gồm 270 video tấn công và 90 video người thật. Tại ngưỡng quyết định từ tập kiểm định, mọi cấu hình đều đạt APCER = 0% trên mẫu quan sát. Về tỷ lệ từ chối sai người thật (BPCER), hai cấu hình E1 và E2 từ chối nhầm 5/90 video, E3 và E3b từ chối nhầm 9/90 video, còn E4 từ chối nhầm 8/90 video. So với mô hình đối chứng E1, chỉ số ACER của E3/E3b tăng thêm 2,2222 điểm phần trăm và E4 tăng thêm 1,6667 điểm phần trăm; các nhánh huấn luyện mới chưa cải thiện chỉ số đánh giá chính.

Mặc dù cấu hình E4 đạt chỉ số AUC là 0,996626 (cao hơn mức 0,994444 của E1), chỉ số ACER tại ngưỡng quyết định đã cố định lại cao hơn. Kết quả này phản ánh sự khác biệt giữa năng lực xếp hạng tổng thể qua toàn bộ dải ngưỡng và tỷ lệ lỗi thực tế tại một điểm vận hành cụ thể. Đối với mô hình tham khảo E0 trên ảnh RGB, do khác biệt về kiến trúc mạng, hàm mất mát, kích thước đầu vào và chuẩn hóa, phép so sánh E0–E1 chỉ mang tính tham chiếu tổng thể.

### 5.2 Đối chiếu kết quả trên từng video

Đối chiếu kết quả trên từng video tương ứng cho thấy E1 và E2 cùng phân loại đúng 355 video và từ chối sai cùng 5 video người thật. Nhánh phân loại thay đổi điểm số nhưng giữ nguyên quyết định sau ngưỡng. So với E1, E3 khắc phục 1 video lỗi và phát sinh 5 lỗi mới; E3b không khắc phục video lỗi nào và phát sinh 4 lỗi mới; E4 khắc phục 1 video lỗi và phát sinh 4 lỗi mới. E3 và E4 khắc phục video casia_s39_v1, trong khi cả ba cấu hình cùng phát sinh lỗi ở casia_s36_v2, s38_v2, s39_v2 và s48_v2; E3 có thêm lỗi ở casia_s32_v2.

E3 và E3b cùng đạt ACER 5,0000%, nhưng mỗi cấu hình khắc phục 1 video lỗi của cấu hình kia và đồng thời phát sinh 1 lỗi mới. So với E3b, E4 khắc phục 1 video người thật mà không phát sinh lỗi mới, giảm ACER 0,5556 điểm phần trăm ở seed này. Mỗi nhóm chất lượng có 30 video người thật; số lỗi trong nhóm chất lượng thấp của E1/E2, E3 và E3b/E4 lần lượt là 2, 7 và 6. Các nhãn chất lượng là siêu dữ liệu phân nhóm, chưa cung cấp phép đo trực tiếp về độ mờ hoặc ánh sáng để giải thích nguyên nhân lỗi.

### 5.3 Sai số bản đồ giả độ sâu trên tập kiểm định

Bảng 4 MAE độ sâu trên tập kiểm định

| Model | Attack full | Live full | Live mask |
| --- | --- | --- | --- |
| E3 | 0,01794 | 0,09843 | 0,11706 |
| E3b | 0,01665 | 0,10442 | 0,12409 |
| E4 | 0,00781 | 0,13076 | 0,15585 |

Chỉ số MAE được tính trên bản đồ mục tiêu đã chuẩn hóa mà không cắt ngưỡng dự đoán; mặt nạ vùng mặt thật (live mask) gồm các điểm ảnh có giá trị mục tiêu lớn hơn 10⁻⁶ (tổng cộng 203.982 điểm ảnh trên 240 khung hình người thật, bên cạnh 720 khung hình tấn công). Cấu hình E4 ép bản đồ dự đoán của mẫu tấn công về gần 0 tốt hơn nhưng lại có độ lệch lớn hơn trên vùng mặt thật so với E3 và E3b. Đại lượng MAE không thứ nguyên này phản ánh sự đánh đổi trong quá trình học biểu diễn ở tập kiểm định chứ không thay thế cho chỉ số ACER cấp độ video. MAE không có đơn vị centimet; chưa có MAE E1/E2 trong cùng phép đo để kết luận các nhánh mới giữ hình học tốt hơn đối chứng.



### 5.4 Độ ổn định trên ba seed mới

Bảng 5 Kết quả từng lần trên 360 video test với ngưỡng validation

| Mô hình | Seed | APCER % | BPCER % | ACER % | FA | FR |
| --- | --- | --- | --- | --- | --- | --- |
| E1 | 43 | 0,0000 | 13,3333 | 6,6667 | 0/270 | 12/90 |
| E3 | 43 | 0,0000 | 6,6667 | 3,3333 | 0/270 | 6/90 |
| E1 | 44 | 0,3704 | 4,4444 | 2,4074 | 1/270 | 4/90 |
| E3 | 44 | 0,0000 | 8,8889 | 4,4444 | 0/270 | 8/90 |
| E1 | 45 | 0,0000 | 7,7778 | 3,8889 | 0/270 | 7/90 |
| E3 | 45 | 0,0000 | 6,6667 | 3,3333 | 0/270 | 6/90 |

Bảng 6 Thống kê trung bình và độ lệch chuẩn mẫu qua seed 43 đến 45

| Chỉ số | E1 | E3 |
| --- | --- | --- |
| APCER (%) | 0,1235 ± 0,2138 | 0,0000 ± 0,0000 |
| BPCER (%) | 8,5185 ± 4,4905 | 7,4074 ± 1,2830 |
| ACER (%) | 4,3210 ± 2,1623 | 3,7037 ± 0,6415 |
| EER (%) | 2,5926 ± 0,6415 | 1,4815 ± 0,6415 |
| AUC | 0,993992 ± 0,000957 | 0,996269 ± 0,001654 |

Mỗi seed dùng cùng 270 video attack và 90 video live. E3 tốt hơn tại seed 43 và 45, nhưng kém hơn tại seed 44. Chênh lệch ACER E3 − E1 lần lượt là −3,3333; +2,0370; −0,5556 điểm phần trăm, tổng hợp thành −0,6173 ± 2,6857 điểm phần trăm. SD của chênh lệch lớn hơn độ lớn trung bình và chỉ có ba seed, nên giảm trung bình chưa chứng minh cải thiện ổn định. EER giảm và AUC tăng ở cả ba seed là quan sát bổ sung; ACER tại ngưỡng cố định vẫn là chỉ số chính.

Cả sáu validation có ACER/EER bằng 0 và AUC bằng 1 trên 48 video. Epoch chọn E1/E3 lần lượt là 29/15, 28/11 và 23/14 ở seed 43/44/45. Ở seed 43, ngưỡng E1 và E3 lần lượt là 0,265096 và 0,398321; ở seed 44 là 0,152037 và 0,432113; ở seed 45 là 0,239873 và 0,389849. Các giá trị ngưỡng được chọn riêng trước đánh giá test, không dùng chung vì thang điểm khác nhau.

### 5.5 Lỗi theo cặp và minh họa độ sâu

Bảng 7 Thay đổi quyết định E1 sang E3 trên từng seed

| Seed | Sửa lỗi E1 | Lỗi mới | Cùng sai | Cùng đúng |
| --- | --- | --- | --- | --- |
| 43 | 6 | 0 | 6 | 348 |
| 44 | 1 | 4 | 4 | 351 |
| 45 | 2 | 1 | 5 | 352 |

Ở seed 44, E3 sửa một video replay nhưng tạo bốn lỗi live mới; FA giảm từ 1 xuống 0 trong khi FR tăng từ 4 lên 8. Trong nhóm live quality=low gồm 30 video mỗi seed, số lỗi E1→E3 lần lượt là 9→4, 3→6 và 4→4. Quality là siêu dữ liệu, chưa trực tiếp đo độ mờ hoặc ánh sáng.

<!-- wide-start -->

![Hình 1 Trường hợp replay seed 44 được E3 sửa lỗi](assets/case_12_seed44_casia_s30_vHR_4.png)

![Hình 2 Trường hợp live seed 44 bị E3 từ chối trong khi E1 nhận đúng](assets/case_13_seed44_casia_s31_v1.png)

<!-- wide-end -->

Video replay casia_s30_vHR_4 có điểm E1 khoảng 0,1543 vượt ngưỡng 0,1520; E3 có điểm 0,0312 thấp hơn ngưỡng 0,4321 và sửa lỗi. Video live casia_s31_v1 thể hiện lỗi theo chiều ngược lại. Prediction có vùng giữa mặt thấp trong khi target phủ mặt đầy hơn; quan sát này chưa xác lập mô hình dựa vào nền hay viền.

Các panel dùng cùng thang depth [0,1] và absolute error [0;0,9920669794], thể hiện một frame thay vì mean map toàn video. Trong 40 forward CPU đã có, 20 điểm frame không đạt tolerance atol=10⁻⁵, rtol=10⁻⁴ so với CUDA, với max sai khác khoảng 0,000684. Nguyên nhân chưa xác định đầy đủ và trạng thái TF32 lịch sử chưa ghi đủ. Hình CPU chỉ minh họa, chưa tái lập chính xác score CUDA; mọi quyết định video và metric giữ kết quả CUDA đã cố định.

### 5.6 Chi phí forward trên A100

Bảng 8 Tham số và latency forward batch 1 trên A100

| Mô hình | Seed | Tham số | CUDA p50 ms | CUDA p95 ms | Host p50 ms | Host p95 ms |
| --- | --- | --- | --- | --- | --- | --- |
| E1 | 43 | 2245016 | 5,9167 | 5,9412 | 5,9438 | 5,9706 |
| E3 | 43 | 2246281 | 5,9638 | 5,9905 | 5,9913 | 6,0206 |
| E4 | 42 | 2246281 | 5,9617 | 5,9914 | 5,9894 | 6,0219 |

Nhánh E3 thêm 1.265 tham số (0,05635%); CUDA p50 tăng 0,047104 ms (0,7961%) và p95 tăng 0,049203 ms (0,8282%) so với E1. E3/E4 có cùng kiến trúc suy luận; chênh nhỏ giữa checkpoint chưa thể quy cho loss. Thời gian forward không gồm frontend nên không quy đổi thành FPS webcam. Phép đo giới hạn ở một phiên GPU, float32, batch 1 và hai input, không đại diện biến thiên giữa các thiết bị.

### 5.7 Webcam thăm dò và lỗi ngoài tập dữ liệu

Bảng 9 Timing trong các lượt webcam đã đo

| Lượt | Giây đo | Frame đọc/PAD | FPS vòng | Frame PAD/s | TTD giây |
| --- | --- | --- | --- | --- | --- |
| live-02 | 30,399 | 450/2 | 14,803 | 0,066 | Thiếu |
| live-03 | 45,224 | 738/12 | 16,319 | 0,265 | 10,378 |
| replay-01 | 46,338 | 108/26 | 2,331 | 0,561 | Thiếu |
| replay-02 | 45,594 | 34/28 | 0,746 | 0,614 | 7,407; 8,606 |
| live-reset-01 | 45,750 | 166/25 | 3,628 | 0,546 | 7,174 |

Live-03 đạt 16,319 FPS vòng nhưng chỉ 0,265 frame PAD/s vì nhiều frame không chạy model. Hai đầu ra đủ cửa sổ của live-03 và 17 đầu ra của live-reset đều là attack trong cảnh người vận hành khai báo live. Replay-02 có tám đầu ra đủ cửa sổ là attack; replay-01 tối đa 4/5 nên chưa quyết định. Các cửa sổ trong cùng clip phụ thuộc nhau; số ít clip và nhãn cảnh khai báo chưa hỗ trợ ước lượng ACER.

726 trạng thái no_face ở live-03 phản ánh thiếu detection; người vận hành xác nhận không chủ ý rời khung. Ở lượt reset riêng, buffer đã xóa khi rời vùng nhìn và gom lại khi quay về nhưng kết thúc ở 2/5, chưa có quyết định thứ hai. Print thật chưa được thử; ảnh trên màn hình không thay phép thử print. Ngưỡng PAD benchmark được giữ nguyên, và các lỗi live cho thấy nguyên mẫu chưa phù hợp xác thực thực tế.

## 6 Thảo luận và giới hạn

### 6.1 Đối chiếu với nghiên cứu liên quan

CDCN [1] (Bảng 4 của công trình) báo ACER 1,0% trên OULU-NPU P1, còn CDCN++ báo 0,2% với kiến trúc khác. UCDCN-L2 [3] (Bảng 5 của công trình) báo 0,9% trên P1/P2. CASO-PAD [7] (Bảng 5 và 8 của công trình) báo ACER 0,42% ở complete protocol nhưng 4,38% và 1,81% ở P1/P2, với một frame ngẫu nhiên/video và ngưỡng Youden trên dev. Những giao thức này khác trung bình 20 frame và tối thiểu ACER của nghiên cứu hiện tại; các số công bố không tạo bảng xếp hạng chung với CASIA development.

Ở phép thử chéo tập dữ liệu, CDCN báo HTER 32,6% từ Replay-Attack sang CASIA [1] (Bảng 7 của công trình); CASO-PAD báo HTER 21,67%, AUC 79,27% từ OULU/MSU/Replay sang CASIA [7] (Bảng 9 của công trình). Chúng là phép thử chuyển miền, khác cả chỉ số và dữ liệu huấn luyện. E1 kế thừa kiến trúc CDCN nhưng dùng pseudo-depth 3DDFA V2 và 30 epoch thay PRNet và ngân sách tối đa 1.300 epoch; đây chưa phải tái lập benchmark gốc. Một số quy tắc gộp video/ngưỡng của các bảng CDCN/UCDCN chưa được nguồn đã đọc xác định đầy đủ.

### 6.2 Ý nghĩa của kết quả bất lợi

E2 không thay đổi bất kỳ quyết định nào so với E1 ở seed 42, nên bổ sung nhánh phân loại trên biểu diễn cố định chưa giải quyết các lỗi đã quan sát. E3 thay đổi biểu diễn và hành vi theo seed; mức giảm ACER trung bình nhỏ đi kèm trường hợp kém hơn. AUC cải thiện không bảo đảm ACER tốt hơn ở ngưỡng validation, còn MAE pseudo-depth thấp hơn không tự bảo đảm lợi ích phân loại. Các lỗi webcam cho thấy cần đánh giá riêng chuyển miền và frontend trước khi dùng kết quả development cho nhận định triển khai.

### 6.3 Đe dọa đối với tính hợp lệ

E1/E3 khác ngân sách huấn luyện và weight decay nên chưa cô lập tác dụng head. Đối chứng loss và chiến lược E3/E3b/E4 mới có seed 42, còn thống kê ba seed chỉ thuộc cặp E1/E3. Validation có bốn người và 48 video, test development đã được quan sát nhiều vòng. Khóa ngưỡng trên validation không loại bỏ ảnh hưởng của quá trình phát triển đã biết test. Nghiên cứu chưa có tập xác nhận mới, đánh giá cross-dataset của các cấu hình nhóm hoặc thử mask 3D.

Pseudo-depth có sai số ước lượng; zero map attack là mục tiêu học, không phải độ sâu vật lý. Các case chọn có chủ đích và hình CPU chưa khớp CUDA theo tolerance ban đầu. Webcam dùng CPU, trung vị năm frame và ít cảnh khai báo, khác benchmark dùng trung bình 20 frame; detector bỏ lỡ mặt và các cửa sổ live đều bị từ chối. Print và chu trình quay lại đủ cửa sổ chưa hoàn tất. Nhận diện danh tính chưa được tích hợp. Bằng chứng hiện có chưa xác nhận hiệu quả bảo mật hoặc tốc độ thời gian thực của toàn hệ thống.

## 7 Kết luận

Nhánh phân loại đóng băng giữ nguyên ACER 2,7778% và năm lỗi của CDCN ở seed 42; các chiến lược tinh chỉnh chưa vượt đối chứng ở lần khảo sát này. Với ba seed mới, E3 đạt ACER trung bình 3,7037 ± 0,6415% so với 4,3210 ± 2,1623% của E1, nhưng chênh lệch ghép cặp −0,6173 ± 2,6857 điểm phần trăm và kết quả seed 44 chưa hỗ trợ cải thiện ổn định. Chi phí forward tăng nhỏ trong phép đo A100 đã thử, trong khi webcam bộc lộ lỗi từ chối live. Kết quả đóng góp bằng chứng thực nghiệm về các cấu hình cụ thể, gồm cả giới hạn và kết quả bất lợi; đánh giá ngang bằng budget/weight decay và dữ liệu độc lập là hướng tiếp theo.

# Tài liệu tham khảo

[1] Z. Yu et al., “Searching Central Difference Convolutional Networks for Face Anti-Spoofing,” Proc. IEEE/CVF CVPR, 2020, pp. 5295–5305. https://openaccess.thecvf.com/content_CVPR_2020/html/Yu_Searching_Central_Difference_Convolutional_Networks_for_Face_Anti-Spoofing_CVPR_2020_paper.html

[2] J. Guo, X. Zhu, Y. Yang, F. Yang, Z. Lei, and S. Z. Li, “Towards Fast, Accurate and Stable 3D Dense Face Alignment,” Proc. ECCV, 2020, pp. 152–168. https://arxiv.org/abs/2009.09960

[3] J. Zhang et al., “UCDCN: a nested architecture based on central difference convolution for face anti-spoofing,” Complex & Intelligent Systems, vol. 10, pp. 4817–4833, 2024. DOI: 10.1007/s40747-024-01397-0.

[4] A. Howard et al., “Searching for MobileNetV3,” Proc. IEEE/CVF ICCV, 2019, pp. 1314–1324. https://openaccess.thecvf.com/content_ICCV_2019/html/Howard_Searching_for_MobileNetV3_ICCV_2019_paper.html

[5] T.-Y. Lin, P. Goyal, R. Girshick, K. He, and P. Dollár, “Focal Loss for Dense Object Detection,” Proc. IEEE ICCV, 2017, pp. 2980–2988. https://openaccess.thecvf.com/content_iccv_2017/html/Lin_Focal_Loss_for_ICCV_2017_paper.html

[6] Z. Yu et al., “CDCN,” mã nguồn tham chiếu của công trình CVPR 2020. https://github.com/ZitongYu/CDCN

[7] S. Khan, “Face presentation attack detection via content-adaptive spatial operators,” Scientific Reports, Article in Press, 2026. DOI: 10.1038/s41598-026-67944-6.

[8] Z. Zhang, J. Yan, S. Liu, Z. Lei, D. Yi, and S. Z. Li, “A Face Antispoofing Database with Diverse Attacks,” Proc. ICB, 2012, pp. 26–31. DOI: 10.1109/ICB.2012.6199754.
