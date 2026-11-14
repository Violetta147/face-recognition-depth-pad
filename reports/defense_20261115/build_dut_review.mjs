import fs from "node:fs/promises";
import path from "node:path";
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";

// Run from the repository root with the Codex bundled Node runtime.
// Builds the HTML review and PNG previews for content approval.
const runtime = path.join(process.env.USERPROFILE, ".cache/codex-runtimes/codex-primary-runtime/dependencies");
const { Presentation } = await import(pathToFileURL(path.join(runtime,
  "node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs")));
const output = path.resolve("outputs/defense_20261115/Duyệt slide DUT v3");
const assets = "reports/slides_round5/assets";
const W = 1280, H = 720, LEFT = 69, WIDTH = 1142;
const blue = "#0C5284", ink = "#173349", soft = "#3F5667", yellow = "#FFE300";
const dataColor = "#087789", caution = "#875611";
const deck = Presentation.create({ slideSize: { width: W, height: H } });
const records = [];
const modelNames = {
  E0: "MobileNetV3-Small trên ảnh RGB",
  E1: "CDCN lấy trung bình độ sâu",
  E2: "CDCN chỉ huấn luyện nhánh phân loại",
  E3: "CDCN huấn luyện đồng thời với BCE",
  E3b: "CDCN huấn luyện ba giai đoạn với BCE",
  E4: "CDCN huấn luyện ba giai đoạn với Focal",
};
const { E0: mobileNet, E1: meanDepth, E2: frozenHead, E3: jointBce, E3b: stagedBce, E4: stagedFocal } = modelNames;
const modelTableTitle = "Tên các cấu hình thực nghiệm";
const modelCodePattern = /\bE(?:3b|[0-4])\b/;
function checkSlideText(s, value) {
  if (records.at(-1)?.title !== modelTableTitle) {
    assert.doesNotMatch(value, modelCodePattern, `Mã mô hình xuất hiện ở slide ${deck.slides.items.indexOf(s) + 1}`);
  }
}
const backgrounds = {};
for (const key of ["cover", "content", "closing"]) {
  backgrounds[key] = await fs.readFile(path.join(assets, `dut-${key}.png`));
}

function box(s, value, x, y, w, h, size, color = ink, bold = false, alignment = "left") {
  checkSlideText(s, value);
  const b = s.shapes.add({ name: value.slice(0, 54), geometry: "textbox",
    position: { left: x, top: y, width: w, height: h }, fill: "none", line: { fill: "none", width: 0 } });
  b.text = value;
  b.text.style = { fontFamily: "Arial", fontSize: size, color, bold, alignment,
    verticalAlignment: "middle", wrap: "wrap", insets: { left: 0, right: 0, top: 0, bottom: 0 } };
  return b;
}

function emphasize(shape, phrases, color) {
  for (const phrase of phrases) {
    const range = shape.text.get(phrase);
    range.bold = true;
    if (color) range.fill = color;
  }
}

function highlight(s, value, y, color = blue) {
  s.shapes.add({ name: "Nền nhấn kết quả", geometry: "rect",
    position: { left: LEFT, top: y, width: WIDTH, height: 56 },
    fill: color === caution ? "#FFF2CC" : "#E7F2FA", line: { fill: "none", width: 0 } });
  return box(s, value, LEFT + 16, y + 3, WIDTH - 32, 50, 23, color, true);
}

function marker(s, x, y, width) {
  const height = 24;
  const edge = [[0, 5], [24, 2], [width * 0.33, 3], [width * 0.72, 1],
    [width - 9, 3], [width, 9], [width - 4, 15], [width, 20],
    [width * 0.67, 22], [width * 0.27, 21], [7, 24], [2, 18], [4, 10]];
  s.shapes.add({ name: "Vệt bút dạ quang", geometry: "custom",
    position: { left: x, top: y, width, height }, fill: "rgba(255, 220, 48, 0.58)",
    line: { fill: "none", width: 0 },
    customPaths: [{ width, height, commands: [
      { moveTo: { x: edge[0][0], y: edge[0][1] } },
      ...edge.slice(1).map(([x, y]) => ({ lineTo: { x, y } })),
      { close: {} },
    ] }],
  });
}

