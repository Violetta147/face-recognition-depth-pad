# Dùng Colab sau khi nhận bàn giao

Không cần Colab để đọc số liệu hoặc kiểm score CSV. Chỉ cấp GPU khi đã có
kế hoạch inference hoặc huấn luyện mới và đã có dữ liệu đúng hash.

1. Clone đúng nhánh bàn giao. Không giả định main là bản sạch được giao.
2. Kiểm delivery/FILES.json trước khi dùng checkpoint.
3. Mount Drive của người vận hành. Xác nhận người đó đọc được dữ liệu nguồn.
4. Khôi phục archive đúng hash theo danh mục. Đặt đường dẫn theo máy Colab.
5. Cài dependency. Ghi torch, torchvision, CUDA, GPU và driver thực tế.
6. Chạy test CPU và kiểm manifest/depth trước khi train.
7. Đặt config và output mới cho thí nghiệm mới. Giữ log và thất bại.

Các notebook *_Executed.ipynb là hồ sơ lịch sử. Không Run all các file này.
Một số cell đã lưu cổng mở train/test. Cổng đã mở trong hồ sơ không cấp quyền
chạy lại. Các notebook clean là công cụ của protocol cũ; đọc mục đích và gate
trước khi dùng. Source ZIP cũ nằm trong evidence/source_archives hoặc khu vực
artifact nghiên cứu được ghi trong FILES.json. SOURCE_LOCK trong ZIP khóa
đúng nội dung cũ. Không sửa ZIP để phù hợp một môi trường mới.

Nếu cần một thí nghiệm mới, dùng mã nguồn hiện tại và phiếu thí nghiệm mới.
Nếu cần đối chiếu lịch sử, giải nén source cũ vào thư mục riêng. Không dùng
commit cũ trong báo cáo như một commit chắc chắn có trên nhánh bàn giao sạch.
