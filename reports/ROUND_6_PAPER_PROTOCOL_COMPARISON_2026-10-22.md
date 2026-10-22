# Lượt 6: đối chiếu phương pháp và protocol paper

Cập nhật 22/10/2026. Chỉ E1 và E3 của nhóm dùng cùng phép thử CASIA đã khóa,
nên chỉ cặp này cho phép đo mức thay đổi trực tiếp. Các kết quả công bố dưới
đây cung cấp bối cảnh; không tạo bảng xếp hạng chung với CASIA của nhóm.
Bản Word và paper lịch sử được giữ nguyên. Nguồn máy đọc và SHA-256 PDF:
`ROUND_6_PAPER_PROTOCOL_COMPARISON_2026-10-22.json`.

## Phép so sánh trực tiếp của nhóm

CASIA-FASD/CASIA-MFSD: 600 video, chia theo người 16 train / 4 validation /
30 test; 20 frame/video. Test có 360 video, gồm 270 attack và 90 live. Một
score video là trung bình score frame. Threshold chọn riêng trên validation:
minimum ACER, rồi minimum |APCER − BPCER|, rồi threshold nhỏ hơn. Sáu model
và threshold đã khóa trước khi mở test của đợt; ba seed 43/44/45 giữ đầy đủ.

| Model | Video test ACER, mean ± sample SD | EER, mean ± sample SD | AUC mean ± sample SD |
| --- | ---: | ---: | ---: |
| E1, Official CDCN architecture, depth-only | 4,3210 ± 2,1623% | 2,5926 ± 0,6415% | 0,993992 ± 0,000957 |
| E3, cùng backbone + learned depth head, joint BCE | 3,7037 ± 0,6415% | 1,4815 ± 0,6415% | 0,996269 ± 0,001654 |

SD tính với ddof=1; AUC không đơn vị. Paired delta E3 − E1 = −0,6173 ±
2,6857 điểm phần trăm. E3 tốt hơn ở 2/3 seed, kém hơn seed 44; chưa chứng
minh cải thiện ổn định. Chi tiết: [báo cáo kết quả](ROUND_6_RESULTS_2026-10-22.md).

E1 là baseline dùng kiến trúc Official CDCN trong pipeline của nhóm. Không
gọi đây là tái lập đầy đủ benchmark paper: split, pseudo-depth và ngân sách
train khác. E3 là ứng viên đã chọn trước test; không có bằng chứng rằng đây
là cải tiến tốt nhất có thể đạt được.

## Các số công bố và điều kiện đi kèm

Các error rate trong bảng đều là %. Không đổi HTER thành ACER. AUC có ký
hiệu % được giữ nguyên đơn vị công bố. P1/P2 là protocol 1/2, không phải seed.
Ký hiệu “chưa xác minh” là giới hạn của nguồn đã đọc, không khẳng định tác giả
không có quy tắc đó.

