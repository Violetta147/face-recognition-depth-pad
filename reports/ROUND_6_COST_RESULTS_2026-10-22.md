# Lượt 6: chi phí suy luận E1/E3/E4 trên A100

**Kiểm toán PASS ngày 22/10/2026.** Đủ 3.600 mẫu đo trong 18 lượt,
1.200 mẫu/model; tất cả mẫu chậm được giữ. Hash, thứ tự và thống kê tính lại
khớp artifact trên Drive. E3 tăng khoảng 0,8% latency forward so với E1
trong block này. Đây là phép đo riêng, không phải FPS webcam.

## Kết quả thực đo

Đơn vị latency là ms. p50 là trung vị; p95 là percentile 95, nội suy tuyến
tính trên toàn bộ 1.200 mẫu/model. “Host” là wall time của forward có đồng bộ
GPU; CUDA event đo elapsed trên stream. Hai phạm vi không được cộng vào nhau.

| Model | Seed checkpoint | Params | Byte checkpoint | CUDA p50 | CUDA p95 | Host p50 | Host p95 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| E1 | 43 | 2.245.016 | 9.020.220 | 5,9167 | 5,9412 | 5,9438 | 5,9706 |
| E3 | 43 | 2.246.281 | 9.029.106 | 5,9638 | 5,9905 | 5,9913 | 6,0206 |
| E4 | 42 | 2.246.281 | 9.029.042 | 5,9617 | 5,9914 | 5,9894 | 6,0219 |

So với E1, E3 thêm 1.265 parameter, tương đương **0,05635%**; tăng
**0,047104 ms / 0,7961% CUDA p50** và **0,049203 ms / 0,8282% CUDA p95**.
Host p50 tăng 0,047520 ms / 0,7995%; host p95 tăng 0,049944 ms / 0,8365%.
File checkpoint tăng 8.886 byte; file còn chứa metadata nên không đồng nghĩa
RAM hoặc VRAM. Tensor parameter/state byte được lưu riêng trong JSON.

E3 và E4 có cùng kiến trúc suy luận. Chênh lệch CUDA p50 giữa chúng chỉ
0,002048 ms; không diễn giải thành lợi thế tốc độ do BCE hay Focal Loss.
E4 seed 42 chỉ tham gia bảng chi phí, không vào mean/SD accuracy ba seed mới.

## Điều kiện và độ dao động trong block

- NVIDIA A100-SXM4-40GB, UUID `GPU-6e233774-f5a8-0a01-d08f-3eb145fc6890`,
  driver 580.82.07; torch 2.11.0+cu130, CUDA 13.0, cuDNN 92700.
- Python 3.13.15; dependency inventory đầy đủ trong registration và JSON audit.
  Đây là GPU/runtime mới, tách khỏi registration training cũ.
- Input float32, batch 1, RGB 256 × 256, contiguous NCHW; hai ảnh validation
  thật `casia_s04_v3_f000000` và `casia_s04_v1_f000000`, luân phiên.
  Ảnh crop gốc 112 × 112, áp transform Official CDCN và hash tensor trước đo.
- `eval()`/`inference_mode()`; không autocast, TF32, compile hay CUDA Graph;
  cuDNN benchmark=False, deterministic=False.
- Sáu hoán vị thứ tự E1/E3/E4, shuffle seed 20261022; mỗi model xuất hiện
  hai lần tại mỗi vị trí. Mỗi lượt 50 warm-up ngoài thống kê, 200 lần có đo.
- Decode, resize/normalize, transfer lên GPU và ghi Drive nằm ngoài timing.
  Không chọn lượt nhanh nhất, không loại outlier hoặc điều chỉnh sau khi xem số.

| Model | CUDA p50 nhỏ nhất trong 6 lượt | CUDA p50 lớn nhất trong 6 lượt |
| --- | ---: | ---: |
| E1 | 5,9146 ms | 5,9208 ms |
| E3 | 5,9617 ms | 5,9668 ms |
| E4 | 5,9566 ms | 5,9648 ms |

