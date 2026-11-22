import base64
import gzip
import io
import json
from pathlib import Path
import sys
import tarfile

import pytest
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import cdcn_prnet_dev_schedule as schedule
from cdcn_prnet_train_pilot import RECOVERY_FORMAT
sys.path.pop(0)


@pytest.fixture
def schedule_fixture(tmp_path, monkeypatch):
    assets, initial, output = (tmp_path / name for name in ("assets", "initial", "schedule"))
    assets.mkdir()
    (assets / "smoke_summary.json").write_text("{}")
    config = {"profile": "full", "seed": 43, "batch": 56, "workers": 4, "device": "cpu",
              "assets_manifest_sha256": schedule.sha(assets / "smoke_summary.json"),
              "architecture_source_commit": "architecture"}

    def save(directory, epoch, metric, start=None, complete=True):
        directory.mkdir(parents=True, exist_ok=True)
        history = [{"epoch": index} for index in range(1, epoch + 1)]
        weights = {"weight": torch.tensor(float(epoch))}
        torch.save({"format": RECOVERY_FORMAT, "config": config, "history": history,
                    "model": weights}, directory / "resume.pt")
        if complete:
            torch.save(weights, directory / "checkpoint.pt")
            report = {**config, "mode": "full", "loader_workers": 4, "train_videos": 1200,
                      "dev_videos": 900, "dev_frames_per_video": 8, "history": history,
                      "checkpoint_sha256": schedule.sha(directory / "checkpoint.pt"),
                      "dev": {"acer_pooled": metric, "threshold_from_dev": 0.2}}
            if start is not None:
                report["resumed_from_epoch"] = start
            (directory / "pilot_result.json").write_text(json.dumps(report))

    save(initial, 100, 0.1)
    locked = {"epoch": 100, "seed": 43, "batch": 56, "assets_manifest_sha256": config["assets_manifest_sha256"],
              "dev_report_sha256": schedule.sha(initial / "pilot_result.json"), "protocol_sha256": "protocol"}
    monkeypatch.setattr(schedule, "verify_run", lambda *args: locked)
    return assets, initial, output, save


def test_schedule_continues_from_latest_recovery_and_reuses_dev_results(schedule_fixture, tmp_path, monkeypatch):
    assets, initial, output, save = schedule_fixture
    calls = []

    def fake_train(root, out, device, epochs, batch, seed, profile, protocol, workers, *, checkpoint_every, resume):
        state = torch.load(resume, weights_only=True)
        calls.append((len(state["history"]), epochs))
        if len(calls) == 1:
            save(out, 125, 0, complete=False)
            raise KeyboardInterrupt
        save(out, epochs, 0.05, start=len(state["history"]))

    monkeypatch.setattr(schedule, "train", fake_train)

    def run():
        schedule.continue_training(initial, assets, tmp_path / "protocol.tar", output,
                                   torch.device("cpu"), epochs=200)

    with pytest.raises(KeyboardInterrupt):
        run()
    assert json.loads((output / "dev_selection.json").read_text())["best"]["epoch"] == 100
    run()
    assert calls == [(100, 150), (125, 150), (150, 200)]
    selection = json.loads((output / "dev_selection.json").read_text())
    assert selection["complete"] and selection["best"]["epoch"] == 150
    assert [item["epoch"] for item in selection["candidates"]] == [100, 150, 200]
    run()
    assert len(calls) == 3
    with pytest.raises(ValueError, match="separate output directory"):
        schedule.continue_training(initial, assets, tmp_path / "protocol.tar", output,
                                   torch.device("cpu"), epochs=250)


def test_schedule_rejects_a_resume_with_different_baseline_weights(schedule_fixture, tmp_path):
    assets, initial, output, _ = schedule_fixture
    path = initial / "resume.pt"
    state = torch.load(path, weights_only=True)
    state["model"]["weight"] = torch.tensor(-1.0)
    torch.save(state, path)
    with pytest.raises(ValueError, match="identical baseline weights"):
        schedule.continue_training(initial, assets, tmp_path / "protocol.tar", output,
                                   torch.device("cpu"), epochs=150)


def test_continuation_notebook_compiles_and_contains_schedule_worker():
    path = ROOT / "notebooks/Face_PAD_OULU_NPU_CDCN_PRNet_Continue_Train_Dev.ipynb"
    cells = json.loads(path.read_text(encoding="utf-8"))["cells"]
    for cell in cells:
        if cell["cell_type"] == "code":
            compile("".join(cell["source"]), path.name, "exec")
    setup = "".join(cells[2]["source"])
    namespace = {}
    # Extract the embedded source without executing Colab setup.
    prefix = setup.split("\nimport ", 1)[0]
    exec(prefix, namespace)
    archive_bytes = gzip.decompress(base64.b64decode(namespace["BUNDLE"]))
    with tarfile.open(fileobj=io.BytesIO(archive_bytes)) as bundle:
        worker = bundle.extractfile("scripts/cdcn_prnet_dev_schedule.py").read()
    assert worker == (ROOT / "scripts/cdcn_prnet_dev_schedule.py").read_bytes()
    assert '"--epochs", 1300' in "".join(cells[4]["source"])