async function evidence(s, name, x, y, w, h, alt) {
  const blob = await fs.readFile(path.join("reports/round8_documents_20261023/assets", name));
  s.images.add({ blob, contentType: "image/png", fit: "contain",
    position: { left: x, top: y, width: w, height: h }, alt });
}

function newSlide(title, source, kind = "content") {
  const s = deck.slides.add();
  records.push({ title, source });
  checkSlideText(s, [title, source].join("\n"));
  s.images.add({ blob: backgrounds[kind], contentType: "image/png", fit: "cover",
    position: { left: 0, top: 0, width: W, height: H }, alt: "Nền từ template DUT" });
  if (kind === "content") {
    box(s, title, LEFT, 40, WIDTH, 87, 40, blue, true);
    box(s, String(deck.slides.items.length).padStart(2, "0"), 1010, 663, 65, 22, 17, blue, true);
  }
  return s;
}

function list(s, entries, { top = 151, step = 118, label = 245 } = {}) {
  entries.forEach(([key, value], i) => {
    box(s, key, LEFT, top + i * step, label, 72, 27, blue, true);
    box(s, value, LEFT + label + 23, top + i * step, WIDTH - label - 23, 82, 27);
  });
}

function foot(s, value, y = 550) {
  box(s, value, LEFT, y, WIDTH - 66, 54, 21, soft, true);
}

function table(s, rows, widths, top, rh = 57, font = 24) {
  checkSlideText(s, rows.flat().join("\n"));
  const t = s.tables.add({ rows: rows.length, columns: widths.length, left: LEFT, top,
    width: widths.reduce((a,b) => a + b), height: rows.length * rh, columnWidths: widths, values: rows });
  t.styleOptions = { headerRow: false, bandedRows: false };
  t.borders.assign({ style: "solid", fill: "#C9D8E2", width: 1 });
  rows.forEach((row, i) => {
    t.rows[i].height = rh;
    row.forEach((_, j) => {
      const cell = t.getCell(i,j);
      cell.fill = i === 0 ? blue : i % 2 ? "#FFFFFF" : "#EAF3F9";
      cell.text.style = { fontFamily: "Arial", fontSize: font, color: i === 0 ? "#FFFFFF" : ink,
        bold: i === 0, verticalAlignment: "middle" };
    });
  });
}

const paper = "Paper_DG56.pdf trong hồ sơ Nhóm 01, Bảng kết quả CASIA-FASD.";
const firstReview = "Phiếu DG56 ngày 19/10/2026, trang 3: https://drive.google.com/file/d/1uQSb2sLuqopMp-Wgm4LKdq2HXc6NYdaV/view";
const secondReview = "Phiếu DG56 ngày 29/10/2026, trang 2: https://drive.google.com/file/d/1VDUiIyHXlhVXFrEa9pO4hiSfHQvF2nbz/view";
const review = firstReview + "\n" + secondReview;
const boot = "PHAN_TICH_DIEM_DA_KHOA.md và KHOANG_BOOTSTRAP.json.";
const oulu = "Hồ sơ Nhóm 01, Source Code/Kết quả/OULU và pair_dev_lock.json.";
const prnet = "CDCN_CVPR2020_OULU_P1.md và Source Code/Kết quả/PRNet Dev pilot.";

let s = newSlide("Chống tấn công giả mạo sinh trắc học khuôn mặt", paper, "cover");
box(s, "Chống tấn công giả mạo\nsinh trắc học khuôn mặt", 378, 146, 813, 173, 53, yellow, true);
box(s, "Thực nghiệm trên CASIA-FASD và OULU-NPU", 378, 319, 813, 59, 30, "#FFFFFF", true);
box(s, "Sinh viên: Nguyễn Hữu Minh Quân    MSSV: 102230208\nSinh viên: Trịnh Minh Đạt    MSSV: 102230180",
  378, 386, 813, 85, 26, "#FFFFFF", true);
