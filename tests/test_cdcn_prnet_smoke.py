import ast
import base64
import hashlib
import io
import json
from pathlib import Path
import tarfile

import cv2
import numpy as np

from scripts import cdcn_prnet_smoke as smoke


def test_protocol_smoke_selects_first_video_per_stratum(tmp_path):
    rows = []
    for phone, session in ((1, 1), (4, 2)):
        for subject in (22, 21):
            for access in (1, 2, 3, 4, 5):
                label = 1 if access == 1 else -1
                rows.append(f"{label},{phone}_{session}_{subject}_{access}")
    protocol = tmp_path / "Protocols.tar"
    with tarfile.open(protocol, "w") as archive:
        data = "\ufeff".encode() + "\r\n".join(rows).encode()
        member = tarfile.TarInfo("Protocols/Protocol_1/Dev.txt")
        member.size = len(data)
        archive.addfile(member, io.BytesIO(data))
    assert smoke.select_videos(protocol, "Dev") == {
        f"1_1_22_{access}": access for access in (1, 2, 4)
    }
    assert smoke.select_videos(protocol, "Dev", wide_sample=True) == {
        f"{phone}_{session}_22_{access}": access
        for phone, session in ((1, 1), (4, 2))
        for access in (1, 2, 4)
    }


def test_crop_uses_x_for_width_y_for_height_and_clamps():
    roi = smoke.crop_bounds((61, 2, 15, 20), (36, 77, 3))
    assert roi == (slice(0, 25), slice(58, 77))
    assert smoke.crop_bounds((164, 0, 440, 20), (100, 900)) == (slice(0, 23), slice(98, 670))


def test_emit_attack_retries_empty_depth_and_keeps_nonzero_eval_map(tmp_path, monkeypatch):
    class Capture:
        frame_id = 0

        def get(self, mode):
            return 40 if mode == cv2.CAP_PROP_FRAME_COUNT else self.frame_id

        def set(self, mode, index):
            self.frame_id = index

        def read(self):
            self.frame_id += 1
            return True, np.full((32, 48, 3), self.frame_id, dtype=np.uint8)

        def release(self):
            pass

    monkeypatch.setattr(smoke.cv2, "VideoCapture", lambda path: Capture())

    def reconstruct(frame, *_):
        depth = np.zeros(frame.shape[:2], dtype=np.uint8)
        if frame[0, 0, 0] > 1:
            depth[6:18, 10:25] = 100
        return (10, 6, 15, 12), depth

    monkeypatch.setattr(smoke, "reconstruct", reconstruct)
    video = tmp_path / "1_1_22_4.avi"
    rows = smoke.emit_video(video, 4, "Dev", tmp_path, ())
    assert [row["nominal"] for row in rows] == [1, 13, 29]
    assert [row["frame_id"] for row in rows] == [2, 13, 29]
    assert all(row["train_target_zero"] for row in rows)
    for row in rows:
        name = f"{video.stem}_{row['frame_id']:03d}"
        image = tmp_path / "Dev/images" / video.stem / f"{name}_scene.jpg"
        depth = tmp_path / "Dev/maps" / video.stem / f"{name}_depth1D.jpg"
        bbox = tuple(map(int, image.with_suffix(".dat").read_text().splitlines()))
        loaded = cv2.imread(str(depth), cv2.IMREAD_GRAYSCALE)
        roi = smoke.crop_bounds(bbox, loaded.shape)
        assert cv2.imread(str(image)).shape[:2] == loaded.shape
        assert cv2.resize(loaded[roi], (32, 32)).sum() == row["prnet_sum_32"] > 0
    assert len(list(tmp_path.rglob("*.jpg"))) == 6
    train = smoke.emit_video(video, 4, "Train", tmp_path, (), tuple(range(24)), spread_train=True)
    assert len(train) == 24
    assert len({row["frame_id"] for row in train}) == 24
    assert train[-1]["nominal"] == 39


def test_colab_bundles_current_sources_and_compiles():
    root = Path(__file__).resolve().parents[1]
    notebook = root / "notebooks/Face_PAD_OULU_NPU_CDCN_PRNet_Smoke.ipynb"
    cells = json.loads(notebook.read_text(encoding="utf-8"))["cells"]
    for cell in cells:
        if cell["cell_type"] == "code":
            compile("".join(cell["source"]), notebook.name, "exec")
    assignments = ast.parse("".join(cells[2]["source"])).body[:2]
    digest, encoded = (ast.literal_eval(node.value) for node in assignments)
    bundle = base64.b64decode(encoded)
    assert hashlib.sha256(bundle).hexdigest() == digest
    with tarfile.open(fileobj=io.BytesIO(bundle), mode="r:gz") as archive:
        for name in ("scripts/cdcn_prnet_smoke.py", "src/deepface_pad/progress.py", "src/deepface_pad/__init__.py"):
            assert archive.extractfile(name).read() == (root / name).read_bytes()
