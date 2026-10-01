# Bộ slide báo cáo Lượt 1–4

Nội dung chốt ngày 02/10/2026, phục vụ báo cáo dự kiến 03/10/2026.

## Luồng trình bày

15 slide chính, khoảng 13–15 phút: bài toán và câu hỏi → hướng tiếp cận và paper
liên quan → protocol → pseudo-depth → E0/E1/E2 → kết quả → lỗi và chi phí → giới
hạn, kế hoạch và kết luận. Bảy slide phụ lục để trả lời câu hỏi, gồm ba sơ đồ gốc
người dùng cung cấp. E0 là baseline tham khảo; E1–E2 là phép so sánh chính.

Nội dung và lời nói từng slide nằm trong `rounds1_4_presentation_content.json`.
Số liệu được đọc từ output notebook E0, Official E1 và E2 hiện có, đối chiếu với
các báo cáo CASIA đã lưu. Các notebook có output của người dùng được giữ nguyên.
Không xem bản notebook clean không output là bằng chứng một run đã hoàn tất.

## Sử dụng hình và sơ đồ

- Dùng ảnh validation RGB/target/mask/prediction và biểu đồ từ output notebook.
- Không thay ảnh minh họa trong sơ đồ kiến trúc thành bằng chứng thực nghiệm.
- Sơ đồ MobileNetV3 tổng quát có output softmax; slide chú thích E0 thực tế là
  một logit + sigmoid và BCEWithLogits.
- Colorbar 0–1 ở sơ đồ CDCN chỉ minh họa; predicted depth qua ReLU không bị
  chặn cứng tại 1. Resize hai nhánh về 32×32 là giảm kích thước không gian.
- Chưa có ảnh RGB/depth của năm video test cùng sai; không dùng ảnh validation
  thay cho chúng. Phần phân tích lỗi chính dùng bảng video thật và giả thuyết
  được nêu rõ. Không bắt buộc bổ sung hình này để báo cáo kết quả hiện tại.

## Giới hạn kết luận

E1 tái lập topology/loss CDCN trong protocol nhóm. E2 frozen head chưa cải thiện
ACER so với E1 trong run seed 42. Không tuyên bố tái lập số paper, đạt SOTA,
novelty cho ý tưởng chung learned head, hay E2 nhanh hơn từ một phép đo sơ bộ.
CASIA test đã quan sát; benchmark độc lập và nhiều seed vẫn cần. E3/E4 chưa có
kết quả benchmark.

## Artifact và kiểm chứng

PPTX và các hình có biometric pixels được xuất vào `artifacts/presentations/`,
đã được Git ignore; không commit ảnh khuôn mặt, notebook có output hoặc weights.
Nguồn nội dung không có pixel và test kiểm tra metric/count/chi phí được commit.
Kiểm tra package, text geometry, editable tables, notes và render từng slide trước
khi giao. Việc render không có nghĩa là đã mở thử trong PowerPoint.