box(s, "Nhóm 01 Deep-PAD · Học phần Thị giác máy tính", 378, 486, 813, 48, 22, "#FFFFFF", true);

s = newSlide("Hai cách tính score từ bản đồ độ sâu", paper + " Hình pipeline.png và validation-depth-case.png, hồ sơ Lượt 8.");
const question = box(s, "Đọc bản đồ độ sâu bằng nhánh phân loại có giảm lỗi ở cấp video so với cách lấy trung bình không?",
  LEFT, 126, WIDTH, 84, 31, ink, true);
emphasize(question, ["giảm lỗi ở cấp video"], blue);
const flow = [
  ["Ảnh khuôn mặt", "RGB", 69, 248, 220],
  ["Mạng CDCN", "Dự đoán độ sâu", 344, 248, 230],
  ["Bản đồ độ sâu", "32 × 32", 629, 248, 225],
  ["Score CDCN", "Lấy trung bình độ sâu", 909, 216, 302],
  ["Score từ đầu CNN", "Học cách đọc độ sâu", 909, 322, 302],
];
for (const [heading, detail, x, y, w] of flow) {
  s.shapes.add({ name: heading, geometry: "rect",
    position: { left: x, top: y, width: w, height: 80 },
    fill: "#E7F2FA", line: { fill: "#B9D4E5", width: 1 } });
  box(s, heading, x+6, y+9, w-12, 32, 25, blue, true, "center");
  box(s, detail, x+6, y+42, w-12, 26, 20, ink, false, "center");
}
for (const [x, y, arrow] of [[289, 249, "→"], [574, 249, "→"], [854, 232, "↗"], [854, 321, "↘"]]) {
  box(s, arrow, x, y, 55, 75, 34, blue, true, "center");
}
await evidence(s, "validation-depth-case.png", LEFT, 461, 576, 131,
  "Khung CASIA-FASD thật với bản đồ độ sâu tham chiếu và dự đoán");
box(s, "Score CDCN là giá trị trung bình của bản đồ độ sâu dự đoán 32 × 32.", 669, 466, 542, 73, 25, blue, true);
box(s, "Hình bên trái là ví dụ từ CASIA-FASD.", 669, 545, 542, 35, 19, soft);

s = newSlide("Thiết kế thực nghiệm trên CASIA-FASD", paper);
table(s, [["Train", "Validation", "Test"], ["16 người · 192 video", "4 người · 48 video", "30 người · 360 video"]], [365, 365, 412], 147, 61);
const methodLine = "Nhóm dùng MobileNetV3-Small trên ảnh RGB làm đối chứng. Với CDCN, nhóm so sánh hai cách tính điểm từ cùng bản đồ độ sâu.";
const rgbMethod = box(s, methodLine, LEFT, 300, WIDTH, 91, 28);
emphasize(rgbMethod, ["MobileNetV3-Small", "hai cách tính điểm"]);
const rgb = methodLine.indexOf("RGB");
["#B42318", "#127C45", "#1E55B3"].forEach((color, i) => {
  const letter = rgbMethod.text.getRange(rgb + i, 1);
  letter.fill = color;
  letter.bold = true;
});
const trainingMethod = box(s, "Với nhánh phân loại, nhóm thử huấn luyện đồng thời hoặc chia ba giai đoạn. Nhóm cũng so sánh hai hàm mất mát phân loại là BCE và Focal.", LEFT, 390, WIDTH, 111, 28);
emphasize(trainingMethod, ["huấn luyện đồng thời", "ba giai đoạn", "BCE", "Focal"]);
highlight(s, "Điểm mỗi video là trung bình 20 khung. Ngưỡng lấy từ validation.", 537);

