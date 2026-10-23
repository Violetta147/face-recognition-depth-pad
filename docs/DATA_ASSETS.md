# Dữ liệu cần nhận ngoài Git

Code, manifest, checkpoint, score, bản khóa, hình và tài liệu đã có trong
repository. Đọc báo cáo, phân tích CSV và sửa tài liệu không cần dataset.

## Tệp trên Drive

Chủ dự án quản lý Drive `face-pad` và sẽ cấp email đồng đội quyền đọc/tải.
Chưa kiểm quyền tải trên tài khoản đồng đội. Ổ G: là cách máy nguồn gắn
Drive, không phải yêu cầu cho máy mới.

| Tệp | Kích thước byte | Vị trí khi cần dùng |
| --- | ---: | --- |
| `casia-fasd.zip` | 2.198.264.547 | `evidence/face-pad/casia-fasd.zip` |
| `depth-checkpoints/casia-fasd-depth-checkpoint.tar` | 20.439.040 | `evidence/face-pad/depth-checkpoints/casia-fasd-depth-checkpoint.tar` |
| `webcam-evidence-private.zip` | 62.254.973 | Nơi riêng; giữ cấu trúc và danh mục hash của ZIP. |

SHA-256 cần khớp trước khi dùng:

```text
casia-fasd.zip
84096c9734cf6120d36ed8f45d82864259420b2af0bd5ce4c7230fd9a572cd1b

casia-fasd-depth-checkpoint.tar
26cfa7f26d61e3a71372404008f5dc9dd696af931172850986a8642e440b3d80

webcam-evidence-private.zip
6e107745ea7dfa5b548ccc87437327d0d08f52a3ebdfbd72df32227daf964e56
```

Kiểm trên Windows: `Get-FileHash -Algorithm SHA256 -LiteralPath '<tệp>'`.
Hai archive dữ liệu đã có trên Drive. Chủ dự án xác nhận đã upload ZIP webcam
ngày 23/10/2026; chưa kiểm bản tải bằng tài khoản đồng đội. ZIP có năm AVI,
CSV/summary và `PRIVATE_FILES.json`. Không cần upload lại hoặc chép cả repo lên Drive.

## Tệp cần cho từng việc

| Việc | Đầu vào ngoài Git |
| --- | --- |
| Đọc kết quả, phân tích score, sửa Word/paper/slide, kiểm mã | Không cần. |
| Chạy webcam mới | Camera máy chạy; checkpoint/detector đã có trong Git. |
| Xem clip cũ, kiểm box/reset, chọn video dự phòng | ZIP webcam riêng. |
| Dựng lại RGB/target/prediction | Archive CASIA và archive depth. |
| Train thí nghiệm khác theo yêu cầu sau này | Dữ liệu/cache đầy đủ và config mới; đọc runbook tương ứng. |

Không đưa video riêng, venv, thư viện đã cài, cache, hook, cấu hình agent
hoặc chat lên GitHub. Không gửi các nhóm này qua Drive để cài máy nhận.
Tạo lại môi trường theo `SETUP.md`.

## Hình đã có trong Git

`artifacts/figure-notebook-20261016/` theo dõi các hình nguồn cho
`reports/slides_round5/Bao_cao_DeepFace_PAD.md/.pptx`.
`reports/slides_round5/assets/provenance.json` ánh xạ nguồn sang asset và SHA.
Đây là slide đến Lượt 5, chưa phải slide cuối Lượt 8.

Hình Lượt 7: `reports/round7/figures-attempt03/`; raw arrays:
`artifacts/round7/figures-attempt03/qualitative_arrays.npz`. Checkpoint và bằng
chứng nằm ở `evidence/face-pad/` và các tệp được theo dõi trong `artifacts/`.
Không cần upload thêm các nhóm này lên Drive.
