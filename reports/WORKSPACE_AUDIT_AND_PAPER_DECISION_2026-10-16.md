# Rà soát không gian dự án và quyết định làm bài báo

Kiểm kê ngày 16/10/2026, trước khi tạo tài liệu mới. **Không xóa, di chuyển hoặc
đổi tên file nào.** Đây là đề xuất để người dùng sắp xếp, không phải lệnh dọn.

## Kết luận cần dùng ngay

Giữ `reports/bao_cao_cuoi_ky`. Nó là khung báo cáo cuối kỳ và kho tham chiếu,
không phải bài báo. Tạo bài báo riêng ở `reports/paper_round5`, dùng kết quả
E0–E4 đã hoàn tất. Khi quay lại final report, cập nhật khung hiện có theo
bằng chứng mới và xuất một tên bản hoàn chỉnh khác, giữ bản trước cập nhật.

Khung Markdown còn khoảng **128 đoạn hướng dẫn/placeholder** theo mẫu tìm kiếm;
Word hiện không có hình thực nghiệm. Các con số này không đo chất lượng viết,
nhưng xác nhận không thể nộp nguyên khung. Tên đề tài đăng ký có nhận diện và
thời gian thực, trong khi phần đã đo hiện tập trung vào PAD. Không tự viết các
thành phần chưa triển khai thành kết quả đã hoàn thành.

## Phạm vi kiểm kê

- 20.539 file ngoài `.git`, tổng 948,83 MiB; gồm cả dependency và cache.
- 135 đường dẫn được Git quản lý ở thời điểm kiểm kê.
- CSV đủ từng đường dẫn, byte, đề xuất và lý do:
  `artifacts/workspace-audit-20261016/inventory.csv`.
- Danh sách 187 nhóm trùng byte SHA-256, chỉ so các file trên 4 KiB ngoài
  dependency: `artifacts/workspace-audit-20261016/duplicates.json`.
- Đã đọc sâu kế hoạch, khung/nguồn báo cáo, các audit, config CASIA E3–E4,
  code đọc dữ liệu/loss/training/metric và nguồn của các hình. Không đọc tay
  từng file thư viện trong hơn 19 nghìn file dependency/cache.
- Kiểm kê này ở checkout cục bộ; không có nghĩa đã kiểm kê mọi byte trên Drive
  hoặc mọi thư mục cá nhân ngoài dự án.

## Các file và thư mục có thể gom hoặc bỏ bản tạo lại

Đường dẫn tính từ gốc DeepFace-PAD. MiB là 1.048.576 byte. Các dòng dưới có
thể lồng nhau, không cộng các dung lượng trùng nhau.