| Nguồn / model | Dataset và phép thử | Split / đơn vị / threshold | Kết quả công bố | Vị trí nguồn |
| --- | --- | --- | --- | --- |
| CDCN | OULU-NPU P1, intra-dataset | Official protocol; aggregation và cách chọn threshold chưa xác minh trong mục 4.1–4.2 | APCER 0,4; BPCER 1,7; ACER 1,0 | [CDCN 2020](https://openaccess.thecvf.com/content_CVPR_2020/papers/Yu_Searching_Central_Difference_Convolutional_Networks_for_Face_Anti-Spoofing_CVPR_2020_paper.pdf), Table 4; local preprint PDF tr.7 |
| CDCN++ | OULU-NPU P1 | Cùng protocol công bố; khác kiến trúc CDCN | APCER 0,4; BPCER 0,0; ACER 0,2 | Cùng nguồn, Table 4 |
| CDCN | Replay-Attack → CASIA-MFSD | Cross-dataset; train Replay, test CASIA; threshold/aggregation chưa xác minh | HTER 32,6 | Cùng nguồn, Table 7; local PDF tr.8 |
| UCDCN-L2 | OULU-NPU P1 / P2 | Official protocols; train/dev/test theo Table 9; video aggregation và threshold Table 5 chưa xác minh | P1 ACER 0,9; P2 ACER 0,9 | [UCDCN 2024](https://link.springer.com/article/10.1007/s40747-024-01397-0), Table 5, PDF tr.9 / journal tr.4825 |
| UCDCN, Linear head | OULU-NPU, toàn train/test | Có thống kê ảnh ở Table 4; aggregation chưa xác minh; threshold 0,5 chỉ được nêu cho Table 7 | ACER 1,82 | Cùng nguồn, Table 7, PDF tr.10 và phần giải thích tr.11 |
| CASO-PAD | OULU-NPU, complete protocol | 20/15/20 người; mỗi video một frame ngẫu nhiên, không gộp; Youden trên dev rồi khóa test | APCER 0,00; BPCER 0,83; ACER 0,42 | [CASO-PAD 2026](https://www.nature.com/articles/s41598-026-67944-6), Table 5, PDF tr.14; cách đánh giá tr.9–11 |
| CASO-PAD | OULU-NPU P1 / P2 | Protocol riêng; quy tắc một frame/video và threshold như trên | P1 ACER 4,38; P2 ACER 1,81 | Cùng nguồn, Table 8, PDF tr.16 |
| CASO-PAD | O&M&I → C | Cross-dataset: train OULU/MSU/Replay, target CASIA chưa thấy khi train; phần chọn dev cho cross-domain chưa mô tả đủ để tái lập | HTER 21,67; AUC 79,27% | Cùng nguồn, Table 9, PDF tr.17 |

CDCN dùng PRNet và tối đa 1.300 epoch trong phần implementation; nhóm dùng
cache 3DDFA và 30 epoch E1. Không gán ACER 0,2 của CDCN++ cho E1. Các số
cross-dataset không phải CASIA intra-dataset. [CDCN, mục 4.2](https://arxiv.org/abs/2003.04092)

UCDCN dùng UNet++/CDC, head học từ depth, input 128² và lịch train nhiều
giai đoạn. Đây là tham khảo kỹ thuật gần; E3 không tái tạo backbone đó.
Không gán threshold 0,5 cho Table 5. Công bố 653 fps trên RTX 3090 không
cùng phép đo batch-1 A100 của nhóm; đơn vị “flops” trong bài chưa đủ rõ để
chép thành GFLOPs. [UCDCN, Implementation và Comparison](https://link.springer.com/article/10.1007/s40747-024-01397-0)

CASO-PAD bản Article in Press đã đọc: MobileNetV3 + involution; Table 13
ghi 3,635M params, 0,256 GFLOPs ở 256². Setup dùng RTX 5080, test batch 256.
Không dùng các số đó làm latency A100 batch 1. Không thay ACER complete
protocol bằng ACER P1/P2 hoặc gộp ba phép thử. [CASO-PAD, PDF nhà xuất bản](https://www.nature.com/articles/s41598-026-67944-6_reference.pdf)

## Cách dùng trong báo cáo tiếp theo

Trình bày kết quả ba seed của nhóm thành bảng chính, kèm paired delta và
seed 44. Đặt bảng paper thành bối cảnh có protocol; không kết luận nhóm
thắng/thua từ các con số không cùng phép thử. Muốn so sánh trực tiếp với
paper cần một đợt đăng ký riêng theo đúng dataset, partition, preprocessing,
đơn vị gộp và threshold; không điều chỉnh Lượt 6 đã mở test.

Số tham số/checkpoint đã kiểm nằm ở `ROUND_6_COST_STATIC_2026-10-22.json`;
[latency A100 mới đã kiểm toán](ROUND_6_COST_RESULTS_2026-10-22.md) theo
[kế hoạch chi phí](ROUND_6_COST_PLAN.md). Không có FPS webcam mới. Phân tích
ảnh lỗi và demo webcam thuộc Lượt 7, không ghi thành kết quả đã hoàn tất ở đây.
