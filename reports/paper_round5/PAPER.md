<!-- title_vi -->
# Đánh giá thực nghiệm bộ phân loại bản đồ độ sâu và chiến lược huấn luyện CDCN trên CASIA-FASD

<!-- title_en -->
An Empirical Evaluation of Depth-Map Classifiers and CDCN Training Strategies on CASIA-FASD

<!-- authors -->
Trịnh Minh Đạt, Nguyễn Hữu Minh Quân

Trường Đại học Bách khoa, Đại học Đà Nẵng, Việt Nam

<!-- abstract_vi -->
## Tóm tắt

Nghiên cứu đánh giá nhánh phân loại học sâu trên bản đồ độ sâu cho bài toán chống giả mạo khuôn mặt. Trên CASIA-FASD, chúng tôi đối sánh CDCN tính điểm bằng trung bình không gian với nhánh phân loại dưới bốn thiết lập: đóng băng mạng khung, huấn luyện đồng thời với BCE, huấn luyện theo giai đoạn với BCE và huấn luyện theo giai đoạn với Focal. Dữ liệu gồm 600 video, trích xuất 20 khung hình mỗi video và phân chia độc lập theo chủ thể. Trọng số và ngưỡng quyết định được chọn trên tập kiểm định. Với seed 42, CDCN đối chứng và nhánh đóng băng cùng đạt ACER 2,7778% trên 360 video kiểm tra; hai cấu hình BCE còn lại đạt 5,0000%, còn Focal đạt 4,4444%. Nhánh đóng băng không khắc phục được 5 video lỗi của đối chứng; Focal khắc phục 1 video lỗi so với BCE theo giai đoạn nhưng chưa vượt đối chứng. Các kết quả giới hạn ở một seed và giao thức phát triển nội bộ, chưa xác nhận khả năng tổng quát hóa độc lập.

Từ khóa: chống giả mạo khuôn mặt; CDCN; pseudo-depth; bộ phân loại độ sâu; nghiên cứu thực nghiệm.

<!-- abstract_en -->
## Abstract

This study evaluates learned depth-map classification for face presentation attack detection. On a fixed CASIA-FASD development split, spatial-mean CDCN scoring is compared with a classification head under four settings: frozen-backbone training, joint BCE, staged BCE, and staged Focal training. The dataset comprises 600 videos with 20 uniformly sampled frames per video and subject-disjoint splits. Model weights and decision thresholds are selected on validation. With seed 42, the baseline and frozen-backbone classifier achieve 2.7778% ACER on 360 test videos, versus 5.0000% for joint and staged BCE and 4.4444% for staged Focal. The frozen classifier corrects none of the five baseline errors; Focal corrects one staged-BCE error but remains worse than the baseline. These single-seed results do not establish improved ACER or independent generalization.

Keywords: face anti-spoofing; CDCN; pseudo-depth; depth-map classifier; empirical evaluation.

<!-- pipeline -->

<!-- body -->
## 1 Giới thiệu

Phát hiện tấn công trình diện (Presentation Attack Detection – PAD), còn gọi là chống giả mạo khuôn mặt, phân biệt khuôn mặt người thật với các phương tiện giả mạo như ảnh in hoặc video phát lại. Tác vụ này khác với nhận diện danh tính. Giám sát bằng bản đồ độ sâu cung cấp mục tiêu học tại từng điểm ảnh từ đầu vào RGB. Hiệu quả của biểu diễn này phụ thuộc cả kiến trúc dự đoán độ sâu, cơ chế trích xuất điểm phân loại và chiến lược huấn luyện.

Mạng tích chập sai phân trung tâm (Central Difference Convolutional Network – CDCN) kết hợp thông tin cường độ và chênh lệch cục bộ để dự đoán bản đồ độ sâu [1]. Đối chứng E1 tính điểm người thật bằng trung bình không gian của bản đồ. Phép tính này không phân biệt vị trí của các giá trị độ sâu. Nghiên cứu kiểm tra liệu nhánh phân loại được huấn luyện trên cùng bản đồ có giảm tỷ lệ lỗi hay không, sau đó đánh giá ảnh hưởng của huấn luyện đồng thời, huấn luyện theo giai đoạn và hàm mất mát phân loại.

Nghiên cứu cung cấp phép đối sánh giữa trung bình không gian và nhánh phân loại học sâu trên cùng mạng khung CDCN, cùng các đối chứng về chiến lược huấn luyện và hàm mất mát. Phân tích kết hợp chỉ số phân loại cấp video, thay đổi quyết định trên từng video tương ứng và sai số bản đồ giả độ sâu (pseudo-depth). Phạm vi đóng góp là đánh giá thực nghiệm các thiết lập trên kiến trúc có sẵn trong giao thức phát triển CASIA-FASD.

