import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const root = path.resolve(process.argv[2] ?? process.cwd());
const build = path.join(root, "artifacts/.build-report-20261002");
const output = path.join(root, "artifacts/presentations");
const finalPath = path.join(output, process.argv[3] ?? "DeepFace_PAD_Bao_cao_03-10-2026.pptx");
const skill = process.env.SKILL_DIR;
if (!path.isAbsolute(skill ?? "") || !path.isAbsolute(process.env.RUNTIME_PYTHON ?? "")) throw new Error("Set SKILL_DIR and RUNTIME_PYTHON");
const { finalizePresentation, resolvePresentationFont } = await import(pathToFileURL(path.join(skill, "container_tools/artifact_tool_utils.mjs")).href);
await fs.mkdir(build, { recursive: true });
await fs.mkdir(output, { recursive: true });
const data = JSON.parse(await fs.readFile(path.join(root, "reports/rounds1_4_presentation_content.json"), "utf8"));
const font = resolvePresentationFont({ fontFamily: "Arial" });
const c = { navy: "#18314B", teal: "#087F8C", gray: "#526575", pale: "#EFF7F8", purple: "#6A55A3", orange: "#A45A16", line: "#D6E0E5" };
const presentation = Presentation.create({ slideSize: { width: 1280, height: 720 } });
const bounds = [];

