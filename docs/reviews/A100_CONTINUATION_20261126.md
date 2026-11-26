# Rà soát phần cứng cho lượt tiếp tục CDCN–PRNet

## Câu hỏi và quyết định thiết kế

Người dùng ưu tiên tính đúng đắn và khả năng giải trình khi tiếp tục
lượt CDCN–PRNet trên OULU-NPU P1 từ epoch 100 tới 1.300. Runtime hiện
tại được Colab cấp A100 40 GB, còn lượt 100 epoch đã dùng A100 80 GB.

Nhánh tiếp tục chính chọn giữ `NVIDIA A100-SXM4-80GB`, theo tên GPU
trong báo cáo gốc. Đây là lựa chọn kiểm soát điều kiện của lượt này.
Việc dùng A100 40 GB trong một thực nghiệm có cấu hình và nguồn gốc
được ghi đầy đủ vẫn có thể hợp lệ về phương pháp.

## Bằng chứng đã có và giới hạn

| Quan sát | Điều được xác nhận | Phần chưa được kiểm chứng |
| --- | --- | --- |
| `pilot_result.json` của lượt 100 epoch | GPU A100-SXM4-80GB, batch 56, seed 43, PyTorch 2.14.1+cu130 | Báo cáo cũ chưa ghi đầy đủ CUDA, cuDNN và các cờ thuật toán |
| Phép đo batch 56 trên A100 40 GB | Forward, backward và Adam đã chạy, bộ nhớ PyTorch giữ đỉnh khoảng 35,50 GiB | Tương đương trọng số và chỉ số sau nhiều epoch với A100 80 GB |
| Kiểm thử phục hồi cục bộ | Khôi phục optimizer, scheduler và bộ sinh số ngẫu nhiên, tiếp tục đúng epoch, chọn theo Dev | Tính trùng từng bit giữa hai runtime Colab hoặc hai GPU |
| Kiểm thử tuần tự và song song trên hai video CPU | Hai video mẫu khớp trong runtime được kiểm | Tính trùng của huấn luyện GPU hoặc toàn bộ tiền xử lý trên mọi runtime |

Khuyến nghị trước đó chuyển ngay sang 40 GB dựa trên khả năng chạy vừa
bộ nhớ. Cơ sở đó chưa đủ để khẳng định kết quả huấn luyện tương đương.
Giới hạn này được ghi lại để người thiết kế và người đọc kết quả thấy
đúng phạm vi bằng chứng. [Bảng đo hai GPU](../CDCN_CVPR2020_OULU_P1.md#lượt-traindev-mở-rộng).

PyTorch nêu rõ giới hạn tái lập qua nền tảng và phiên bản, kể cả khi
cùng seed. Thứ tự phép tính số thực có thể làm kết quả khác từng bit.
Giữ cùng A100 80 GB giảm một thay đổi phần cứng, nhưng muốn khẳng định
trùng số học vẫn cần một phép đối chiếu được định nghĩa và đo thực tế.
[PyTorch về tái lập](https://docs.pytorch.org/docs/2.14/notes/randomness.html),
[PyTorch về độ chính xác số học](https://docs.pytorch.org/docs/2.14/notes/numerical_accuracy.html).

Chưa định lượng mức thay đổi trọng số, điểm video hoặc ACER do chuyển
giữa A100 40 GB và 80 GB trong lượt huấn luyện này. Cũng chưa chứng minh
nguồn sai khác của một khung trong cache CPU cũ là do số vCPU hoặc loại
CPU. Các giả thuyết này cần được phân biệt với kết quả đã quan sát.

## Cách thực hiện nhánh chính

1. Chọn runtime có GPU `NVIDIA A100-SXM4-80GB` trước cell 4.
2. Khôi phục cùng cache Train/Dev và trạng thái epoch 100 đã khóa.
3. Chạy cùng batch 56, seed 43, optimizer, lịch LR và quy tắc chọn
   checkpoint trên Dev như kế hoạch đã ghi.
4. Ghi GPU, VRAM, PyTorch, CUDA, cuDNN, NumPy, OpenCV, TF32 và các tùy
   chọn deterministic trong `schedule.json`. Khi tiếp tục cùng lịch,
   đối chiếu bộ thông tin đó. Thông tin GPU và thư viện được ghi từ
   lượt nguồn cũng nằm trong `source_environment` để kiểm tra.

Notebook và worker kiểm GPU trước khi train. Thư mục của nhánh này là
`dev-continuation-p1/from100-seed43-to1300-every50-a10080`, giúp định vị
đúng cấu hình đã chọn. Nếu đã có dữ liệu ở thư mục tiếp tục cũ, giữ dữ
liệu đó để kiểm riêng theo báo cáo và checkpoint tương ứng.

Mã ghi lại các cờ tính toán đang dùng. Lượt nguồn chưa ghi đủ các cờ
đó, nên không suy ra chúng từ seed hoặc tên GPU. Kiểm thử phần mềm đã
đạt cũng cần được phân biệt với bằng chứng tái lập thực nghiệm trên
Colab. Lượt Test 100 epoch đã khóa được ghi riêng trong
[bản kết quả](../results/OULU_P1_CDCN_PRNET_20261118.md).