## 2 Nghiên cứu liên quan

Kiến trúc CDCN và biến thể CDCN++ được giới thiệu trong [1]. Nghiên cứu này sử dụng CDCN tiêu chuẩn làm mạng khung dự đoán độ sâu. Quy trình phân chia dữ liệu, công cụ sinh nhãn độ sâu và lịch trình huấn luyện được thiết lập cho phép đối sánh nội bộ; kết quả vì vậy được diễn giải theo giao thức phát triển đang xét.

Mô hình 3DDFA V2 ước lượng hình học khuôn mặt 3D từ ảnh 2D [2] và được chúng tôi sử dụng để sinh nhãn giả độ sâu ngoại tuyến trước khi huấn luyện. Trước đó, kiến trúc UCDCN cũng đã kết hợp mạng dự đoán độ sâu với bộ phân loại và áp dụng cơ chế giám sát tương tự cho mẫu thật/giả [3]. Do đó, bài báo này tập trung đánh giá có kiểm soát các phương án huấn luyện trên cùng kiến trúc CDCN. Ngoài ra, mạng MobileNetV3-Small [4] được dùng làm đối chứng RGB tham khảo, và hàm mất mát Focal [5] được sử dụng để giảm trọng số của các mẫu dễ đã phân loại với độ tự tin cao. UCDCN chưa được chạy làm đối chứng trực tiếp trong nghiên cứu này.

## 3 Phương pháp

### 3.1 Bản đồ độ sâu và nhánh phân loại

Mạng CDCN tiếp nhận ảnh RGB 256 × 256, sử dụng hệ số sai phân trung tâm θ = 0,7 và hợp nhất đặc trưng đa tỷ lệ để sinh bản đồ độ sâu một kênh kích thước 32 × 32. Cấu hình E1 lấy giá trị trung bình cộng toàn bản đồ làm điểm số người thật. Cấu hình E2 thay thế phép tính trung bình bằng hai lớp tích chập 1→8→16 kèm ReLU, gộp trung bình toàn cục (global average pooling) và lớp tuyến tính 16→1 với hàm Sigmoid ở đầu ra. Nhánh phân loại này bổ sung 1.265 tham số, nâng tổng số tham số từ 2.245.016 lên 2.246.281.

Cấu hình E2 khởi tạo bằng trọng số E1 được chọn trên tập kiểm định và cố định cả tham số mạng khung lẫn thống kê BatchNorm trong suốt quá trình huấn luyện. Do đó, E1 và E2 sử dụng cùng biểu diễn độ sâu, chỉ khác cơ chế trích xuất điểm phân loại. Điểm số video là trung bình điểm của 20 khung hình; giá trị cao hơn biểu thị dự đoán nghiêng về lớp người thật. Mô hình 3DDFA V2 và bản đồ độ sâu mục tiêu chỉ phục vụ giám sát khi huấn luyện, không tham gia suy luận PAD.

### 3.2 Hàm mất mát và lịch trình huấn luyện

Hàm mất mát độ sâu (depth loss) của Official CDCN là tổng sai số bình phương trung bình (MSE) toàn bản đồ và MSE tương phản của tám hướng sai phân lân cận (với trọng số đều bằng 1). Cấu hình E2 chỉ huấn luyện nhánh phân loại bằng hàm entropy chéo nhị phân (BCE). Trong khi đó, cấu hình E3 huấn luyện đồng thời cả mạng khung và nhánh phân loại với tổng hàm mất mát độ sâu và BCE (trọng số phân loại bằng 1).

Cấu hình E3b chia quá trình huấn luyện thành ba giai đoạn (stages): giai đoạn depth chỉ cập nhật mạng khung, giai đoạn head chỉ cập nhật nhánh phân loại, và giai đoạn joint tinh chỉnh đồng thời cả hai. Cấu hình E4 giữ nguyên lịch trình của E3b nhưng thay hàm BCE bằng hàm mất mát Focal (với α = 0,25 cho lớp người thật, 1 − α cho lớp tấn công và γ = 2). Ở đầu mỗi giai đoạn, bộ tối ưu hóa được khởi tạo lại và nạp lại trọng số tốt nhất của giai đoạn liền trước, giúp E3–E3b đánh giá toàn diện chiến lược phân tách giai đoạn.

## 4 Thiết lập thực nghiệm

### 4.1 Dữ liệu và nhãn giả độ sâu