s = newSlide(modelTableTitle, paper);
table(s, [["Mã trong bài", "Tên cấu hình", "Cách tính điểm hoặc huấn luyện"],
  ["E0", mobileNet, "Phân loại trực tiếp từ ảnh"],
  ["E1", meanDepth, "Lấy trung bình bản đồ độ sâu"],
  ["E2", frozenHead, "Giữ nguyên mạng dự đoán độ sâu"],
  ["E3", jointBce, "Cập nhật mạng độ sâu và nhánh phân loại cùng lúc"],
  ["E3b", stagedBce, "Học độ sâu, học phân loại, rồi tinh chỉnh cả hai"],
  ["E4", stagedFocal, "Cùng lịch ba giai đoạn, dùng Focal cho phân loại"]],
  [147, 440, 555], 142, 61, 21);

s = newSlide("Hai cách tính điểm cho cùng quyết định", paper + " Biểu đồ phân bố điểm, hồ sơ Lượt 8.");
table(s, [["Cấu hình", "Từ chối nhầm", "ACER"],
  [mobileNet, "10 trong 90", "5,56%"], ["Trung bình độ sâu\nChỉ học nhánh phân loại", "5 trong 90", "2,78%"],
  ["BCE đồng thời hoặc chia ba giai đoạn", "9 trong 90", "5,00%"], [stagedFocal, "8 trong 90", "4,44%"]],
  [313, 132, 88], 150, 59, 19);
await evidence(s, "e1-e2-score-histograms.png", 608, 158, 603, 300, "Phân bố điểm trên tập test ở seed 42");
s.shapes.add({ name: "Nền tiêu đề biểu đồ", geometry: "rect",
  position: { left: 608, top: 189, width: 603, height: 19 },
  fill: "#FFFFFF", line: { fill: "none", width: 0 } });
box(s, "Trung bình độ sâu", 642, 187, 275, 23, 15, ink, true, "center");
box(s, "Chỉ học nhánh phân loại", 936, 187, 269, 23, 15, ink, true, "center");
box(s, "Phân bố điểm trên tập test CASIA-FASD, seed 42", 614, 435, 578, 52, 20, soft);
box(s, "Cả 270 video tấn công đều bị chặn.", LEFT, 457, 515, 43, 20, soft);
box(s, "ACER lấy trung bình tỷ lệ tấn công lọt và tỷ lệ người thật bị từ chối.", LEFT, 492, WIDTH, 27, 19, soft);
highlight(s, "Lấy trung bình độ sâu và chỉ học nhánh phân loại cho cùng quyết định trên cả 360 video.", 530);

s = newSlide("Huấn luyện đồng thời cho kết quả khác nhau qua ba lượt", "ROUND_6_RESULTS_2026-10-22.md, bảng từng seed và thống kê ghép cặp.");
table(s, [["Seed", "Trung bình độ sâu", "BCE đồng thời", "Chênh lệch"],
  ["43", "6,67%", "3,33%", "−3,33 điểm %"],
  ["44", "2,41%", "4,44%", "+2,04 điểm %"],
  ["45", "3,89%", "3,33%", "−0,56 điểm %"]], [83, 210, 182, 199], 154, 70, 20);
const origin = 991;
box(s, "ACER so với cách lấy trung bình độ sâu", 771, 151, 440, 48, 20, blue, true, "center");
s.shapes.add({ name: "Mốc không chênh lệch", geometry: "rect",
  position: { left: origin, top: 219, width: 2, height: 200 },
  fill: "#6B879B", line: { fill: "none", width: 0 } });
