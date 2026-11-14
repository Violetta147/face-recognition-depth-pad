import io
import tarfile
from pathlib import Path

import numpy as np
import pytest

from deepface_pad.oulu_npu import expected_ids, face_crop, protocol_videos, read_eyes, sample_crops, select_videos


def protocol_tar(path: Path, split: str = "Train", *, bad_label=False):
    ids = sorted(expected_ids(1, None, "train"))
    lines = [f"{1 if a == 1 else -1},{p}_{s}_{u:02}_{a}\n" for p, s, u, a in ids]
    if bad_label:
        lines[0] = lines[0].replace("1,", "-1,", 1)
    data = "".join(lines).encode()
    info = tarfile.TarInfo(f"Protocols/Protocol_1/{split}.txt")
    info.size = len(data)
    with tarfile.open(path, "w") as tar:
        tar.addfile(info, io.BytesIO(data))


def test_protocol_membership_and_pilot(tmp_path):
    path = tmp_path / "Protocols.tar"
    protocol_tar(path)
    rows = protocol_videos(path, 1, None, "train")
    assert len(rows) == 1200
    pilot = select_videos(rows, True)
    assert len(pilot) == len({(v.phone, v.access) for v in pilot}) == 30
    assert len(expected_ids(1, None, "test")) == 600
    assert len(expected_ids(4, 2, "test")) == 60
    assert {p for p, _, _, _ in expected_ids(3, 2, "test")} == {2}
    protocol_tar(path, bad_label=True)
    with pytest.raises(ValueError, match="conflicting label"):
        protocol_videos(path, 1, None, "train")


def test_face_crop_fallback_and_missing_landmarks():
    pytest.importorskip("cv2")

    class Detector:
        def detect(self, image):
            assert image.shape == (320, 320, 3)
            return None, None

    eyes = read_eyes(b"0,0,0,0,0\n1 40 42 80 42\n")
    image = np.full((100, 150, 3), 123, dtype=np.uint8)
    assert face_crop(image, Detector(), eyes.get(0)) == (None, None)
    crop, source = face_crop(image, Detector(), eyes[1])
    assert source == "eyes" and crop.shape == (256, 256, 3)
    assert (crop == 123).all()


def test_empty_time_bin_reuses_nearest_unused_frame(monkeypatch):
    cv2 = pytest.importorskip("cv2")
    from deepface_pad import oulu_npu

    class Capture:
        index = 0

        def isOpened(self):
            return True

        def set(self, _, index):
            self.index = index
            return True

        def get(self, prop):
            return 12 if prop == cv2.CAP_PROP_FRAME_COUNT else self.index

        def read(self):
            frame = self.index
            self.index += 1
            return True, frame

        def release(self):
            pass

    monkeypatch.setattr(cv2, "VideoCapture", lambda _: Capture())
    monkeypatch.setattr(oulu_npu, "face_crop",
                        lambda frame, *_: (frame, "yunet") if frame >= 4 else (None, None))
    result = list(sample_crops(Path("empty-first-bin.avi"), None, {}, 3))
    assert [(index, method) for index, _, method in result] == [(4, "yunet_nearby"), (5, "yunet"), (9, "yunet")]
    monkeypatch.setattr(oulu_npu, "face_crop",
                        lambda frame, *_: (frame, "yunet") if frame >= 10 else (None, None))
    with pytest.raises(ValueError, match="fewer than 3 distinct"):
        list(sample_crops(Path("too-few.avi"), None, {}, 3))
