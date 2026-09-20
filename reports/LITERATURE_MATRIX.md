# Literature matrix cho Lượt 1

Ma trận này định vị baseline và hướng cải tiến. Cột **mức so sánh** chỉ được đổi thành
"trực tiếp" khi dataset, protocol, split, đơn vị frame/video và cách chọn threshold
đều tương thích với thí nghiệm của nhóm.

| Công trình | Năm | Supervision / cơ chế | Output hoặc scoring | Vai trò trong dự án | Mức so sánh hiện tại |
|---|---:|---|---|---|---|
| [CDCN](https://openaccess.thecvf.com/content_CVPR_2020/html/Yu_Searching_Central_Difference_Convolutional_Networks_for_Face_Anti-Spoofing_CVPR_2020_paper.html) | 2020 | Central difference convolution, depth supervision | Predicted depth, mean-depth score | Baseline E1 | Contextual cho tới khi dùng đúng official protocol |
| [Deep Spatial Gradient and Temporal Depth](https://openaccess.thecvf.com/content_CVPR_2020/html/Wang_Deep_Spatial_Gradient_and_Temporal_Depth_Learning_for_Face_Anti-Spoofing_CVPR_2020_paper.html) | 2020 | Spatial gradient và temporal depth | Pixel/depth cues theo không gian-thời gian | Bằng chứng cho depth supervision | Contextual |
| [DC-CDN](https://www.ijcai.org/proceedings/2021/177) | 2021 | Static-dynamic central difference | Spatial-temporal PAD representation | Hướng mở rộng CDC, không nằm trong lõi hai người | Contextual |
| [UCDCN](https://link.springer.com/article/10.1007/s40747-024-01397-0) | 2024 | Nested CDC, depth regression, classifier, Focal Loss và staged training | Depth + classification | Gần nhất về kỹ thuật với learned depth head | Contextual; chỉ trực tiếp trên protocol tương thích |
| [CASO-PAD](https://www.nature.com/articles/s41598-026-67944-6) | 2026 | MobileNetV3 và content-adaptive spatial operator | Binary PAD score | Bối cảnh mô hình nhẹ mới | Contextual |

## Kết luận dùng cho thiết kế thí nghiệm

- E0 kiểm tra binary MobileNetV3 và nguy cơ học shortcut.
- E1 tái lập CDCN depth-only với mean-depth score.
- E2 cô lập đúng một thay đổi chính: learned classifier đọc predicted depth.
- E3 và E4 lần lượt kiểm tra joint training và staged/Focal; không dùng để thay đổi câu hỏi nghiên cứu.
- CASIA-FASD hiện chỉ là dữ liệu phát triển giữa kỳ, vì vậy không dùng số CASIA để tuyên bố vượt paper trên OULU-NPU, Replay-Attack hoặc protocol khác.
