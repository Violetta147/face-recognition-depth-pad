"""Build the Colab A100 notebook for the matched OULU E1/E3 pair."""
from build_oulu_colab import ROOT, SOURCES, build_notebook
from build_oulu_e1_colab import CELLS as E1_CELLS

CELLS = [
    ("markdown", """# OULU-NPU Protocol 1 · Đối chứng E1–E3, seed 43
Chọn A100. Chạy cell 1–5 theo thứ tự. Nếu runtime E1 còn mở, chép các cell code vào notebook đang mở để dùng lại dữ liệu cục bộ. Cả hai nhánh nạp cùng checkpoint E1 và thêm 5 epoch × 600 bước với Adam mới. E1 tiếp tục học độ sâu. E3 thêm đầu phân loại và BCE, hệ số 1, đồng thời cập nhật backbone. Hai nhánh dùng cùng thứ tự mẫu, batch 16, BF16 và tiêu chí chọn checkpoint từ Dev."""),
    ("code", E1_CELLS[1][1].replace('RESULTS = BASE / "cdcn-e1-p1"',
                                   'RESULTS = BASE / "cdcn-pair-p1"')),
    E1_CELLS[2],
    ("code", '''#@title 3. Kiểm checkpoint E1 và ghi cấu hình hai nhánh
import yaml
from deepface_pad.oulu_pair import BRANCHES, ARTIFACTS, pair_config
from deepface_pad.progress import run_logged

STARTER = (BASE / "cdcn-e1-p1/runs" / "OULU_P1_E1_CDCN_seed43_20261114T142652Z")
RESUME_PAIR = ""  # Khi đổi runtime, điền đường dẫn từ PAIR_CONFIG_READY.
PAIR = Path(RESUME_PAIR) if RESUME_PAIR else RESULTS / f"seed43-{time.time_ns()}"
configs = {branch: pair_config(ROOT, STARTER, PAIR / "runs", DEPTH_SHA, branch) for branch in BRANCHES}
if RESUME_PAIR:
    assert PAIR.is_dir()
else:
    PAIR.mkdir(parents=True, exist_ok=False)
for branch, config in configs.items():
    path = PAIR / f"{branch}.yaml"
    if RESUME_PAIR:
        assert yaml.safe_load(path.read_text(encoding="utf-8")) == config
    else:
        path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
print("PAIR_CONFIG_READY", PAIR)
'''),
    ("code", '''#@title 4. Chạy hai nhánh lần lượt, lưu từng run hoàn tất
import pandas as pd

entrypoint = "import sys; from deepface_pad.train import run; print('RUN_DIR=' + str(run(sys.argv[1])))"
env = {**os.environ, "PYTHONPATH": str(WORK / "src"), "PYTHONUNBUFFERED": "1"}
for branch in BRANCHES:
    record = PAIR / f"{branch}-complete.json"
    if record.is_file():
        print("Already complete:", branch, flush=True)
        continue
    config_path = PAIR / f"{branch}.yaml"
    assert yaml.safe_load(config_path.read_text(encoding="utf-8")) == configs[branch]
    log = PAIR / f"{branch}-{time.time_ns()}.log"
    run_logged([sys.executable, "-u", "-c", entrypoint, config_path], label=branch, log=log, env=env)
    with log.open(encoding="utf-8") as handle:
        run_dir = Path(next(line.strip().split("=", 1)[1] for line in handle if line.startswith("RUN_DIR=")))
    history = pd.read_csv(run_dir / "train_log.csv")
    assert history.optimizer_steps.tolist() == [600] * 5
    expected = file_hash(STARTER / "best.ckpt")
    initial = json.loads((run_dir / "initial_checkpoint.json").read_text())
    assert initial["sha256"] == expected
    payload = {"run": str(run_dir), "sha256": {name: file_hash(run_dir / name) for name in
               (*ARTIFACTS, "initial_checkpoint.json", "val_scores.csv")}}
    temp = record.with_suffix(".tmp")
    temp.write_text(json.dumps(payload, indent=2))
    temp.replace(record)
'''),
    ("code", '''#@title 5. Khóa hai run và in kết quả Dev
runs = {}
metrics = {}
for branch in BRANCHES:
    runs[branch] = json.loads((PAIR / f"{branch}-complete.json").read_text())
    run_dir = Path(runs[branch]["run"])
    for name, digest in runs[branch]["sha256"].items():
        assert file_hash(run_dir / name) == digest, name
    metrics[branch] = json.loads((run_dir / "metrics.json").read_text())
lock = {"protocol": 1, "seed": 43, "optimizer_updates_per_branch": 3000, "runs": runs,
        "source_bundle_sha256": BUNDLE_SHA256, "depth_zip_sha256": DEPTH_SHA,
        "starter_sha256": file_hash(STARTER / "best.ckpt"), "dev_metrics": metrics}
path = PAIR / "pair_dev_lock.json"
data = json.dumps(lock, indent=2) + "\\n"
if path.is_file():
    assert path.read_text() == data, "Existing pair lock differs"
else:
    path.write_text(data, encoding="utf-8")
print(json.dumps(metrics, indent=2))
print("PAIR_DEV_READY", path, flush=True)
'''),
]

if __name__ == "__main__":
    build_notebook(CELLS, "Face_PAD_OULU_NPU_E1_E3_Pair.ipynb",
                   [*SOURCES, "oulu_depth_smoke", "oulu_depth_full", "oulu_e1", "oulu_pair"], gpu=True)