Nghiên cứu sử dụng phiên bản khung hình CASIA-FASD từ Kaggle (immada/casia-fasd), với nhãn video được xác định theo quy ước của bộ dữ liệu gốc [6]. Dữ liệu gồm 50 chủ thể và 600 video người thật, ảnh in uốn cong, ảnh in cắt mắt và video phát lại. Các ảnh đã xử lý hậu kỳ mang tiền tố bs/fs được loại bỏ; chuỗi HR_1 được gán nhãn người thật. Mỗi video lấy cách đều 20 khung hình. Các chủ thể 4, 9, 14 và 19 được tách từ tập huấn luyện gốc để lập tập kiểm định; tập kiểm tra gồm 30 chủ thể còn lại. Chủ thể và video tách biệt giữa các phân tập.

<!-- table:split -->

Các phép đối sánh sử dụng giao thức phát triển nội bộ của CASIA-FASD, khác với giao thức đánh giá trong [1]. Tập kiểm tra đã được sử dụng qua nhiều vòng phát triển mô hình, nên kết quả phản ánh hiệu năng trên phân chia hiện tại thay vì khả năng tổng quát hóa trên một tập xác nhận độc lập mới.

Mô hình 3DDFA V2 sinh bản đồ giả độ sâu cho 3.000 khung hình người thật; 9.000 khung hình tấn công được gán bản đồ bằng không theo quy ước giám sát. Toàn bộ 12.000 bản đồ có giá trị hữu hạn; bản đồ người thật chứa giá trị khác không. Mỗi bản đồ được đổi kích thước về 32 × 32 và chia cho giá trị cực đại của chính nó khi cực đại đó lớn hơn 1. Ảnh RGB được chuẩn hóa với trung bình 0,5 và độ lệch chuẩn 128/255. Trong huấn luyện, phép lật ngang ngẫu nhiên xác suất 0,5 được áp dụng đồng bộ cho ảnh và bản đồ mục tiêu.

### 4.2 Cấu hình huấn luyện và lựa chọn mô hình

Cấu hình E0 sử dụng mạng MobileNetV3-Small với đầu vào 224 × 224 và chuẩn hóa ImageNet, trong khi các nhánh độ sâu sử dụng đầu vào 256 × 256. Các mô hình E0, E1 và E2 được huấn luyện lần lượt trong 5, 30 và 10 epoch (E2 dùng tốc độ học LR = 10⁻³). Ba nhánh E3, E3b và E4 cùng sử dụng bộ tối ưu hóa Adam, LR = 10⁻⁴, weight decay 10⁻⁴, kích thước lô bằng 8 và ngân sách 16 epoch, đồng thời khởi tạo từ cùng trọng số E1 (seed 42).

<!-- table:schedule -->

Mô hình E1 lựa chọn trọng số (checkpoint) theo hàm mất mát độ sâu trên tập kiểm định. Cấu hình E2 cùng các giai đoạn head và joint của E3, E3b, E4 lựa chọn trọng số theo hàm mất mát phân loại BCE trên tập kiểm định (kể cả khi huấn luyện bằng Focal loss); riêng giai đoạn depth chọn theo hàm mất mát độ sâu. Với mỗi cấu hình, ngưỡng quyết định cấp độ video được xác lập trên tập kiểm định để tối thiểu hóa ACER (ưu tiên chênh lệch |APCER − BPCER| nhỏ hơn rồi ngưỡng nhỏ hơn nếu hòa).

Trên 48 video kiểm định, E3, E3b và E4 cùng đạt ACER = 0%, EER = 0% và AUC = 1. Quy tắc lựa chọn ưu tiên lần lượt ACER, EER, AUC và BCE; E3 được chọn do BCE thấp nhất, đạt 0,010902 so với 0,014566 của E3b và 0,087385 của E4. Các ngưỡng quyết định của E1, E2, E3, E3b và E4 lần lượt là 0,191604; 0,411779; 0,849619; 0,751813 và 0,418625. Trọng số và ngưỡng được xác lập trên tập kiểm định, sau đó áp dụng trực tiếp lên tập kiểm tra.

Các cấu hình E3, E3b và E4 được huấn luyện trên NVIDIA A100-SXM4-40GB với PyTorch 2.11.0+cu130; E1 được huấn luyện với cu128. Khác biệt môi trường thực thi giới hạn khả năng tách riêng ảnh hưởng của chiến lược huấn luyện. E2 và E3 còn khác số chu kỳ và tốc độ học, nên phép so sánh giữa chúng phản ánh tác động tổng hợp của các thiết lập này.