| Đường dẫn | Dung lượng gần đúng | Đề xuất | Lý do và điều kiện |
|---|---:|---|---|
| `artifacts/.build-report-20261002/node_modules/` | 326,58 MiB | Có thể gỡ dependency cục bộ | Dependency dựng slide cũ, không phải kết quả thí nghiệm. Giữ script và thông tin package để cài lại. |
| `artifacts/marp-report-20261016/tooling/` | 102,18 MiB | Giữ khi còn xuất Marp; có thể gỡ sau | Renderer Marp đang được `scripts/render_marp_report.ps1` tham chiếu. Gỡ sẽ phải cài lại trước khi dùng lệnh đó. |
| Các `__pycache__/` trong `src/`, `scripts/`, `tests/` | nhỏ | Có thể xóa cache | Python tự tạo lại; không chứa mô hình hoặc dữ liệu nguồn. |
| `artifacts/.build-report-20261002/slide-*.png`, `final-*.png`, `contact-*.png` | nằm trong phần build còn lại khoảng 17,56 MiB | Lưu trữ hoặc bỏ render cũ | Ảnh kiểm tra deck lượt 1–4. Giữ deck cuối ở `artifacts/presentations/` và script nguồn. |
| `artifacts/.build-report-20261002/candidate.pptx` | 4,77 MiB | Có thể bỏ bản build trùng | SHA-256 trùng deck cuối và bản tham khảo trong báo cáo. Không bỏ mọi bản. |
| `artifacts/marp-report-20261016/template-preview/` | 5,07 MiB | Có thể tạo lại | Preview 15 trang template. Nền đang dùng nằm trong `reports/slides_round5/assets/`. |
| `artifacts/marp-report-20261016/rendered/` | 4,74 MiB | Có thể bỏ render cũ | Render trước sửa bố cục, không phải bản nộp. |
| `artifacts/marp-report-20261016/rendered-final/` | 4,72 MiB | Lưu một bộ QA hoặc tạo lại | Ảnh kiểm tra bản trước các chỉnh sửa nội dung tiếp theo. |
| `artifacts/marp-report-20261016/pptx-preview/` | 1,12 MiB | Có thể tạo lại | Ảnh mở PowerPoint kiểm tra, không phải source. |
| `artifacts/marp-report-20261016/contact-*.png`, `final-contact-*.png`, `template-contact.png`, `figure-contact.png` | vài MiB | Có thể bỏ ảnh tổng quan cũ | Chỉ phục vụ kiểm tra bố cục. |
| `artifacts/marp-report-20261016/DUT-backgrounds-only.pptx` | 3,61 MiB | Có thể tạo lại | Bản trung gian tách nền; giữ template gốc và ba PNG nền đang dùng. |
| `artifacts/marp-report-20261016/DeepFace_PAD_Slides_DUT.zip` | 25,12 MiB | Đánh dấu gói cũ/lưu trữ | Gói tạo trước lần bỏ HTML và trước chỉnh sửa nội dung của người dùng; không lấy nó làm bản mới nhất. |
| `artifacts/marp-report-html-fix/` | 5,25 MiB | Lưu backup nguồn, có thể bỏ preview | Ảnh trước/sau sửa HTML. Giữ `Bao_cao_DeepFace_PAD.before.md` nếu cần phục hồi bản người dùng. |
| `artifacts/final-report-scaffold-qa/` | 3,67 MiB | Có thể tạo lại render | Kiểm tra khung 18 trang, không phải báo cáo hoàn chỉnh. |
| `artifacts/final-report-block1-qa/` | 4,86 MiB | Giữ `backups/`; có thể bỏ ảnh render | Backup Word có giá trị phục hồi; không coi cả thư mục là rác. |
| `artifacts/word-format-audit/` | 4,91 MiB | Lưu trữ hoặc tạo lại | Artifact kiểm tra định dạng Word cũ. |
| `reports/slides_round5/Bao_cao_DeepFace_PAD.pptx` | xem CSV | Giữ làm bản trước sửa, không dùng nộp | Đã xác nhận bản tự xuất từng hiện nguyên thẻ HTML. Bản sửa ở `exports/Bao_cao_DeepFace_PAD_Khong_HTML.pptx`. |
| [Briefing cũ](archive/briefings/face-pad-core-briefing.pptx) | 0,02 MiB | Đã chuyển vào lịch sử ngày 21/10 | Trước ở `reports/face-pad-core-briefing.pptx`; giữ nguyên byte. |
| [Tài liệu CDCN](../references/papers/2003.04092v1.pdf) và `reports/bao_cao_cuoi_ky/nguon/tai_lieu/CDCN_2020.pdf` | 4,62 MiB mỗi bản | Đã chuyển bản ở root vào references ngày 21/10 | Giữ cả bản tham chiếu lịch sử; không xóa bản nào. |
| `reports/Template-DUT-Total.pptx` và bản trong `bao_cao_cuoi_ky/tham_khao/` | 3,77 MiB mỗi bản | Có thể giảm bản sao sau khi sửa link | Trùng hash; template gốc vẫn là nguồn dựng nền slide. |
| `reports/bao_cao_cuoi_ky/nguon/notebooks/` | có E1 khoảng 2,09 MiB | Chỉ lưu snapshot lịch sử | E1 trùng notebook gốc tại thời điểm kiểm kê. E2 có thể cũ so với notebook người dùng đã sửa; không ghi đè nguồn mới bằng bản sao. |
| `reports/bao_cao_cuoi_ky/nguon/bao_cao/`, `cau_hinh/`, `tai_lieu/` | thuộc 7,15 MiB bản sao nguồn | Gom snapshot theo ngày nếu muốn | Tài liệu sao chép để đọc một chỗ; một số trạng thái E3/E4/Drive đã cũ. Giữ `NGUON_CUC_BO.json` và đối chiếu hash. |
| `reports/bao_cao_cuoi_ky/hinh_anh/so_do/` | khoảng 4,49 MiB | Có thể giảm bản sao, cần sửa link | Trùng ba ảnh trong `diagrams/`; slide có asset riêng để chuyển máy. |
| `configs/e0_mobilenet.yaml`, `e1_cdcn.yaml`, `e2_head_frozen.yaml`, `e3_joint_bce.yaml`, `e4_staged_focal.yaml` | rất nhỏ | Có thể gom vào mẫu lịch sử khi sửa references | Đây là template generic, không phải config full CASIA lượt 5; README/COLAB và tests còn tham chiếu. Không xóa trực tiếp. |
| `configs/casia_e0_smoke.yaml`, `casia_e1_cdcn_official_smoke.yaml` | rất nhỏ | Giữ cho smoke hoặc gom có kiểm soát | Kiểm tra nhanh pipeline, không thay số liệu full run. |

