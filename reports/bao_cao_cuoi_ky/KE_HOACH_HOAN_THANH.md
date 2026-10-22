# Kế hoạch hoàn thành báo cáo cuối kỳ

Cập nhật ngày 16/10/2026, múi giờ Việt Nam. Người dùng yêu cầu tiếp tục báo cáo
sau khi hoàn tất thí nghiệm lượt 5 và cung cấp thông tin bìa. Bản hiện tại
hoàn thiện nội dung đến lượt 5, không xác nhận toàn bộ nghiên cứu tám lượt đã
kết thúc. Các quyết định tạm dừng và bảng nguồn chỉ tới E2 của 15/10 đã được
thay bằng trạng thái này.

## Thông tin và quyết định hiện hành

- Học phần Thị giác máy tính, lớp 1021673.2610.23.14; Khoa Công nghệ thông tin,
  Trường Đại học Bách khoa, Đại học Đà Nẵng.
- Giảng viên TS. Huỳnh Hữu Hưng, tên/học vị xác minh từ https://scv.udn.vn/hhhung.
  Scholar trả 429 khi đọc; không dùng trang không đọc được để đoán học hàm.
- Trịnh Minh Đạt, MSSV 102230180; Nguyễn Hữu Minh Quân, MSSV 102230208.
- Phân công đề xuất A=Đạt, B=Quân, mục tiêu 50%–50% trách nhiệm; A dẫn 1/3/5/7,
  B dẫn 2/4/6/8. Chưa xác nhận đây là lịch sử công việc/báo cáo đã xảy ra.
- Giữ cấu trúc bìa/tóm tắt/phân công/mục lục, bốn chương, kết luận, tham khảo
  và phụ lục. A4 một cột, TNR 13, giãn dòng 1,3; lề trái 3 cm, còn lại 2 cm.
  Giới hạn 15–20 trang tính cả phần đầu/cuối theo phân bổ làm việc đã chốt.
- Giữ CASIA của E1/E2, 16/4/30 người và 20 frame/video; seed 42. E3/E3b/E4 đã
  có full validation và test; E3 giữ lựa chọn validation. Nhiều seed chưa chạy.
- Final report và paper là hai tài liệu riêng theo tin nhắn thầy đã cung cấp.
  Template-DUT-Total là mẫu slide, không thay mẫu Word báo cáo này.

## File và nguyên tắc đồng bộ

- Nội dung: ban_thao/BAO_CAO_CUOI_KY.md.
- Word: ban_thao/Nhom1_Bao_cao_cuoi_ky_DeepFace_PAD_20261016.docx.
- Builder: scripts/build_final_report_completed.py; test: tests/test_final_report_completed.py.
- Bản KHUNG Word/Markdown giữ nguyên. Bản sao trước cập nhật và hash nằm tại
  artifacts/final-report-completion-20261016/backup/ và backup-hashes.json.
- Lịch sử kế hoạch 15/10 vẫn xem được trong Git, gồm commit ca99b13. Lịch báo
  cáo buổi sáng đã qua không được dùng như lịch tương lai hiện hành.
- [Phân công chi tiết](PHAN_CONG_HAI_THANH_VIEN.md).
- [Danh mục nguồn hiện hành](nguon/DANH_MUC_NGUON.md).

Chỉ đánh dấu đã soạn khi nội dung thực sự có trong Markdown/Word. Người đọc
hiểu và chấp nhận kết luận là bước xác nhận của nhóm, không suy ra từ việc tạo
file. Cập nhật field/mục lục và kiểm tra mọi trang sau sửa bố cục. Commit theo
AGENTS.md; không push/nộp khi chưa có yêu cầu tương ứng.

## Checklist theo các khối đã chốt

### Khối 0 Đầu vào và trách nhiệm

- [x] Điền khoa, giảng viên, mã lớp và hai MSSV từ nguồn đã xác nhận.
- [x] Lập phân công cân bằng theo tám lượt, có người rà soát chéo.
- [x] Xác nhận kết quả mới E3/E3b/E4 và chọn file Word/Markdown hiện hành.
- [ ] Hai thành viên xác nhận riêng công việc lịch sử nếu cần bảng chấm đóng góp.

### Khối 1 Khóa nguồn kết quả

- [x] Đọc bảng nguồn E0/E1/E2 và kiểm toán raw CSV/JSON/checkpoint 16/10.
- [x] Bổ sung validation, depth MAE, freeze và test E3/E3b/E4.
- [x] Tách validation/test, ngưỡng, epoch trong stage và global epoch.
- [x] Giữ run ID, seed, split, mẫu số, đơn vị và phạm vi kiểm chứng.

### Khối 2 Chương dữ liệu

