# Chuyển skill sang agent khác

Thư mục nguồn tên `marp_slides_tutorial` theo yêu cầu; tên khai báo là `marp-slides-tutorial`.

Nếu agent hỗ trợ Agent Skills, chép toàn bộ thư mục vào thư mục skills mà agent đó nhận diện và đặt tên thư mục đích `marp-slides-tutorial`. Với Codex, có thể đặt trong thư mục skills của cấu hình Codex cá nhân. Kiểm tra tài liệu agent/phiên bản để chọn vị trí discovery; đừng chỉ chép SKILL.md vì còn references và assets.

Nếu agent không tự nhận skill, gửi toàn bộ thư mục hoặc ZIP và dùng lời nhắc:

> Đọc SKILL.md trong thư mục marp_slides_tutorial và các hướng dẫn được liên kết để sửa deck Markdown này cho Marp Slides trong Obsidian. Giữ chỉnh sửa hiện có và kiểm tra bản render trước khi kết luận.

Skill cung cấp chỉ dẫn và ví dụ, không kèm Obsidian, Marp CLI, quyền UI hay cấu hình tài khoản. Không cần dữ liệu ASR hoặc asset DUT của project gốc.

Mở `assets/example.md` bằng Marp Slides hoặc Marp for VS Code. Nếu đã có Marp CLI, từ thư mục skill có thể chạy:

```shell
marp assets/example.md -o example.html
```

Điều chỉnh lệnh gọi CLI theo môi trường. Mẫu không cần tải ảnh hoặc theme; các số liệu đều là minh họa.