Nhóm có thể tạo lại theo CSV gồm 19.233 file, khoảng **430,02 MiB**. Chủ yếu
là hai bộ dependency ở trên. Không cần xóa báo cáo để đạt phần lớn mức giảm này.

## Những thứ phải giữ

| Nhóm | Lý do |
|---|---|
| `.git/`, `AGENTS.md`, `pyproject.toml`, `src/`, `scripts/`, `tests/` | Lịch sử, môi trường, triển khai và kiểm tra. |
| Notebook E0, Official E1, E2, lượt 5 và notebook xuất hình | Nguồn chạy/đối chiếu. Notebook clean và notebook có output có vai trò khác nhau. |
| Các config `casia_e0_bce_5e`, `casia_e1_cdcn_official`, `casia_e2_official_head_frozen`, `casia_e3_joint_bce`, `casia_e3b_staged_bce`, `casia_e4_staged_focal` | Định nghĩa những run tạo bảng kết quả. |
| `artifacts/research-audit-20261016/drive-snapshot/` và các script `verify_*.py` | Manifest, score/QA và chương trình xác minh. |
| `artifacts/round5-full-audit-20261016/` | Checkpoint từng stage, config, log, freeze và MAE validation. |
| `artifacts/round5-test-audit-20261016/` | CSV test, threshold và phân tích paired video. |
| `artifacts/round5-smoke-audit-20261016/` | Bằng chứng smoke, khác full run; giữ lịch sử kỹ thuật. |
| `reports/ROUND_5_*.md/json`, `RESEARCH_AUDIT_ROUNDS_1_4_*` | Tóm tắt đã xác minh và nguồn máy đọc. |
| `artifacts/figure-notebook-20261016/` | Hình/CSV/provenance đã kiểm tra; paper và slide cần chúng. |
| `reports/slides_round5/assets/` | Markdown/HTML dùng đường dẫn trực tiếp; xóa sẽ mất hình/nền. |
| `reports/bao_cao_cuoi_ky/ban_thao/`, kế hoạch, bảng bằng chứng, danh mục nguồn | Nền để hoàn thiện final report, còn nhiều phần viết lại được bằng kết quả đã có. |
| `.obsidian/`, `reports/marp_slides_tutorial/`, `diagrams/` | Cấu hình/cách trình chiếu và nguồn sơ đồ người dùng, không phải rác vì chưa track. |

`best.ckpt` và `best_stage_*_joint.ckpt` trùng byte ở sáu run smoke/full.
Đây là alias có chủ đích của checkpoint tốt nhất stage cuối; các công cụ dùng
tên riêng. Trùng hash **không có nghĩa có thể xóa một tên tùy ý**.

## Có nên xóa và dựng lại báo cáo cuối kỳ

Không nên. Thư mục chỉ 20,72 MiB và có bản Word đã được chỉnh, backup, 37 nguồn
tham chiếu lịch sử. Vấn đề chính là nội dung chưa được viết, không phải cấu
trúc thư mục hỏng. Tạo lại cùng khung không giải quyết phần thiếu bằng chứng.

Có thể hoàn thiện ngay bằng nguồn hiện có: tổng quan, dữ liệu, phương pháp,
thiết kế E0–E4, validation/test, phân tích lỗi ghép cặp, MAE validation, giới
hạn và kết luận. Cần sửa trạng thái E3/E4 từ dự kiến sang đã hoàn tất.

Không thể tự đánh dấu hoàn tất bằng cách viết: nhiều seed, benchmark độc lập,
latency cùng môi trường, webcam/nhận diện danh tính chưa có phép đo. Các phần
này phải ghi chưa thực hiện, hoặc chạy thí nghiệm theo đăng ký và compute
được người dùng cung cấp. Phân công, email, giảng viên và mã lớp cần xác nhận;
không suy diễn từ lịch sử chat.

