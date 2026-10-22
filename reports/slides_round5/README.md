# Báo cáo thực nghiệm DeepFace-PAD bằng Marp

Nguồn chỉnh sửa: `Bao_cao_DeepFace_PAD.md`. Deck gồm 18 trang chính và 4 trang
phụ lục, cập nhật tới 16/10/2026, E0–E4 trên CASIA development protocol, seed 42.
Không dùng số liệu pilot để thay Official E1; không chọn lại model/ngưỡng từ test.

## Mở và xuất

Mở Markdown bằng Marp Slides trong Obsidian (lệnh **Marp Slides: Slide Preview**)
hoặc Marp for VS Code. Deck dùng Markdown thuần cho nội dung, không cần bật
HTML parsing. Giữ thư mục `assets/` cạnh file Markdown. CSS nằm trong frontmatter.

HTML cạnh Markdown, PDF và PPTX trong `exports/` là bản xuất. PPTX Marp dùng ảnh cho từng slide;
chỉnh nội dung bằng Markdown rồi xuất lại. Ghi chú thuyết trình nằm trong comment
Markdown và speaker notes của bản PPTX. CLI đã kiểm tra bố cục; chưa xác nhận
trong UI Marp Slides/Obsidian của người dùng.

Chuẩn bị asset từ các artifact cục bộ đã kiểm chứng:

```powershell
python scripts/prepare_marp_report.py
powershell -NoProfile -File scripts/export_dut_backgrounds.ps1
```

Lệnh thứ hai cần PowerPoint trên Windows. Script tạo bản sao template, bỏ chữ
mẫu, giữ artwork nền/master, xuất trang 1/6/15 thành cover/content/closing.
Template gốc không thay đổi. Font nội dung Arial có dấu tiếng Việt; font UTM
Neutra của mẫu chưa có trên máy. Ảnh khoa học được chép nguyên byte, không crop,
đổi màu, thay tương phản hoặc dựng lại dữ liệu. File `assets/provenance.json`
ghi nguồn và SHA-256. Asset chứa ảnh CASIA nên không đưa vào Git công khai.

Xuất với Marp CLI 4.5.1 (đã dùng khi kiểm tra):

```powershell
node artifacts/marp-report-20261016/tooling/node_modules/@marp-team/marp-cli/marp-cli.js --allow-local-files reports/slides_round5/Bao_cao_DeepFace_PAD.md -o reports/slides_round5/Bao_cao_DeepFace_PAD.html
# Thêm --pdf hoặc --pptx để xuất định dạng tương ứng.
```

Hoặc dùng `powershell -NoProfile -File scripts/render_marp_report.ps1` để xuất
cả ba định dạng. HTML nằm cạnh `assets/` để đường dẫn ảnh hoạt động khi chuyển
thư mục sang máy khác.

## Bằng chứng

- `reports/ROUND_5_TEST_RESULTS_2026-10-16.json`: metric và lỗi ghép cặp E0–E4.
- `reports/ROUND_5_FULL_VALIDATION_2026-10-16.json`: chọn E3 trước test và MAE validation.
- `artifacts/figure-notebook-20261016/numeric-final/`: hình, CSV, caption và provenance.
- `artifacts/figure-notebook-20261016/qualitative-preview/`: ảnh thực casia_s32_v2,
  inference CPU từ checkpoint đã khóa, score kiểm tra khớp CSV trong 0,001.

Giới hạn phải giữ khi sửa: một seed; test phát triển đã quan sát qua nhiều lượt;
pseudo-depth không phải đo cảm biến; ảnh một frame không đại diện toàn split;
không có kết quả nhiều seed, webcam hay latency GPU mới. Hai sơ đồ kiến trúc
trong `diagrams/` là minh họa do người dùng cung cấp, không phải ảnh thí nghiệm.

Kiểm tra nguồn: `python -m unittest discover -s tests -p test_marp_report.py`.
