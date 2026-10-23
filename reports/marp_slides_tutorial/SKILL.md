---
name: marp-slides-tutorial
description: Create, edit and troubleshoot Markdown presentations rendered with Marp, especially Marp Slides in Obsidian. Use for slide layout, images, backgrounds, themes and export; distinguish Marp from Obsidian core Slides.
---

# Marp Slides Tutorial

Tạo slide từ Markdown, giữ nguồn chỉnh sửa được và kiểm tra bằng đúng trình render người dùng chọn. Skill không phụ thuộc project PBL6 hoặc đường dẫn cá nhân.

## Cách làm

- Đọc Markdown và cấu hình hiện có trước khi sửa. Giữ chỉnh sửa của người dùng, sao lưu trước thay đổi lớn. Không tự đổi công cụ hoặc tạo thêm bản deck.
- Đọc [hướng dẫn](references/tutorial.md) cho cú pháp, ảnh, nền và xuất. Marp Slides và core Slides của Obsidian là hai renderer khác nhau.
- Nếu preview sai, đọc [xử lý lỗi](references/troubleshooting.md). Kiểm tra file và đường dẫn trước khi kết luận do cache.
- Dùng [mẫu Markdown](assets/example.md) khi cần deck mới; CSS nằm trong frontmatter, không cần theme cài riêng.
- Slide học thuật tiếng Việt cần câu ngắn, rõ, có bài toán, phương pháp, kết quả và hướng tiếp theo. Chỉ ghi số liệu có nguồn, kèm đơn vị, số mẫu và phạm vi đo. Phân biệt tập con được chọn với toàn bộ split dataset.
- Khi mô tả hành động của người trình bày, dùng “nhóm” hoặc “nhóm chúng em” và nêu mục đích. Việc chưa chốt dùng “nhóm dự định…”. Khi nêu giới hạn, viết cụ thể “Nhóm mới kiểm tra X, chứ chưa đánh giá Y”; không tự thêm phản đề vào mọi câu.
- Nội dung chiếu dành cho người nghe báo cáo, không phải cuộc trao đổi hỗ trợ với người dùng. Đưa chi tiết code/tra cứu vào ghi chú, trừ khi mục đích buổi trình bày là giải thích code.
- Render và xem trang đã sửa; kiểm tra chữ tràn, ảnh thiếu và vùng logo/footer. Kiểm tra CLI không chứng minh giao diện plugin đã đúng. Nói rõ đã kiểm tra file, bản render hay UI thực tế.
- Giữ Markdown và các asset liên quan khi chuyển deck. HTML/PDF/PPTX là bản xuất; kiểm tra lại sau khi thay nguồn.

## Chuyển sang agent khác

Đọc [PORTING.md](PORTING.md). Skill không tự cấp công cụ, quyền sửa cấu hình hoặc đồng bộ tài khoản; thực hiện trong phạm vi người dùng yêu cầu.
