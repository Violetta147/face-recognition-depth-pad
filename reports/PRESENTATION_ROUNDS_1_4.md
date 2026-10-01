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

## Dựng lại và trạng thái kiểm tra

Builder: `scripts/build_rounds1_4_presentation.mjs`, dùng `@oai/artifact-tool`.
Cần runtime do `load_workspace_dependencies` trả về và skill Presentations.
Đặt `SKILL_DIR`, `RUNTIME_NODE_MODULES`, `RUNTIME_PYTHON` theo máy hiện tại;
copy builder vào `artifacts/.build-report-20261002/build.mjs` và tạo junction
`node_modules` trong thư mục build tới `RUNTIME_NODE_MODULES`, rồi chạy Node
từ repository root. Tham số tùy chọn: root tuyệt đối và tên PPTX mới.
Finalizer không ghi đè file hoặc receipt đã tồn tại; muốn dựng lại hãy dùng tên mới.

Output giao: `artifacts/presentations/DeepFace_PAD_Bao_cao_03-10-2026.pptx`
và `artifacts/presentations/Loi_thuyet_trinh_Luot_1_4.md`.
PPTX có 22 trang, 9 bảng native, sơ đồ chính native và 22 trang Notes.
Hình notebook và sơ đồ gốc là PNG; không dựng lại các curve từ dữ liệu suy đoán.

Kiểm tra ngày 02/10/2026:

- `python -m pytest -q tests/test_presentation_evidence.py`: **3 passed**.
  Test thứ ba kiểm tra PPTX thực: tác giả, AUC, video lỗi, Notes và bảng editable;
  tự skip nếu máy khác không có artifact biometric được Git ignore.
- Finalizer: package và geometry không có findings; font Arial; import lại đủ
  22 slide; 9 bảng native. Receipt nằm trong thư mục build riêng.
- Import chính PPTX cuối, render lại đủ 22 slide và đọc toàn bộ bản render.
  Sửa mũi tên để luồng model đi từ RGB sang output trước khi giao.
- Lệnh authoring kết thúc với exit code 1 nhưng không có exception sau khi
  in đường dẫn final; không dùng exit code này làm bằng chứng PASS. Receipt,
  test nội dung artifact và lệnh import/render độc lập (exit 0) là bằng chứng
  kiểm tra ở trên.

SHA-256 PPTX cuối:
`11c4a6145f78499351197b584f8dde7aca3b5c873004ea4095f2cbc2486bea0b`.