for (const [i, delta] of [-3.33, 2.04, -0.56].entries()) {
  const width = Math.abs(delta) * 47;
  s.shapes.add({ name: "Chênh lệch ở seed " + (43 + i), geometry: "rect",
    position: { left: delta < 0 ? origin - width : origin, top: 248 + i*67, width, height: 24 },
    fill: delta < 0 ? dataColor : caution, line: { fill: "none", width: 0 } });
}
box(s, "Giảm lỗi", 789, 416, 182, 38, 18, dataColor, true, "right");
box(s, "0", 973, 416, 36, 38, 18, soft, false, "center");
box(s, "Tăng lỗi", 1013, 416, 170, 38, 18, caution, true);
foot(s, "Chênh lệch trung bình ± độ lệch chuẩn là −0,62 ± 2,69 điểm phần trăm.", 459);
highlight(s, "Huấn luyện đồng thời với BCE giảm lỗi ở hai lượt và tăng lỗi ở lượt còn lại.", 533, caution);

s = newSlide("Giải trình DG56 về ngưỡng và đối chứng", review + "\n" + boot);
table(s, [["Góp ý", "Nhóm đã kiểm", "Còn mở"],
  ["Ngưỡng và sai số", "Một video thật làm tỷ lệ từ chối nhầm ở tập validation đổi 8,33 điểm %.", "Kiểm định chéo 5 phần, chia theo người"],
  ["Khoảng bất định", "Lấy mẫu lại theo người 20.000 lần.", "Lặp lịch ba giai đoạn với BCE và Focal"],
  ["Nhánh phân loại", "Hai cách tính điểm xếp ngược thứ tự ở 863 trong 64.620 cặp video.", "Thử kết hợp điểm và so sánh với cùng số lượt cập nhật"]],
  [241, 527, 374], 146, 83, 23);
highlight(s, "CDCN lấy trung bình độ sâu có ACER 2,78%. Khoảng bootstrap 95% là 0,56–5,00%.", 530);
const reviewSource = box(s, "Nguồn: Phiếu DG56 ngày 19/10, trang 3 và phiếu ngày 29/10, trang 2.",
  LEFT, 588, WIDTH - 100, 28, 17, soft);
reviewSource.text.get("Phiếu DG56 ngày 19/10").link = {
  uri: "https://drive.google.com/file/d/1uQSb2sLuqopMp-Wgm4LKdq2HXc6NYdaV/view", isExternal: true
};
reviewSource.text.get("phiếu ngày 29/10").link = {
  uri: "https://drive.google.com/file/d/1VDUiIyHXlhVXFrEa9pO4hiSfHQvF2nbz/view", isExternal: true
};

s = newSlide("Giải trình DG56 về dữ liệu đánh giá", secondReview + "\n" + oulu);
box(s, "Tiêu chí 1 · Tính mới và hàm lượng khoa học", LEFT, 119, WIDTH, 34, 24, blue, true);
marker(s, 86, 226, 775);
const novelty = box(s, [
  "“Câu hỏi nghiên cứu hẹp nhưng rõ (cách tính điểm từ bản đồ độ sâu CDCN) và được trả lời bằng thực nghiệm",
  "có kiểm soát; kết luận là đầu phân loại học được không vượt trung bình bản đồ – kết quả âm có giá trị nhưng",
  "tính mới thấp. Khoảng cách tới paper:",
  "kiểm chứng trong kịch bản khó hơn (chéo tập) nơi khác biệt có thể xuất hiện.”",
].join("\n"), 89, 151, 1117, 104, 21);
emphasize(novelty, ["kiểm chứng trong kịch bản khó hơn (chéo tập) nơi khác biệt có thể xuất hiện"]);

marker(s, 624, 275, 79);
box(s, "Tiêu chí 2 · Loại đóng góp kỹ thuật và đóng góp dữ liệu", LEFT, 270, WIDTH, 34, 24, blue, true);
marker(s, 191, 312, 115);
const contribution = box(s, "“Không có dữ liệu mới (CASIA-FASD bản Kaggle); manifest và mã băm hỗ trợ tái lập.”",
  89, 305, 1117, 38, 21);
emphasize(contribution, ["dữ liệu mới"]);