### 4.3 Chỉ số đánh giá

APCER là tỷ lệ video tấn công được phân loại nhầm thành người thật; BPCER là tỷ lệ video người thật bị từ chối sai; ACER là trung bình cộng của hai tỷ lệ này. APCER được tính gộp trên các loại tấn công trong dữ liệu. AUC đo năng lực xếp hạng phân tách hai lớp trên toàn bộ dải ngưỡng. EER được xấp xỉ bằng trung bình APCER và BPCER tại ngưỡng ứng viên rời rạc có độ chênh lệch tuyệt đối giữa hai tỷ lệ nhỏ nhất, thay vì nội suy liên tục. ACER trên tập kiểm tra được tính tại ngưỡng chọn từ tập kiểm định.


## 5 Kết quả và thảo luận

### 5.1 So sánh hiệu năng trên tập kiểm tra phát triển

<!-- table:results -->

Tập kiểm tra bao gồm 270 video tấn công và 90 video người thật. Tại ngưỡng quyết định từ tập kiểm định, mọi cấu hình đều đạt APCER = 0% trên mẫu quan sát. Về tỷ lệ từ chối sai người thật (BPCER), hai cấu hình E1 và E2 từ chối nhầm 5/90 video, E3 và E3b từ chối nhầm 9/90 video, còn E4 từ chối nhầm 8/90 video. So với mô hình đối chứng E1, chỉ số ACER của E3/E3b tăng thêm 2,2222 điểm phần trăm và E4 tăng thêm 1,6667 điểm phần trăm; các nhánh huấn luyện mới chưa cải thiện chỉ số đánh giá chính.

Mặc dù cấu hình E4 đạt chỉ số AUC là 0,996626 (cao hơn mức 0,994444 của E1), chỉ số ACER tại ngưỡng quyết định đã cố định lại cao hơn. Kết quả này phản ánh sự khác biệt giữa năng lực xếp hạng tổng thể qua toàn bộ dải ngưỡng và tỷ lệ lỗi thực tế tại một điểm vận hành cụ thể. Đối với mô hình tham khảo E0 trên ảnh RGB, do khác biệt về kiến trúc mạng, hàm mất mát, kích thước đầu vào và chuẩn hóa, phép so sánh E0–E1 chỉ mang tính tham chiếu tổng thể.

### 5.2 Đối chiếu kết quả trên từng video

Đối chiếu kết quả trên từng video tương ứng cho thấy E1 và E2 cùng phân loại đúng 355 video và từ chối sai cùng 5 video người thật. Nhánh phân loại thay đổi điểm số nhưng giữ nguyên quyết định sau ngưỡng. So với E1, E3 khắc phục 1 video lỗi và phát sinh 5 lỗi mới; E3b không khắc phục video lỗi nào và phát sinh 4 lỗi mới; E4 khắc phục 1 video lỗi và phát sinh 4 lỗi mới. E3 và E4 khắc phục video casia_s39_v1, trong khi cả ba cấu hình cùng phát sinh lỗi ở casia_s36_v2, s38_v2, s39_v2 và s48_v2; E3 có thêm lỗi ở casia_s32_v2.

E3 và E3b cùng đạt ACER 5,0000%, nhưng mỗi cấu hình khắc phục 1 video lỗi của cấu hình kia và đồng thời phát sinh 1 lỗi mới. So với E3b, E4 khắc phục 1 video người thật mà không phát sinh lỗi mới, giảm ACER 0,5556 điểm phần trăm ở seed này. Mỗi nhóm chất lượng có 30 video người thật; số lỗi trong nhóm chất lượng thấp của E1/E2, E3 và E3b/E4 lần lượt là 2, 7 và 6. Các nhãn chất lượng là siêu dữ liệu phân nhóm, chưa cung cấp phép đo trực tiếp về độ mờ hoặc ánh sáng để giải thích nguyên nhân lỗi.

### 5.3 Sai số bản đồ giả độ sâu trên tập kiểm định

<!-- table:depth -->

Chỉ số MAE được tính trên bản đồ mục tiêu đã chuẩn hóa mà không cắt ngưỡng dự đoán; mặt nạ vùng mặt thật (live mask) gồm các điểm ảnh có giá trị mục tiêu lớn hơn 10⁻⁶ (tổng cộng 203.982 điểm ảnh trên 240 khung hình người thật, bên cạnh 720 khung hình tấn công). Cấu hình E4 ép bản đồ dự đoán của mẫu tấn công về gần 0 tốt hơn nhưng lại có độ lệch lớn hơn trên vùng mặt thật so với E3 và E3b. Đại lượng MAE không thứ nguyên này phản ánh sự đánh đổi trong quá trình học biểu diễn ở tập kiểm định chứ không thay thế cho chỉ số ACER cấp độ video. MAE không có đơn vị centimet; chưa có MAE E1/E2 trong cùng phép đo để kết luận các nhánh mới giữ hình học tốt hơn đối chứng.

