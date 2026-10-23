# Nguồn bằng chứng cho hai tài liệu mới

Số trích dẫn trong hai bản thảo được sắp riêng theo thứ tự xuất hiện.
Thông tin quản lý tệp và kiểm thử nằm tại đây, ngoài nội dung khoa học.

| Nội dung | Nguồn trong repository | Phạm vi kiểm tra |
| --- | --- | --- |
| E0–E4, seed 42 | reports/RESEARCH_AUDIT_ROUNDS_1_4_2026-10-16.json; reports/ROUND_5_FULL_VALIDATION_2026-10-16.json; reports/ROUND_5_TEST_RESULTS_2026-10-16.json | Kế thừa kiểm toán và dựng bảng từ JSON; giữ cohort lịch sử riêng |
| E1/E3, seed 43–45 | reports/ROUND_6_RESULTS_2026-10-22.json | Kiểm lại hash và số học từ 43.200 score frame, 2.160 bản ghi video trên cùng 360 video |
| Mean, sample SD và paired delta | Cùng JSON Lượt 6; SOURCE_RECHECK.json; tests/test_round8_documents.py | n=3, SD dùng n−1; không coi video lặp là độc lập |
| Chi phí A100 | reports/ROUND_6_COST_RESULTS_2026-10-22.json; artifacts/round6-cost-audit-20261022/timings.csv | Tính lại p50/p95 CUDA và host từ 3.600 timing, không chạy GPU |
| Lỗi và subgroup | reports/round7/analysis/analysis.json; reports/round7/analysis/subgroups.csv | Giữ mẫu số và kết quả bất lợi seed 44; quality không đo blur/ánh sáng |
| Hình lỗi | reports/round7/figures-attempt03/provenance.json; reports/round7/FIGURES_QA.json | Case 12/13 sao nguyên byte; depth CPU đã có, video decision từ CUDA cũ |
| Webcam đã đo | reports/round7/WEBCAM_RESULTS.json; reports/round7/ADDENDUM_RESULTS_DISCUSSION_2026-10-22.md | Kế thừa audit integrity/state/timing; phiên này không đo hoặc giải mã video lại |
| Công trình khác | reports/ROUND_6_PAPER_PROTOCOL_COMPARISON_2026-10-22.json và PDF có hash trong đó | Giữ riêng OULU, CASIA development và cross-dataset; không xếp hạng chung |
| Hình seed 42 và sơ đồ | reports/bao_cao_cuoi_ky/hinh_anh/notebook; reports/bao_cao_cuoi_ky/hinh_anh/hoan_thien | Bốn PNG sao nguyên byte; sơ đồ mô tả triển khai |
| Bản lịch sử | Hai Markdown và hai Word trong reports/bao_cao_cuoi_ky và reports/paper_round5 | Hash giữ nguyên, ghi trong hai provenance mới |

Báo cáo: Bảng 6–10 thuộc seed 42; Bảng 11–14 thuộc ba seed mới; Bảng 15
là cost; Bảng 16 là webcam cũ; Bảng 17 là bối cảnh paper. Hình 5–6 của
báo cáo tương ứng Hình 1–2 của paper. Hash sáu ảnh và nguồn gốc nằm trong
SOURCE_RECHECK.json.

Paper dùng bố cục tham chiếu IEEE conference A4 hai cột, giữ tiếng Việt và
năm từ khóa chuyên ngành. Chưa chọn nơi nộp. Nguồn định dạng chính thức ở
README.md; đây không phải chứng nhận đủ điều kiện xuất bản.