Các lượt là forward lặp trên cùng GPU và hai input; 1.200 mẫu không phải
1.200 lần train độc lập. Chưa khảo sát GPU khác, precision khác, batch khác,
biến động giữa nhiều phiên hoặc latency toàn pipeline. Không suy FPS webcam.

## Kiểm toán và bằng chứng

Source đo đã khóa: `d316f72ff2093fb336cc20c7a0e522cbda9363c6`.
Script audit: `scripts/audit_round6_cost.py`, commit
`4f2611996163a2054ade3d7c94a9b2a09a51875f`; không chạy model hoặc CUDA.
So sánh source lock với ZIP đã giao, plan/profile/input với preflight đã duyệt;
CSV phải đủ từng round/position/model/iteration/input đúng thứ tự. Tính lại
toàn bộ pooled/per-block summary; tolerance roundoff 10^-10 ms absolute,
10^-12 relative, số lượng và key phải khớp chính xác. p50/p95 còn được kiểm
riêng bằng sort và công thức nội suy, không gọi lại hàm quantile của runner.

| Artifact | SHA-256 |
| --- | --- |
| registration.json | `c8567914f9c8d5b3cd1833cf1f88e55e2ab1698cd4b7c0237831caf97ee15258` |
| timings.csv | `6034ac6f7133c5cee91a5f310fda0d79d68edb153a4b596453ab3b566cc83ce7` |
| results.json | `500a7a1a5a789e4de17326fd7b5b4aa3a3da29f031d3c64aa156ae56347a78f4` |
| Cost notebook executed | `37f941faa2398c40998c68e36492f6ef2f1504d3fa932d80a46804481a6b1a91` |

Drive block: `face-pad/reports/round6-cost-d316f72ff209/a100-01/`.
Bản lưu cục bộ nguyên hash: `artifacts/round6-cost-audit-20261022/`.
Kết quả đầy đủ: `ROUND_6_COST_RESULTS_2026-10-22.json`.

Đã nhận `notebooks/Face_PAD_Round6_Cost_E1_E3_E4_Executed.ipynb`: bốn code
cell execution 1–4, không output lỗi, source chỉ mở cổng đo. Receipt:
`ROUND_6_COST_EXECUTED_NOTEBOOK_2026-10-22.json`. Cell CPU test dùng checked
subprocess trước khi in GPU; raw stdout của subprocess không được lưu trong
stream notebook, không mô tả nó là log đã quan sát. Kiểm thử cục bộ thực tế:
17 test liên quan đạt; kiểm tra chốt toàn repository **194 passed, 1 skipped,
67 subtests passed**. Receipt notebook còn giữ snapshot kiểm thử trước đó.
Fixture chỉ kiểm auditor, không thay thế timing GPU.

Có thể kiểm lại saved artifact mà không cần GPU; dùng output mới để giữ
nguyên báo cáo đã chốt, ví dụ:

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
$env:CUDA_VISIBLE_DEVICES = ''
python scripts/audit_round6_cost.py --folder artifacts/round6-cost-audit-20261022 --evidence artifacts/round6-cost-audit-20261022 --output artifacts/round6-cost-audit-20261022/recheck.json
```

## Liên hệ với câu hỏi nghiên cứu

[Kết quả ba seed](ROUND_6_RESULTS_2026-10-22.md) cho thấy E3 giảm ACER trung
bình từ 4,3210% xuống 3,7037%, nhưng chỉ tốt hơn ở 2/3 seed. Paired delta
−0,6173 ± 2,6857 điểm phần trăm còn dao động lớn. Phép đo mới bổ sung bằng
chứng rằng head tăng ít tham số và forward latency trong điều kiện đã thử;
không chứng minh cải thiện accuracy ổn định hoặc tổng quát hóa.

E3 còn khác E1 về training budget và weight decay; đây là hai cấu hình hoàn
chỉnh, không cô lập tác dụng head. Giữ kết quả âm tính seed 42 riêng và không
đổi ứng viên bằng test. [Đối chiếu paper](ROUND_6_PAPER_PROTOCOL_COMPARISON_2026-10-22.md)
chỉ dùng làm bối cảnh khi protocol không trùng.