- [x] Viết nguồn CASIA, sửa HR_1 và loại bs/fs.
- [x] Điền bảng 50 người/600 video/12.000 frame, tách người giữa các tập.
- [x] Viết resize, chuẩn hóa riêng E0/depth và augmentation đồng bộ.
- [x] Giải thích 3DDFA offline, pseudo-depth, zero map, mask và QA.
- [x] Viết manifest/hash/path; chèn mẫu validation có nguồn và giới hạn rõ.

### Khối 3 Chương phương pháp

- [x] Định nghĩa các cấu hình và luồng frame→video→ngưỡng.
- [x] Mô tả E0, CDC, topology/tensor E1 và phép đối chiếu upstream.
- [x] Mô tả E2, freeze weights/BatchNorm và 1.265 tham số thêm.
- [x] Trình bày official MSE/contrast MSE, BCE, Focal và alpha/gamma thực tế.
- [x] Viết joint/staged, reset optimizer, restore best và chọn checkpoint.
- [x] Chèn sơ đồ từ code; không dùng ảnh AI làm bằng chứng thí nghiệm.

### Khối 4 Chương thực nghiệm

- [x] Viết phần cứng/phần mềm, seed và khác biệt cu128/cu130.
- [x] Định nghĩa metric, đơn vị và EER rời rạc không nội suy.
- [x] Điền validation/test sáu cấu hình; giữ E3 chọn trước test.
- [x] So riêng head, chiến lược và loss; giữ kết quả chưa cải thiện.
- [x] Chèn curve/histogram đúng run, ghi checkpoint và khác thang loss.
- [x] Điền paired errors, năm video cùng sai, nhóm quality và MAE.
- [x] Báo latency E1/E2 sơ bộ, không suy rộng thành FPS webcam.
- [x] Giữ giới hạn một seed, test đã quan sát và benchmark chưa độc lập.

### Khối 5 Chương tổng quan

- [x] Phân biệt PAD với danh tính và phạm vi tên đề tài.
- [x] Giải thích động cơ depth/head và câu hỏi kiểm chứng được.
- [x] Viết literature, nguồn kế thừa và giới hạn direct comparison.
- [x] Trình bày E1–E2, E3–E3b và E3b–E4 theo đúng biến đang xét.

### Khối 6 Phần đầu và cuối

- [x] Viết tóm tắt, từ khóa và bìa; ngày 19/10 đã biên tập theo quy tắc học thuật.
  Bảng trách nhiệm chuyên môn được giữ ở phần đầu report; kế hoạch chi tiết ở tài liệu riêng.
- [x] Kết luận từ số đã trình bày; hướng tiếp theo lượt 6–8.
- [x] Bảy tài liệu được dẫn trong nội dung, phụ lục run/hash/tái lập.
- [ ] Nhóm đọc lại và xác nhận cách dùng bảng trách nhiệm khi nộp.

### Khối 7 Rà câu chữ và bằng chứng

- [x] Giải thích thuật ngữ chính; tách quan sát, giả thuyết và kế hoạch.
- [x] Bỏ ô hướng dẫn/ô trống; giữ đúng số và chiều metric.
- [x] Rà giới hạn một seed/protocol và tiền lệ của ý tưởng head.
- [ ] Hai thành viên đọc và giải thích được các phần được giao.

### Khối 8 Word và nộp

- [x] Dựng Word và cập nhật TOC/danh mục bằng Microsoft Word.
- [x] Có render kiểm tra mọi trang; ghi kết quả ở KIEM_TRA_BAN_HOAN_THIEN.md.
- [ ] Bản biên tập học thuật ngày 19/10 hiện 24 trang, vượt ngân sách cũ 15–20 trang.
  Chưa rút gọn lại nội dung vì yêu cầu hiện tại là giữ văn phong và sửa tối thiểu.
- [ ] Nhóm xác nhận nội dung và thư mục nộp theo chỉ dẫn hiện hành.
- [ ] Upload khi người dùng yêu cầu; đọc lại metadata sau upload.
- [ ] Luyện bảo vệ, cập nhật slides nếu được yêu cầu tiếp.

## Nghiên cứu còn lại chưa được đánh dấu hoàn tất

Lượt 6 chờ compute để khóa/run nhiều seed và đo chi phí đồng điều kiện. Lượt 7
còn ảnh lỗi test đúng mẫu, webcam và phép đo end-to-end. Lượt 8 còn xác nhận
của nhóm, hiệu chỉnh sau phản hồi và việc nộp. Tạo báo cáo hiện tại không thay
bằng chứng cần thu ở những lượt đó.

## Nhật ký

| Phiên | Đầu ra | Trạng thái |
| --- | --- | --- |
| 15/10 | Khung 18 trang, bảng nguồn tới E2 | Giữ lịch sử/đối chiếu |
| 16/10 thí nghiệm | Kiểm toán 1–4, full validation/test lượt 5 | Kết quả seed 42 đã có |
| 16/10 báo cáo | Nội dung tới lượt 5, phân công và Word | Kiểm tra/nộp theo checklist hiện hành |