function text(slide, content, x, y, w, h, size = 27, color = c.navy, bold = false, align = "left") {
  const shape = slide.shapes.add({ geometry: "textbox", position: { left: x, top: y, width: w, height: h }, fill: "none", line: { fill: "none", width: 0 } });
  shape.text = content;
  shape.text.style = { typeface: font, fontSize: size, color, bold, alignment: align, verticalAlignment: "top", autoFit: "none", wrap: "square", insets: { top: 0, bottom: 0, left: 0, right: 0 } };
  bounds.push({ slide: presentation.slides.items.length, kind: "text", x, y, w, h, content });
  return shape;
}
function base(n, refs = []) {
  const spec = data.slides[n - 1];
  const slide = presentation.slides.add();
  slide.background.fill = "#FFFFFF";
  text(slide, spec.title, 64, 42, 1152, n === 1 ? 162 : 90, n === 1 ? 59 : 43, c.navy, true);
  text(slide, String(n).padStart(2, "0"), 1168, 677, 48, 25, 18, c.gray, false, "right");
  slide.speakerNotes.textFrame.setText(spec.notes + (refs.length ? "\n\nNguồn:\n" + refs.join("\n") : ""));
  return slide;
}
function foot(slide, value, y = 639) { text(slide, value, 64, y, 1110, 38, 19, c.gray); }
function lines(slide, rows, x, y, w, size = 27, gap = 76) {
  rows.forEach((row, i) => text(slide, row, x, y + i * gap, w, gap - 10, size));
}
function node(slide, label, x, y, w, h = 88, color = c.teal, size = 25) {
  const shape = slide.shapes.add({ geometry: "rect", position: { left: x, top: y, width: w, height: h }, fill: "#FFFFFF", line: { fill: color, width: 1.6 } });
  shape.text = label;
  shape.text.style = { typeface: font, fontSize: size, color, alignment: "center", verticalAlignment: "middle", wrap: "square", autoFit: "none", insets: { left: 8, right: 8, top: 8, bottom: 8 } };
  bounds.push({ slide: presentation.slides.items.length, kind: "node", x, y, w, h, content: label });
  return shape;
}
function arrow(slide, a, b, fromSide = "right", toSide = "left", color = c.gray) {
  slide.shapes.connect(a, b, { kind: "straight", fromSide, toSide, line: { fill: color, width: 1.8 }, tail: { type: "triangle", width: "med", length: "med" } });
}
function table(slide, values, x, y, widths, h, size = 24, highlights = []) {
  const t = slide.tables.add({ rows: values.length, columns: values[0].length, left: x, top: y, width: widths.reduce((a, b) => a + b, 0), height: h, columnWidths: widths, values });
  t.borders.assign({ style: "solid", fill: c.line, width: 0.7 });
  for (let row = 0; row < values.length; row++) for (let col = 0; col < values[0].length; col++) {
    const cell = t.getCell(row, col);
    cell.fill = row === 0 ? c.navy : highlights.includes(row) ? c.pale : "#FFFFFF";
    cell.text.style = { typeface: font, fontSize: size, color: row === 0 ? "#FFFFFF" : c.navy, bold: row === 0 || highlights.includes(row), alignment: col === 0 ? "left" : "center", verticalAlignment: "middle", autoFit: "none", insets: { top: 8, bottom: 8, left: 10, right: 10 } };
  }
  bounds.push({ slide: presentation.slides.items.length, kind: "table", x, y, w: widths.reduce((a, b) => a + b, 0), h });
  return t;
}
async function picture(slide, file, x, y, w, h, alt) {
  slide.images.add({ blob: new Uint8Array(await fs.readFile(file)), contentType: "image/png", alt, fit: "contain", position: { left: x, top: y, width: w, height: h } });
  bounds.push({ slide: presentation.slides.items.length, kind: "image", x, y, w, h });
}
async function notebookImage(name, cellIndex, ordinal, basename, expectedSource) {
  const notebook = JSON.parse(await fs.readFile(path.join(root, "notebooks", name), "utf8"));
  const cell = notebook.cells[cellIndex];
  if (!cell.source.join("").includes(expectedSource)) throw new Error("Notebook cell moved: " + name + ":" + cellIndex);
  const outputs = cell.outputs.filter(o => o.data?.["image/png"]);
  if (!outputs[ordinal]) throw new Error("Missing executed image " + name + ":" + cellIndex + ":" + ordinal);
  const image = outputs[ordinal].data["image/png"];
  const dest = path.join(build, basename);
  await fs.writeFile(dest, Buffer.from(Array.isArray(image) ? image.join("") : image, "base64"));
  return dest;
}
const e1nb = "notebooks/Face_PAD_Official_CDCN_E1_Rerun.ipynb";
const e2nb = "notebooks/Face_PAD_Round4_Official_Frozen_Head.ipynb";
const e0nb = "notebooks/E0.ipynb";
const depthCase = await notebookImage(path.basename(e1nb), 24, 11, "validation-depth-case.png", "3.3 Xuất 12 validation depth cases");
const e2Curve = await notebookImage(path.basename(e2nb), 12, 0, "e2-bce.png", "BCE curve");
const scoreDistribution = await notebookImage(path.basename(e2nb), 15, 0, "e1-e2-distributions.png", "E2 sửa được gì");
const e0e1Curve = await notebookImage(path.basename(e1nb), 31, 0, "e0-e1-curves.png", "plot_frozen_comparison.py");
const local = (...p) => p.map(v => path.join(root, v));

