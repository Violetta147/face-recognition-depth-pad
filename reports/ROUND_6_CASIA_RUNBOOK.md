# Chạy Lượt 6 trên Colab

Sau test, `scripts/audit_round6_results.py` đối chiếu freeze đã kiểm trước test,
registration/initializer/environment binding, đủ epoch, minimum validation loss,
ID/nhãn frame, mean frame → video, threshold validation, toàn bộ metric và
mean/sample SD/paired delta từ CSV đã lưu. Chỉ đọc artifact và tính lại số liệu;
không train hoặc inference. Snapshot kiểm toán không chép ảnh hay trọng số.

Gói mới dùng seed 43/44/45: E1 30 epoch rồi E3 joint BCE 16 epoch từ best E1
cùng seed, tổng sáu run/138 epoch. E1 chọn minimum validation depth loss;
E3 chọn minimum validation BCE. Threshold lấy minimum validation ACER, sau đó
độ lệch APCER–BPCER, rồi threshold nhỏ hơn. Cấu hình và evaluator giữ như kế
hoạch `ROUND_6_REPLICATION_PLAN.md`. Seed 42 chỉ là lịch sử; E3 vẫn là ứng viên.

## Trình tự và điểm dừng

1. Mở notebook `notebooks/Face_PAD_Round6_CASIA_E1_E3.ipynb` bằng Colab.
   Chọn Runtime → Change runtime type → A100 GPU. Mount đúng Drive có `face-pad`.
2. Chạy các cell 0 và 1 để nạp ZIP source, CPU tests, khôi phục dữ liệu/cache
   đã có, kiểm manifest/provenance và đăng ký môi trường. Không tải dataset mới.
   Cache live 3DDFA được tái sử dụng; attack zero cố định có thể được khôi phục
   bằng helper cũ. Không chạy worker 3DDFA. Toàn bộ 12.000 target phải khớp hash
   của snapshot đã khóa, gồm cả attack zero. Không đổi split/normalization.
3. **Dừng tại PREFLIGHT PASS**, gửi output cuối cell 1.4 và CPU tests.
   Không dùng Run all. Chỉ mở cổng train sau khi đã kiểm output và thời gian
   A100 còn lại. Ước lượng 2–3 giờ gồm setup/QA chưa phải thời gian thực đo.
4. Chạy một cặp seed 43 rồi kiểm run ID, log/loss, initializer và thời gian.
   Làm tương tự seed 44, 45. Mỗi cổng mặc định False. Run dở dang được giữ;
   dừng khi gặp run trùng/khác nội dung, không tự chọn run tốt hoặc ghi đè.
5. Sau cả sáu validation, chạy freeze và gửi bảng validation cùng đường dẫn
   `comparison_freeze.json`. Test vẫn đóng. Freeze chứa registration hash,
   hash checkpoint/config/threshold/log/score validation/provenance và binding
   môi trường cho đủ sáu run. Mỗi E3 khóa hash best E1 đúng seed.
6. Chỉ mở test sau khi freeze được kiểm tra. Runner test từ chối thiếu freeze,
   dữ liệu override, checkpoint sai hoặc artifact đã đổi. Giữ mọi kết quả.

## Bằng chứng và gián đoạn

`registration.json` lưu source commit và toàn bộ hash source trong ZIP, config
của sáu run, manifest, ledger, 12.000 hash depth, GPU UUID/driver, Python,
torch/CUDA/cuDNN và `pip freeze`. Môi trường phải khớp trước từng cặp và freeze.
Mỗi run ghi binding từ đầu, kiểm lại log đủ epoch và minimum validation loss;
metrics/threshold được tính lại từ CSV validation trước freeze.

E3 warm-start từ best E1; **không phải full resume**. Runner chưa khôi phục
optimizer/scheduler/RNG. Nếu bị ngắt, giữ partial log/checkpoint và báo tiến độ
thật; không xóa run lỗi hoặc tự dùng lại như run hoàn tất. Khi Colab đổi GPU,
driver hoặc dependency, dừng để xác định block môi trường mới.

Bảng cuối lưu từng run và mean/sample SD (ddof=1) cho APCER/BPCER/ACER/EER/AUC.
Đơn vị video; metric JSON/CSV là tỷ lệ, bảng notebook hiển thị phần trăm (AUC
không có đơn vị). Paired delta ACER = E3 − E1; delta dương là kém hơn E1.
Ba seed CASIA development không đủ kết luận tổng quát hoặc ý nghĩa thống kê.
Không gộp seed 42, không chọn lại E4 từ test. Hai Word và notebook cũ giữ nguyên.

Chi phí E1/E3/E4 cùng GPU/input/warm-up/lượt lặp vẫn là đầu việc riêng của
Lượt 6 sau replication; gói này không tạo số đo latency hoặc suy ra FPS webcam.

## Kiểm tra cục bộ

`python -m pytest -q tests/test_round6.py tests/test_preflight.py
tests/test_training_stages.py tests/test_official_depth_head.py tests/test_metrics.py
tests/test_manifest.py` kiểm logic CPU và các cổng, không chạy CASIA/A100 thật.
Không trình bày PASS CPU là kết quả sáu run hoặc thời gian đã đo.
