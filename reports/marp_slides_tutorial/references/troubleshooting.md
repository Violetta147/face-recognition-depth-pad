# Chẩn đoán lỗi hiển thị

## Ảnh hiện thành chữ hoặc bị thiếu

Đọc dòng Markdown thật. Kiểm tra ảnh tồn tại đúng vị trí tương đối so với note, tên/đuôi và khoảng trắng. Với Marp, dùng Markdown chuẩn thay wikilink và `<...>` khi đường dẫn có khoảng trắng. Đừng thêm `../` khi chưa tìm thấy ảnh. Render lại và kiểm tra ảnh tải được, không chỉ cú pháp hợp lệ.

## Nền mất nhưng chữ vẫn hiện

Kiểm tra đúng renderer, directive, file nền và đường dẫn. Plugin Marp Slides 0.46.1 trong ca đã kiểm tra chỉ viết lại đường dẫn background-image khớp `url("...")`; đổi ngoặc đơn sang ngoặc kép đã giải quyết và được người dùng xác nhận. Đây là hành vi phụ thuộc phiên bản, không phải quy tắc chung của CSS. Với phiên bản khác, kiểm tra code/log/tài liệu tương ứng.

Core Slides không đọc theme Marp. Nếu người dùng yêu cầu nền cho core Slides, cần CSS/theme tương ứng; ảnh inline không phải nền. Không tự tạo thêm bản core Slides khi người dùng chỉ yêu cầu Marp.

## Preview khác ảnh mở riêng

Không kết luận ngay là cache. Kiểm tra Markdown trỏ đến ảnh nào, có bản trùng tên không, thời điểm tạo asset và bản xuất. Đối chiếu nội dung SVG/PNG thật với ảnh preview. Có thể thử bản sao asset tên mới và đổi link để phân biệt cache với nguồn cũ; giữ bản gốc. Với SVG, nếu vẫn lỗi thì kiểm tra ID/CSS và cách plugin nhúng ảnh.

Đóng/mở preview hoặc reload chỉ là thử nghiệm. Nếu vẫn lỗi, tiếp tục xác định nguyên nhân; đừng lặp lời khuyên khởi động lại hoặc nói đã sửa khi chưa có bằng chứng.

## HTML bị in nguyên văn

Kiểm tra Enable HTML của plugin hoặc cờ HTML của CLI. Ưu tiên Markdown nếu đủ dùng. Không yêu cầu bật HTML để sửa sai đường dẫn ảnh.

## Chữ tràn hoặc bị cắt

Kiểm tra tỉ lệ, font, padding, chiều cao bảng/ảnh và vùng footer. Giảm nội dung hoặc chia trang trước khi giảm chữ hàng loạt. Mỗi trang có một thông điệp; chi tiết code và giải thích hỗ trợ dài đưa vào ghi chú/tài liệu tra cứu.

## Bằng chứng sau sửa

Ghi rõ đã kiểm tra file/link, render CLI hay quan sát đúng plugin. Xem trang sửa ở kích thước trình chiếu; kiểm tra fence/số trang không thay thế kiểm tra bố cục. Khi không truy cập được UI, nhờ người dùng xác nhận sau khi đã kiểm tra phần có thể làm.
