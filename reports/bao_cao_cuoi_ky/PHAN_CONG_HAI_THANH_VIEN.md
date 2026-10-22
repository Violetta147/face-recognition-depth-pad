# Phân công cân bằng cho hai thành viên

Ngày 16/10/2026, người dùng yêu cầu phân chia đều khối lượng theo kế hoạch 8
lượt và các artifact hiện có. Quy ước làm việc đề xuất: **A là Trịnh Minh Đạt**
(102230180), **B là Nguyễn Hữu Minh Quân** (102230208). Mỗi người dẫn bốn lượt;
người còn lại hỗ trợ demo, ghi phản hồi và kiểm tra chéo.

**Mục tiêu phân công là 50%–50% trách nhiệm dự kiến, không phải số đo đóng góp
đã hoàn thành.** Git, notebook và checkpoint xác nhận nội dung công việc, chưa
xác nhận đầy đủ người thực hiện. Bảng này dùng để nhận trách nhiệm rà soát,
giải thích và tiếp tục các gói công việc; không đổi thành bảng thành tích cá
nhân nếu hai thành viên chưa xác nhận công việc lịch sử.

## Chia theo lượt và đầu ra

| Lượt | Trịnh Minh Đạt phụ trách | Nguyễn Hữu Minh Quân phụ trách | Bằng chứng và trạng thái |
| --- | --- | --- | --- |
| 1 | Câu hỏi PAD, literature, giới hạn so sánh và Chương 1 | Sơ đồ hệ thống, phạm vi triển khai, skeleton và mô tả kiến trúc | Đặc tả, LITERATURE_MATRIX.md, mã nguồn; lõi nghiên cứu đã có |
| 2 | Manifest, chia người/video, sửa ánh xạ nhãn, validator và định nghĩa metric | E0 MobileNetV3, train loop, checkpoint, đường học và score export | E0.ipynb, prepare_casia_fasd.py, metrics.py; E0 đã có kết quả |
| 3 | Quy trình 3DDFA V2 offline, depth ledger, mask và kiểm tra nhãn | Official CDCN, loss độ sâu, verifier mã tác giả và E1 | Notebook Official E1, cdcn_official.py, audit lượt 1–4; E1 đã có kết quả |
| 4 | Đối chiếu ngưỡng/manifest, ghép lỗi E1–E2 và phân tích quyết định | Depth head, đóng băng weights/BatchNorm, E2 và số tham số | Notebook E2, depth_head.py, comparison_freeze; E2 đã có kết quả |
| 5 | Ma trận đối chứng, E3 joint BCE, quy tắc validation và bảng ablation | E3b/E4 staged, Focal loss, xuất depth MAE và kiểm tra stage checkpoint | Notebook lượt 5, ba config, full validation/test JSON; ba nhánh đã có kết quả |
| 6 | Rà protocol paper, kiểm tra cặp seed, tổng hợp paired delta và viết giới hạn | Điều phối run nhiều seed, benchmark cùng môi trường, tổng hợp mean/SD | ROUND_6_REPLICATION_PLAN.md; chưa chạy đợt nhiều seed. Hai người chia lượt vận hành GPU theo thời gian thực tế, không dồn toàn bộ train cho một người |
| 7 | Nhóm lỗi, kiểm tra RGB/target/prediction, viết phân tích và kịch bản live/print/replay | Tích hợp detector/PAD webcam, cửa sổ điểm, đo FPS và time to decision | Paired CSV đã có; ảnh lỗi test và webcam chưa được xác nhận hoàn tất |
| 8 | Rà claim/nguồn, Chương 1–2, phần metric/phân tích Chương 4 và thư mục nộp | Rà tái lập, Chương 3, phần train/kết quả Chương 4, phụ lục và định dạng Word | Báo cáo và paper cùng kiểm tra; hai người cùng viết tóm tắt/kết luận, luyện Q&A |

Đạt dẫn lượt 1, 3, 5, 7; Quân dẫn lượt 2, 4, 6, 8 theo phân công đề xuất.
Việc này không xác nhận ai đã thuyết trình các buổi trước.

## Cân bằng khi triển khai

Chia theo đầu ra có thể kiểm tra, không chia theo số dòng code hoặc số trang.
Viết/chạy một pipeline, kiểm toán kết quả và giải thích được kết luận đều là
công việc nghiên cứu. Các lượt đầu Đạt có phần dữ liệu/metric/pseudo-depth
nặng; Quân có phần model/train/loss nặng. Ở lượt 5 Đạt nhận một nhánh train
và tổng hợp đối chứng, Quân nhận hai nhánh dùng chung nền staged; kiểm tra
chéo cấu hình trước khi kết luận. Ở lượt 6 hai người cùng vận hành và rà run,
không coi thời gian GPU tự chạy là toàn bộ thời gian lao động của người phụ trách.

Sau mỗi gói, ghi ngắn công việc thực tế, artifact/commit, thời gian chủ động
ước lượng và người rà. Nếu một người bị dồn việc, chuyển gói tiếp theo trước
khi triển khai. Mục tiêu 50%–50% là cơ chế phân công để điều chỉnh, không phải
một tỷ lệ đánh giá cá nhân đã được chứng minh.

## Kiểm tra chéo và nghiệm thu

- Đạt kiểm E0/E1/E2/E3/E3b/E4 đúng dữ liệu, split, ngưỡng và mẫu số; Quân kiểm
  công thức, code tính bảng và sự nhất quán giữa Markdown với Word.
- Quân kiểm topology, freeze, loss và stage; Đạt lần theo config/checkpoint
  để bảo đảm kết luận thực sự cô lập được biến đang xét.
- Cả hai đọc báo cáo, giải thích kết quả âm tính, phân biệt validation/test,
  và xác nhận bảng đóng góp lịch sử trước khi dùng làm căn cứ chấm cá nhân.
- Phần chưa chạy giữ trạng thái kế hoạch. Báo cáo tới lượt 5 không được dùng
  để đánh dấu đã hoàn thành toàn bộ nghiên cứu 8 lượt.

Nguồn: `KE_HOACH_THUC_HIEN_THEO_BUOI_HOC.md`,
`reports/RESEARCH_AUDIT_ROUNDS_1_4_2026-10-16.json`,
`reports/ROUND_5_FULL_VALIDATION_2026-10-16.json`,
`reports/ROUND_5_TEST_RESULTS_2026-10-16.json` và
`reports/ROUND_6_REPLICATION_PLAN.md`.
