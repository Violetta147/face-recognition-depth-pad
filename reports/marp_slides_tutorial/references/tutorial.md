# Marp trong Obsidian

## Mở đúng renderer

Marp Slides là community plugin. Mở note, Ctrl+P → **Marp Slides: Slide Preview**. **Slides: Start presentation** thuộc core Slides của Obsidian; nó không áp dụng theme/directive Marp theo cùng cách.

## Markdown cơ bản

```markdown
---
marp: true
theme: default
size: 16:9
paginate: true
---

# Tên đề tài

Nhóm thực hiện và người hướng dẫn.

---

## Kết quả

Một kết quả chính, có đơn vị và nguồn.
```

Khối đầu là frontmatter cấu hình. Dòng `---` ngoài frontmatter, có dòng trống hai bên, chia trang. Ghi chú đặt trong comment `<!-- ... -->` để không hiện trên trang.

## Chèn ảnh

Marp dùng Markdown chuẩn, không dùng wikilink `![[anh.png]]`:

```markdown
![width:800px](<figures/ket qua.png>)
```

Đường dẫn tương đối tính từ file Markdown. Nếu ảnh cùng thư mục, chỉ ghi tên ảnh; `../` đi lên một thư mục. Dấu `<...>` bao đường dẫn có khoảng trắng. Marp đọc `width`/`height` trong phần alt để đặt kích thước. Khi chuyển deck, giữ nguyên cây thư mục ảnh.

## Nền thật

Ảnh trong nội dung khác với ảnh nền. Đặt nền bằng:

```markdown
![bg cover](figures/background.png)
```

Hoặc directive riêng cho một trang:

```markdown
<!-- _backgroundImage: url("themes/cover.png") -->
<!-- _backgroundSize: cover -->
```

Đặt `backgroundImage: url("themes/content.png")` trong frontmatter để áp dụng nền mặc định. Dùng URL ngoặc kép giúp tương thích với ca lỗi đường dẫn đã quan sát ở plugin 0.46.1. Giữ đủ tương phản và khoảng trống cho logo/footer. Asset nền vẫn phải đi cùng deck.

## CSS, HTML và MarkdownIt

`style: |` trong frontmatter tùy chỉnh CSS trực tiếp. **Theme Path** dành cho theme CSS bên ngoài; không cần cài thêm theme để chèn ảnh/nền. Theme ngoài cần tên khai báo `/* @theme ten-theme */`, frontmatter dùng `theme: ten-theme`; xem quy tắc đường dẫn của plugin đang dùng.

**Enable HTML** cho phép thẻ HTML trong Markdown; không cần nếu chỉ dùng Markdown/directive. Xuất HTML là việc khác với bật HTML parsing. **MarkdownIt Plugins** bổ sung cú pháp mở rộng ở phiên bản hỗ trợ; không tự thay theme, cũng không cần cho ảnh/bảng/nền chuẩn. Với sơ đồ, có thể render thành SVG để giảm phụ thuộc extension; giữ nguồn sơ đồ để sửa sau.

## Công thức

Marp hỗ trợ công thức toán. Ví dụ:

```markdown
$$
\mathrm{RTF}=\frac{\text{Thời gian xử lý}}{\text{Thời lượng audio}}
$$
```

Kiểm tra engine toán của renderer, dấu tiếng Việt và bố cục ở bản xuất; preview plugin và CLI có thể khác cấu hình.

## Xuất và trình chiếu

Ctrl+P → lệnh Marp Slides Export HTML/PDF/PPTX. PDF/PPTX/ảnh thường cần browser Chromium phù hợp; xem lỗi thực tế và cấu hình đường dẫn browser.

Marp HTML có thể dùng template `bespoke` với điều khiển trình chiếu/presenter view hoặc `bare` tối giản. Kiểm tra `marp --help` hay HTML Export Mode của plugin; không khẳng định mọi HTML đều có presenter view. Trình duyệt có thể chặn cửa sổ presenter nếu popup bị chặn.

PPTX thông thường giữ hình thức bằng ảnh từng trang, không bảo đảm sửa từng chữ. Một số CLI có tùy chọn editable thử nghiệm; cần kiểm tra lại bố cục. Khi nhập vào slide nhóm, chọn giữ hình thức hoặc dựng lại thành phần theo nhu cầu chỉnh sửa của nhóm.

## Nguồn

- [Marpit image syntax](https://marpit.marp.app/image-syntax): ảnh, kích thước và nền.
- [Marp CLI](https://github.com/marp-team/marp-cli): xuất và template HTML.
- [Marp Slides for Obsidian](https://github.com/samuele-cozzi/obsidian-marp-slides): preview/export/theme; không hỗ trợ wikilink.
- [Obsidian core Slides](https://obsidian.md/help/plugins/slides): Start presentation và ngắt trang.

Đối chiếu nguồn phần mềm ngày 15/10/2026. Ca thực tế của project dùng Marp Slides 0.46.1, Obsidian 1.14.4 và Marp CLI 4.5.1; đây không phải yêu cầu phiên bản bắt buộc của skill.