### 5.4 Giới hạn của nghiên cứu

Thứ nhất, nghiên cứu hiện tại mới thực hiện trên một hạt giống ngẫu nhiên (seed 42), do đó chưa có giá trị trung bình, độ lệch chuẩn qua nhiều lần chạy hay kiểm định thống kê cho các mức chênh lệch nhỏ. Thứ hai, tập kiểm định có quy mô nhỏ (4 chủ thể với 48 video) nên việc đạt ACER = 0% trên tập kiểm định chưa bảo đảm khả năng tổng quát hóa, đồng thời sự khác biệt về môi trường CUDA ở mô hình E1 cũng đặt ra giới hạn nhất định khi diễn giải nhân quả.

Về mặt dữ liệu và triển khai, nhãn giả độ sâu có thể tồn tại sai số hình học và bản đồ không cho mẫu tấn công chỉ là quy ước giám sát. Chúng tôi chưa đánh giá mô hình trên các loại tấn công nằm ngoài tập dữ liệu hiện có, chưa kiểm thử chéo giữa các bộ dữ liệu độc lập (cross-dataset) cũng như chưa đo đạc độ trễ toàn trình trên luồng camera thực tế kèm nhận diện danh tính. Chưa có phép đo độ trễ đồng điều kiện cho mọi cấu hình; số tham số không đủ để kết luận tốc độ thực tế.

## 6 Kết luận

Trên giao thức phát triển CASIA-FASD với hạt giống ngẫu nhiên 42, bộ phân loại với mạng khung cố định chưa cải thiện được mức ACER 2,7778% và không khắc phục được 5 lỗi của phương pháp lấy trung bình bản đồ độ sâu. Chiến lược huấn luyện đồng thời và theo giai đoạn với hàm BCE dẫn đến ACER 5,0000%; cấu hình Focal theo giai đoạn đạt 4,4444%, có cải thiện nhẹ so với BCE theo giai đoạn nhưng vẫn chưa vượt qua E1/E2. Do đó, các kết quả thực nghiệm trong lần chạy này chưa ủng hộ giả thuyết cải thiện chỉ số ACER bằng nhánh phân loại học sâu.

Hướng nghiên cứu tiếp theo là đánh giá độ ổn định của cặp E1 và E3 trên nhiều seed trong cùng môi trường, đồng thời đo chi phí tính toán và mở rộng đánh giá sang dữ liệu độc lập. E3 tiếp tục là cấu hình đại diện theo tiêu chí lựa chọn trên tập kiểm định; kết quả của E4 trên tập kiểm tra được sử dụng để phân tích đối sánh.

## Tài liệu tham khảo

[1] Z. Yu et al., “Searching Central Difference Convolutional Networks for Face Anti-Spoofing,” in Proc. IEEE/CVF CVPR, 2020, pp. 5295–5305.

[2] J. Guo, X. Zhu, Y. Yang, F. Yang, Z. Lei, and S. Z. Li, “Towards Fast, Accurate and Stable 3D Dense Face Alignment,” in Proc. ECCV, 2020, pp. 152–168.

[3] J. Zhang et al., “UCDCN: a nested architecture based on central difference convolution for face anti-spoofing,” Complex & Intelligent Systems, vol. 10, pp. 4817–4833, 2024, doi: 10.1007/s40747-024-01397-0.

[4] A. Howard et al., “Searching for MobileNetV3,” in Proc. IEEE/CVF ICCV, 2019, pp. 1314–1324.

[5] T.-Y. Lin, P. Goyal, R. Girshick, K. He, and P. Dollár, “Focal Loss for Dense Object Detection,” in Proc. IEEE ICCV, 2017, pp. 2980–2988.

[6] Z. Zhang, J. Yan, S. Liu, Z. Lei, D. Yi, and S. Z. Li, “A Face Antispoofing Database with Diverse Attacks,” in Proc. ICB, 2012, pp. 26–31, doi: 10.1109/ICB.2012.6199754.

<!-- appendix -->
## English tables and figure


<!-- table:split_en -->

<!-- table:schedule_en -->

<!-- table:results_en -->

<!-- table:depth_en -->

<!-- pipeline_en -->