marker(s, 198, 362, 86);
box(s, "Tiêu chí 3 · Dữ liệu", LEFT, 357, WIDTH, 34, 24, blue, true);
marker(s, 183, 395, 238);
marker(s, 366, 421, 261);
const dataset = box(s, [
  "“Hạn chế: CASIA-FASD nhỏ và cũ, đã bão hòa (AUC > 0,99); validation chỉ 4 người/12 video live",
  "nên ngưỡng bị lượng tử hóa; không có tập ngoài miền.”",
].join("\n"), 89, 389, 1117, 60, 21);
emphasize(dataset, ["CASIA-FASD nhỏ và cũ", "không có tập ngoài miền"]);
const citation = box(s, "Phiếu nhận xét DG56 ngày 29/10/2026, trang 2, tiêu chí 1–3", LEFT, 470, WIDTH, 32, 18, soft);
citation.text.get("Phiếu nhận xét DG56 ngày 29/10/2026").link = {
  uri: "https://drive.google.com/file/d/1VDUiIyHXlhVXFrEa9pO4hiSfHQvF2nbz/view", isExternal: true
};
highlight(s, "Nhóm đã bổ sung OULU-NPU Protocol 1. Đánh giá chéo tập vẫn còn mở.", 535);

s = newSlide("Thiết kế thực nghiệm OULU-NPU Protocol 1", "docs/OULU_NPU.md, bảng Protocol 1. " + oulu);
table(s, [["Tập", "Người", "Tổng video", "Video thật", "Video tấn công", "Phiên quay"],
  ["Train", "20", "1.200", "240", "960", "1 và 2"],
  ["Dev", "15", "900", "180", "720", "1 và 2"],
  ["Test", "20", "600", "120", "480", "3"]],
  [140, 131, 208, 192, 245, 226], 145, 59);
const setting = box(s, "Nhóm so sánh cách lấy trung bình độ sâu với huấn luyện đồng thời bằng BCE. Hai cấu hình dùng cùng trọng số ban đầu và được cập nhật thêm 3.000 lần.",
  LEFT, 404, WIDTH, 91, 25);
emphasize(setting, ["cùng trọng số ban đầu", "3.000 lần"]);
highlight(s, "Điểm video lấy trung bình 8 khung. Checkpoint và ngưỡng chọn trên Dev.", 522);

s = newSlide("Đối chứng trên OULU-NPU Protocol 1", oulu);
table(s, [["Cấu hình", "APCER", "BPCER", "ACER"],
  [mobileNet, "0,83%", "31,67%", "16,25%"],
  [meanDepth, "2,50%", "24,17%", "13,33%"],
  [jointBce, "3,33%", "10,83%", "7,08%"]], [530, 204, 204, 204], 153, 65);
box(s, "Khi huấn luyện đồng thời với BCE, số video thật bị từ chối giảm từ 29 xuống 13 trên tổng số 120 video thật.", LEFT, 422, WIDTH, 61, 24);
foot(s, "Tập test có 600 video, seed 43. APCER lấy tỷ lệ tấn công lọt cao hơn giữa ảnh in và video phát lại.", 479);
highlight(s, "So với lấy trung bình độ sâu, ACER giảm 6,25 điểm phần trăm và APCER tăng lên 3,33%.", 550, caution);

s = newSlide("Tiến độ tái lập CDCN với PRNet", prnet + " Yu và cộng sự, CVPR 2020, Bảng 4.");
list(s, [["Lượt đã chạy", "40 video Train, 30 video Dev. Đã kiểm luồng chuẩn bị, huấn luyện và chấm điểm."],
  ["Mẫu Dev", "ACER gộp 27,08% sau 10 epoch. Kết quả giới hạn ở mẫu 30 video."],
  ["Tập đầy đủ", "Đang dừng ở bước dựng dữ liệu PRNet. Chưa có kết quả Test để đối chiếu mốc 1,0%."]]);