{
  const s = base(1);
  text(s, "Tái lập CDCN và thử learned depth head", 64, 256, 1100, 75, 37, c.teal);
  text(s, "Báo cáo tiến độ · Lượt 1–4", 64, 390, 1100, 42, 28);
  text(s, data.authors.join("  •  "), 64, 474, 1100, 60, 28);
  text(s, "Ngày " + data.report_date + "  |  CASIA-FASD · seed 42", 64, 559, 1100, 45, 25, c.gray);
}
{
  const s = base(2, local("DAC_TA_HE_THONG_NHAN_DIEN_KHUON_MAT_PAD_DEPTH_MAP.md", "KE_HOACH_THUC_HIEN_THEO_BUOI_HOC.md"));
  text(s, "PAD: người thật hay ảnh in / video replay?", 64, 148, 1140, 50, 31, c.teal, true);
  text(s, "Học cách đọc predicted depth có giảm ACER so với\nmean depth, với phần tăng chi phí nhỏ?", 64, 240, 1140, 113, 36, c.navy, true);
  table(s, [["Lượt 1", "Lượt 2", "Lượt 3", "Lượt 4"], ["Câu hỏi\nnghiên cứu", "Protocol\nvà E0", "Pseudo-depth\nvà E1", "Frozen head E2\nvà so sánh"]], 64, 403, [288, 288, 288, 288], 166, 27);
  foot(s, "Phạm vi hiện tại: RGB PAD cho print/replay; nhận diện danh tính là phần mở rộng");
}
{
  const s = base(3, [data.references.survey, data.references.vit]);
  table(s, [["Hướng", "Cơ chế", "Liên hệ với nhóm"], ["Phân loại RGB", "CNN → live / attack", "E0: MobileNetV3"], ["Giám sát cục bộ", "Depth hoặc pixel map", "E1: pseudo-depth"], ["Toán tử / fusion", "CDC, attention, đa tỉ lệ", "CDCN; nghiên cứu mở rộng"], ["Transformer / domain", "Biểu diễn và tổng quát hóa", "Hướng liên quan, chưa chạy"]], 64, 159, [300, 420, 432], 371, 26);
  text(s, "Nhóm chọn depth-supervised CDCN để kiểm tra một thay đổi có thể cô lập", 64, 568, 1140, 64, 28, c.teal, true);
  foot(s, "Các hướng có thể kết hợp; bảng này không xếp hạng SOTA", 660);
}
{
  const s = base(4, [data.references.cdcn, data.references.code, data.references.dccdn, data.references.ucdcn, data.references.sca]);
  table(s, [["Công trình", "Ý tưởng liên quan", "Đã làm trong nhóm"], ["CDCN · 2020", "CDC + depth supervision", "E1: topology / loss"], ["CDCN++ · 2020", "Backbone tìm kiếm + attention", "Chưa tái lập"], ["DC-CDN · 2021", "Hai hướng cross-CDC + CFIM", "Chưa tái lập"], ["UCDCN · 2024", "Nested network + depth classifier", "Tiền lệ gần learned head"], ["SCA-DS · 2025", "Attention + depth supervision", "Đã đọc abstract"]], 64, 156, [270, 520, 362], 401, 24);
  text(s, "Đối chứng thực chạy: CDCN. Ý tưởng head có tiền lệ trong UCDCN", 64, 588, 1138, 63, 28, c.teal, true);
  foot(s, "So sánh nội bộ cùng điều kiện; chưa so trực tiếp số benchmark của paper", 663);
}
{
  const s = base(5, local("data/README.md", "src/deepface_pad/casia_fasd.py", e1nb, e2nb));
  table(s, [["Split", "Subject", "Video", "Frame"], ["Train", "16", "192", "3.840"], ["Validation", "4", "48", "960"], ["Test phát triển", "30", "360", "7.200"], ["Tổng", "50", "600", "12.000"]], 64, 158, [340, 240, 270, 302], 317, 27);
  lines(s, ["20 frame / video; split không trùng subject hoặc video", "Checkpoint + ngưỡng từ validation; score video = mean score frame"], 64, 507, 1140, 27, 65);
  foot(s, "Validation tự tách từ source train; CASIA test đã được quan sát ở lượt trước", 657);
}
{
  const s = base(6, local(e1nb, "src/deepface_pad/losses.py", "reports/MIDTERM_ROUNDS_1_3_AUDIT.md"));
  text(s, "Nhãn offline: live → 3DDFA V2; attack → zero map", 64, 146, 1152, 43, 28, c.teal, true);
  text(s, "CDCN nhận RGB và học dự đoán depth từ các nhãn này", 64, 207, 1152, 45, 28);
  text(s, "Hình thật: một frame validation từ Official E1", 64, 284, 1135, 36, 25, c.teal, true);
  await picture(s, depthCase, 64, 330, 1152, 307, "Validation RGB, pseudo-depth target, mask, predicted depth, histogram; casia_s14_v2_f000055");
  foot(s, "QA: 3.000 live + 9.000 attack frame; 3DDFA không chạy trong inference", 658);
}
{
  const s = base(7, local("src/deepface_pad/models/mobilenet_baseline.py", "configs/casia_e0_bce_5e.yaml", e0nb));
  const a = node(s, "RGB\n224 × 224", 64, 183, 235, 106);
  const b = node(s, "MobileNetV3-Small\nTiền huấn luyện", 346, 183, 391, 106);
  const d = node(s, "1 logit\n→ sigmoid score", 787, 183, 429, 106);
  arrow(s, a, b); arrow(s, b, d);
  lines(s, ["Train: BCEWithLogits · 5 epoch · best epoch 5", "Preprocessing: 224 × 224 · ImageNet normalization", "Vai trò: baseline RGB tham khảo và kiểm tra pipeline"], 64, 351, 1140, 29, 78);
  foot(s, "E0–E1 khác kiến trúc, loss và preprocessing; chưa cô lập tác dụng của depth");
}
{
  const s = base(8, local("src/deepface_pad/models/cdcn_official.py", "configs/casia_e1_cdcn_official.yaml", e1nb));
  const a = node(s, "RGB\n256 × 256", 64, 163, 219, 90);
  const b = node(s, "Official CDCN\nBa tỉ lệ đặc trưng", 330, 163, 384, 90);
  const d = node(s, "Depth 32 × 32\n→ mean score", 763, 163, 453, 90);
  arrow(s, a, b); arrow(s, b, d);
  text(s, "73 tensor khớp · max_abs_error = 0", 64, 303, 1140, 54, 35, c.teal, true);
  lines(s, ["Loss: absolute MSE + contrastive depth MSE", "Train 30 epoch; best epoch 25 từ validation", "Giữ topology / loss; CASIA + 3DDFA + scorer theo nhóm"], 64, 391, 1140, 27, 67);
  foot(s, "Tái lập kiến trúc/loss trong điều kiện nhóm; chưa tái lập số benchmark paper");
}
{
  const s = base(9, local("configs/casia_e2_official_head_frozen.yaml", "src/deepface_pad/models/cdcn_depth_head.py", "src/deepface_pad/models/depth_head.py", e2nb));
  const a = node(s, "RGB\n256 × 256", 64, 153, 217, 95);
  const b = node(s, "Checkpoint E1\nKhóa weights + BN", 328, 153, 394, 95);
  const d = node(s, "Depth không đổi\n1 × 32 × 32", 771, 153, 445, 95);
  arrow(s, a, b); arrow(s, b, d);
  text(s, "Head đọc predicted depth", 64, 300, 1110, 43, 30, c.purple, true);
  const nodes = [node(s, "Conv 1 → 8\n3 × 3 + ReLU", 64, 365, 237, 99, c.purple), node(s, "Conv 8 → 16\n3 × 3 + ReLU", 346, 365, 243, 99, c.purple), node(s, "Global average\npooling", 635, 365, 262, 99, c.purple), node(s, "Linear 16 → 1\n+ sigmoid", 942, 365, 274, 99, c.purple)];
  nodes.slice(1).forEach((n, i) => arrow(s, nodes[i], n, "right", "left", c.purple));
  text(s, "+1.265 tham số · BCE · Adam 0,001 · tối đa 10 epoch", 64, 512, 1136, 64, 29, c.teal, true);
  foot(s, "Cùng manifest / preprocessing / aggregation với E1; chỉ thay cách đọc depth");
}
{
  const s = base(10, local(e0nb, e1nb, e2nb, "reports/CASIA_E2_OFFICIAL_HEAD_FROZEN_seed42_summary.md"));
  const values = [["Model", "APCER ↓", "BPCER ↓", "ACER ↓", "EER ↓", "AUC ↑"]];
  data.results.forEach(r => values.push([r.id + " · " + (r.id === "E0" ? "RGB" : r.id === "E1" ? "mean" : "head"), r.apcer.toFixed(4) + "%", r.bpcer.toFixed(4) + "%", r.acer.toFixed(4) + "%", r.eer.toFixed(4) + "%", r.auc.toFixed(6)]));
  table(s, values, 64, 167, [232, 184, 184, 184, 184, 184], 277, 25, [2, 3]);
  text(s, "E1 ↔ E2: ACER = 2,7778%; cùng năm live video sai", 64, 490, 1140, 60, 33, c.teal, true);
  text(s, "E0 tham khảo: AUC cao hơn; ACER tại ngưỡng khóa cao hơn", 64, 565, 1140, 55, 27);
  foot(s, "Video-level · seed 42 · ngưỡng từ validation · CASIA development test", 658);
}
{
  const s = base(11, local(e2nb));
  await picture(s, e2Curve, 64, 165, 753, 420, "Original E2 head-only training BCE curve; best validation epoch 1");
  text(s, "Best epoch 1", 857, 192, 359, 50, 33, c.teal, true);
  lines(s, ["Chọn bằng val BCE", "Train BCE gần 0", "Val BCE tăng / dao động", "Head học được score;\nchưa cải thiện ACER"], 857, 267, 359, 26, 73);
  foot(s, "Loss curve không chứng minh ACER ở các epoch sau tăng; không chọn epoch bằng test", 658);
}
{
  const s = base(12, local(e1nb, e2nb));
  text(s, "355 cùng đúng  ·  5 cùng sai  ·  0 sửa lỗi  ·  0 lỗi mới", 64, 156, 1152, 53, 31, c.teal, true);
  table(s, [["Video live cùng sai", "Quality", "E1 score", "E2 score"], ...data.false_rejected_videos.map(r => [r.video, r.quality, r.e1.toFixed(6), r.e2.toFixed(6)])], 64, 246, [453, 215, 242, 242], 308, 24);
  text(s, "Ngưỡng: E1 = 0,191604; E2 = 0,411779", 64, 586, 1135, 47, 27);
  foot(s, "Có high / normal / low; cần xem map của đúng năm video để xác định nguyên nhân", 658);
}
{
  const s = base(13, local(e2nb));
  const values = [["Model", "Tham số", "p50 (ms)", "p95 (ms)", "FPS từ p50"], ...data.efficiency.map(r => [r.id, r.parameters.toLocaleString("en-US"), r.p50_ms.toFixed(3), r.p95_ms.toFixed(3), r.fps.toFixed(2)])];
  table(s, values, 64, 177, [160, 302, 230, 230, 230], 220, 27);
  text(s, "+1.265 tham số = +0,05635%", 64, 443, 1152, 60, 36, c.teal, true);
  text(s, "Latency là phép đo sơ bộ; chưa kết luận E2 nhanh hơn", 64, 531, 1152, 65, 29, c.orange, true);
  foot(s, "A100 40 GB · RGB 256 · batch 1 · forward-only · 10 warmup + 50 lượt; đo E1 rồi E2", 658);
}
{
  const s = base(14, local("KE_HOACH_THUC_HIEN_THEO_BUOI_HOC.md", "reports/CASIA_E2_OFFICIAL_HEAD_FROZEN_seed42_summary.md"));
  text(s, "Giới hạn hiện tại", 64, 157, 534, 45, 31, c.teal, true);
  lines(s, ["Một seed; CASIA development", "Test đã được quan sát", "Chưa có xác nhận độc lập", "Chưa thử backbone mới hơn"], 64, 229, 534, 27, 74);
  text(s, "Thí nghiệm tiếp theo", 681, 157, 535, 45, 31, c.teal, true);
  lines(s, ["E3: joint backbone + head", "E4: staged / Focal theo plan", "Xem lỗi; chạy nhiều seed", "Benchmark độc lập; đo lặp"], 681, 229, 535, 27, 74);
  foot(s, "E3/E4 chưa có kết quả benchmark; chưa tuyên bố novelty hay SOTA");
}
{
  const s = base(15, local("reports/CASIA_E2_OFFICIAL_HEAD_FROZEN_seed42_summary.md"));
  text(s, "Đã có đối chứng và một thí nghiệm cải tiến có kiểm soát", 64, 160, 1152, 99, 39, c.teal, true);
  text(s, "Frozen head E2 chưa cải thiện E1", 64, 317, 1152, 66, 42, c.navy, true);
  text(s, "ACER 2,7778%  ·  cùng năm lỗi live  ·  +1.265 tham số", 64, 426, 1152, 67, 31);
  text(s, "Bước kế tiếp: joint training và kiểm tra độ ổn định", 64, 549, 1152, 66, 31, c.teal);
}
{
  const s = base(16, local("src/deepface_pad/metrics.py", e2nb));
  table(s, [["Metric", "Ý nghĩa"], ["APCER", "Attack bị chấp nhận thành live / tổng attack"], ["BPCER", "Live bị từ chối thành attack / tổng live"], ["ACER", "(APCER + BPCER) / 2"], ["EER", "Điểm hai loại lỗi bằng nhau"], ["AUC", "Chất lượng thứ hạng trên ROC qua ngưỡng"]], 64, 157, [260, 892], 376, 26);
  text(s, "Ví dụ E1/E2: APCER = 0/270; BPCER = 5/90; ACER = 2,7778%", 64, 565, 1152, 65, 27, c.teal, true);
  foot(s, "ACER dùng ngưỡng validation đã khóa; EER/AUC không dùng để sửa ngưỡng test", 658);
}
{
  const s = base(17, local(e2nb));
  await picture(s, scoreDistribution, 64, 157, 1152, 443, "Original E1 mean-depth versus E2 sigmoid score histograms with validation thresholds");
  foot(s, "Thang điểm khác nhau; phân bố gần 0/1 không tự chứng minh phân biệt tốt hơn", 642);
}
{
  const s = base(18, local(e1nb));
  await picture(s, e0e1Curve, 64, 158, 1152, 405, "Original E0 and Official E1 training curves, best epochs 5 and 25");
  text(s, "E0: BCE · best epoch 5       E1: depth loss · best epoch 25", 64, 585, 1152, 44, 28, c.teal, true);
  foot(s, "Loss khác loại và khác thang; không so độ lớn loss để xếp hạng model", 656);
}
{
  const file = path.join(root, "diagrams/Sơ đồ kiến trúc MobileNetV3-Small.png");
  const s = base(19, [file, ...local("src/deepface_pad/models/mobilenet_baseline.py")]);
  await picture(s, file, 65, 142, 594, 527, "User-supplied full MobileNetV3-Small architecture diagram");
  text(s, "Output E0 thực chạy", 729, 178, 487, 50, 31, c.teal, true);
  lines(s, ["FC cuối → 1 logit", "BCEWithLogits khi train", "Sigmoid khi chấm điểm", "Softmax trong sơ đồ là\noutput phân loại tổng quát"], 729, 268, 487, 28, 82);
}
{
  const file = path.join(root, "diagrams/Sơ đồ kiến trúc CDCN đa tỉ lệ.png");
  const s = base(20, [file, ...local("src/deepface_pad/models/cdcn_official.py")]);
  await picture(s, file, 64, 139, 1152, 497, "User-supplied full Official CDCN multiscale architecture diagram");
  foot(s, "ReLU depth không chặn tại 1; resize về 32×32; mặt/map trong sơ đồ chỉ minh họa", 658);
}
{
  const file = path.join(root, "diagrams/Kiến trúc CDCN cải tiến với Learned Depth Head.png");
  const s = base(21, [file, ...local("src/deepface_pad/models/cdcn_depth_head.py", "src/deepface_pad/models/depth_head.py")]);
  await picture(s, file, 64, 139, 1152, 497, "User-supplied full Official CDCN plus learned depth head architecture diagram");
  foot(s, "E2: khóa cả weights và BN; chỉ học head. Mặt/map trong sơ đồ là minh họa", 658);
}
{
  const s = base(22, Object.values(data.references));
  table(s, [["Nguồn", "Nội dung đã dùng"], ["CDCN / CDCN++ · CVPR 2020", "Kiến trúc, loss và mã tác giả"], ["DC-CDN · IJCAI 2021", "Cross-CDC và feature interaction"], ["UCDCN · 2024", "Tiền lệ depth classifier / staged training"], ["SCA-DS · 2025", "Attention + depth supervision (abstract)"], ["Output notebook E0 / E1 / E2", "Metric, curve, kiểm tra backbone và lỗi"]], 64, 157, [488, 664], 380, 25);
  text(s, "Run E2: CASIA_E2_CDCN_OFFICIAL_HEAD_FROZEN\nseed42_20261001T155213Z", 64, 565, 1152, 70, 25, c.teal);
  foot(s, "Link paper và nguồn từng slide trong Notes; raw Drive artifacts chưa kiểm toán độc lập", 658);
}