Thứ tự hợp lý khi cần nhận xét sớm: hoàn thiện bài báo nghiên cứu riêng từ
bằng chứng lượt 5; sau đó dùng cùng nội dung đã kiểm chứng để điền final report.
Không biến bài báo thành khung 18 trang bằng cách đổi tên file.

## Đối chiếu yêu cầu của thầy và các bài đã nộp

Nguyên văn người dùng cung cấp ngày 16/10 phân biệt bản hiện tại của final
report và bài báo; đánh giá cuối kỳ xét cả hai. Thầy yêu cầu bản Word của
paper để nhận xét. Đuôi dùng khi tạo là `.docx`; “WORDX” trong tin nhắn không
phải đuôi chuẩn cần tạo. Hai mẫu thầy đã gửi chưa được cung cấp trong dự án.

Đã đọc nội dung một số file trực tiếp qua Google Drive, không chỉ nhìn tên:

| Nhóm/file | Bằng chứng cấu trúc | Kết luận giới hạn |
|---|---|---|
| [Nhóm 9 Final Report .docx](https://docs.google.com/document/d/1FsDQQ6-xkuvuZguk6lN0Jgoy8yEo0ujr/edit) | Bìa “BÁO CÁO HỌC PHẦN”, mục lục nhiều chương, phụ lục tới trang 50 | Báo cáo học phần, không chỉ vì đuôi DOCX mà thành paper. |
| [Nhóm 15 Bao_Cao_GK_TGMT](https://docs.google.com/document/d/1WwmL8GNRrzufmqlKs85p-GgyvaDRhHrgWfNe2PqKLQE/edit) | Bìa, mục lục tám chương, tài liệu tham khảo trang 44 | Báo cáo dài. |
| [Nhóm 15 paper/CLIPER](https://docs.google.com/document/d/1TmKq8DHT1BlP95yx-bPMY6kk6yoibN39wLQFM0eYVyI/edit) | Tác giả Hanting Li và cộng sự, đơn vị USTC; Abstract, I Introduction | Bài báo của tác giả bên ngoài, tài liệu tham khảo; không coi là bài tự viết của nhóm. |
| [Nhóm 6 CV-Report.docx](https://docs.google.com/document/d/1-q6yHUk7GTlbkdZ71xMcSBEHsr57QLgU/edit) | Mục lục, tóm tắt đề tài, phần giới thiệu và các phần triển khai | Mang cấu trúc báo cáo; chưa kiểm định chất lượng/số liệu của nhóm này. |
| [Nhóm 20 Paper_D2Dewarp_V2_v1.docx](https://docs.google.com/document/d/1YiOVvg1Q5KERuAjE5AIMbhD5g-Xb92cd/edit) | Tên tác giả/đơn vị ĐH Bách khoa, tóm tắt, từ khóa, giới thiệu, related work, phương pháp, thực nghiệm, kết quả | Có bản viết theo cấu trúc bài báo nghiên cứu, khác báo cáo học phần có bìa/mục lục. Không xác minh kết quả khoa học của bài này. |
| Nhóm 4 | Listing hiện có cả PDF và DOCX cùng tên đề tài | Chỉ xác minh định dạng đang có; chưa kết luận đây là paper bằng tên file. |

Do đó, việc người dùng mở 1–2 báo cáo không đủ để kết luận thầy nhầm: thư mục
Article đang chứa nhiều loại tài liệu, và có ít nhất một bản viết theo cấu
trúc bài báo của nhóm sinh viên. Không có snapshot trước tin nhắn để xác minh
định lượng lời “nhiều nhóm” từng chỉ nộp PDF, hoặc kết luận ai nộp sai/hết hạn.
Thư mục nhóm 1 trả về danh sách rỗng trong lần đọc này; đó là trạng thái
connector tại thời điểm kiểm tra, không suy ra lịch sử nộp hoặc quyền truy cập.

## Cách sắp xếp đề xuất

Giữ nguồn code/config/notebook ở vị trí hiện tại. `reports/paper_round5/` chứa
bài báo và checklist; `reports/bao_cao_cuoi_ky/` chứa final report; slide ở
`reports/slides_round5/`. Lưu bản cũ trong thư mục archive theo ngày nếu cần,
sau khi kiểm tra và cập nhật các link liên quan. Không di chuyển raw run hoặc
checkpoint chỉ để làm cây thư mục nhìn gọn.