highlight(s, "Bước tiếp theo là chốt checkpoint và ngưỡng trên Dev đầy đủ trước khi chấm Test.", 540);

s = newSlide("Trao đổi", "Hồ sơ Nhóm 01 Deep-PAD.", "closing");
box(s, "Cảm ơn thầy và các bạn", 95, 234, 805, 98, 57, "#FFFFFF", true);
box(s, "Nhóm 01 Deep-PAD", 98, 363, 680, 53, 33, yellow, true);

await fs.mkdir(output, { recursive: true });
await fs.mkdir(path.join(output, "ảnh"), { recursive: true });
for (const [i, slide] of deck.slides.items.entries()) {
  const blob = await deck.export({ slide, format: "png", scale: 1 });
  const name = `slide-${String(i+1).padStart(2, "0")}.png`;
  await fs.writeFile(path.join(output, "ảnh", name), new Uint8Array(await blob.arrayBuffer()));
  records[i].file = name;
}
const encoded = JSON.stringify(records).replaceAll("<", "\\u003c");
const driveLinkPattern = /(https:\/\/drive\.google\.com\/file\/d\/[A-Za-z0-9_-]+\/view)/;
await fs.writeFile(path.join(output, "Xem slide DUT.html"), `<!doctype html>
<html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Duyệt slide DUT · Nhóm 01 Deep-PAD</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#eef3f7;color:#173349;font:16px Arial,sans-serif}
main{max-width:1340px;margin:0 auto;padding:20px}header{display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;margin-bottom:12px}
h1{font-size:21px;margin:0}button,select{font:inherit;padding:7px 10px;background:white;color:#173349;border:1px solid #9fb0bc;border-radius:4px}
button:disabled{opacity:.45}img{display:block;width:100%;aspect-ratio:16/9;object-fit:contain;background:#0c5284}details{background:white;padding:14px 18px;margin-top:12px}
summary{font-weight:bold;cursor:pointer}p{line-height:1.5}small{color:#3f5667;white-space:pre-line}a{color:#0c5284}:focus-visible{outline:3px solid #117aba}
</style>
<main><header><h1>Bản duyệt slide DUT · Nhóm 01</h1><nav>
<button id="prev" type="button" aria-label="Slide trước">←</button>
<select id="jump" aria-label="Chọn slide"></select>
<button id="next" type="button" aria-label="Slide sau">→</button>
</nav></header>
<img id="preview" alt=""><details open><summary>Nguồn</summary><small id="source"></small></details></main>
<script>
const rows=${encoded};const jump=document.querySelector('#jump'),prev=document.querySelector('#prev'),next=document.querySelector('#next'),preview=document.querySelector('#preview'),source=document.querySelector('#source');
let index=0;
rows.forEach((row,i)=>jump.add(new Option((i+1)+' / '+rows.length+' · '+row.title,i)));
function showSource(value) {
  source.replaceChildren();
  for (const part of value.split(${driveLinkPattern})) {
    if (part.startsWith('https://drive.google.com/')) {
      const link=document.createElement('a');
      link.href=part;
      link.target='_blank';
      link.rel='noopener';
      link.textContent='Mở phiếu nhận xét';
      source.append(link);
    } else {
      source.append(part);
    }
  }
}
function show(i){index=Math.min(rows.length-1,Math.max(i,0));const row=rows[index];jump.value=index;preview.src='ảnh/'+row.file;preview.alt=row.title;showSource(row.source);prev.disabled=index===0;next.disabled=index===rows.length-1}
prev.onclick=()=>show(index-1);next.onclick=()=>show(index+1);jump.onchange=()=>show(Number(jump.value));
window.addEventListener('keydown',e=>{if(e.target===jump)return;if(e.key==='ArrowLeft')show(index-1);if(e.key==='ArrowRight')show(index+1)});show(0);
</script></html>`, "utf8");
console.log(`Rendered ${records.length} DUT review slides in ${output}`);