if (presentation.slides.items.length !== data.total_slides) throw new Error("Unexpected slide count");
for (const b of bounds) if (b.x < 0 || b.y < 0 || b.x + b.w > 1280.1 || b.y + b.h > 720.1) throw new Error("Out of canvas: " + JSON.stringify(b));
await fs.writeFile(path.join(build, "authored-bounds.json"), JSON.stringify(bounds, null, 2));
const guide = ["# Lời thuyết trình Lượt 1–4", "", data.authors.join(" — "), "", "15 slide chính khoảng 13 phút; từ slide 16 là phụ lục. Khi báo cáo ngắn, lướt slide 3–4 và đi thẳng phần E1–E2. Đọc Notes trong PowerPoint để xem nguồn từng slide.", "", ...data.slides.flatMap(s => ["## Slide " + s.id + ": " + s.title, "", s.time_seconds ? "Thời lượng gợi ý: " + s.time_seconds + " giây." : "Phụ lục — mở khi cần trả lời câu hỏi.", "", s.notes, ""])].join("\n");
await fs.writeFile(path.join(output, "Loi_thuyet_trinh_Luot_1_4.md"), guide);
const candidate = path.join(build, "candidate.pptx");
await (await PresentationFile.exportPptx(presentation)).save(candidate);
console.log("Exported candidate", candidate);
for (let i = 0; i < presentation.slides.items.length; i++) {
  const slide = presentation.slides.items[i];
  const png = await presentation.export({ slide, format: "png", scale: 1.5 });
  await fs.writeFile(path.join(build, "slide-" + String(i + 1).padStart(2, "0") + ".png"), new Uint8Array(await png.arrayBuffer()));
  const layout = await slide.export({ format: "layout" });
  await fs.writeFile(path.join(build, "slide-" + (i + 1) + ".layout.json"), await layout.text());
  console.log("Rendered slide", i + 1);
}
const tableOwners = [2, 3, 4, 5, 10, 12, 13, 16, 22];
await finalizePresentation({
  workspaceDir: root, candidatePath: candidate, finalPath,
  pythonExecutable: process.env.RUNTIME_PYTHON,
  integrityValidatorPath: path.join(skill, "container_tools/inspect_presentation_package_integrity.py"),
  layoutValidatorPath: path.join(skill, "container_tools/inspect_presentation_layout_geometry.py"),
  layoutArgs: ["--expected-slide-size-emu", "12192000,6858000", "--validate-heading-fit", ...tableOwners.flatMap(n => ["--require-native-table-slide", String(n)])],
  explicitTotalSlideCount: data.total_slides,
  requiredNativeTableOwnerSlides: tableOwners,
  fontPolicy: { basis: "design", families: [font] },
  verifyArtifactToolImport: true,
  receiptPath: path.join(build, path.basename(finalPath, ".pptx") + ".validation.json"),
});
console.log("Final presentation", finalPath);
