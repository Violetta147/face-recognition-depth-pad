from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from .recognizer import cosine_similarity, l2_normalize
from .types import RecognitionResult


@dataclass(frozen=True)
class GalleryEntry:
    person_id: str
    display_name: str
    embedding: np.ndarray
    model_version: str
    enrolled_at: str
    sample_count: int


class FaceGallery:
    """Local embedding templates with no raw images."""

    SCHEMA_VERSION = 1

    def __init__(self) -> None:
        self._entries: dict[str, GalleryEntry] = {}

    def __len__(self) -> int:
        return len(self._entries)

    @property
    def entries(self) -> tuple[GalleryEntry, ...]:
        return tuple(self._entries.values())

    def enroll(
        self,
        person_id: str,
        display_name: str,
        embeddings: list[np.ndarray],
        model_version: str,
        enrolled_at: str | None = None,
    ) -> GalleryEntry:
        person_id = person_id.strip()
        display_name = display_name.strip()
        if not person_id or not display_name:
            raise ValueError("person_id and display_name must not be empty")
        if not embeddings:
            raise ValueError("At least one embedding is required")
        dimensions = {np.asarray(item).size for item in embeddings}
        if len(dimensions) != 1:
            raise ValueError("All embeddings must have the same dimension")
        template = l2_normalize(
            np.mean(np.stack([l2_normalize(item) for item in embeddings]), axis=0)
        )
        entry = GalleryEntry(
            person_id=person_id,
            display_name=display_name,
            embedding=template,
            model_version=model_version,
            enrolled_at=enrolled_at
            or datetime.now(timezone.utc).isoformat(timespec="seconds"),
            sample_count=len(embeddings),
        )
        self._entries[person_id] = entry
        return entry

    def match(self, embedding: np.ndarray, threshold: float) -> RecognitionResult:
        if not self._entries:
            return RecognitionResult(None, None, None, True)
        query = l2_normalize(embedding)
        best = max(
            self._entries.values(),
            key=lambda entry: cosine_similarity(query, entry.embedding),
        )
        score = cosine_similarity(query, best.embedding)
        if score < threshold:
            return RecognitionResult(None, None, score, True)
        return RecognitionResult(best.person_id, best.display_name, score, False)

    def save(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        ordered = sorted(self._entries.values(), key=lambda item: item.person_id)
        metadata = {
            "schema_version": self.SCHEMA_VERSION,
            "entries": [
                {
                    "person_id": item.person_id,
                    "display_name": item.display_name,
                    "model_version": item.model_version,
                    "enrolled_at": item.enrolled_at,
                    "sample_count": item.sample_count,
                }
                for item in ordered
            ],
        }
        matrix = (
            np.stack([item.embedding for item in ordered]).astype(np.float32)
            if ordered
            else np.empty((0, 0), dtype=np.float32)
        )
        # Atomic replacement prevents a partially written biometric gallery.
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{target.name}.", suffix=".tmp", dir=target.parent
        )
        os.close(descriptor)
        try:
            with open(temporary_name, "wb") as stream:
                np.savez_compressed(
                    stream,
                    embeddings=matrix,
                    metadata=np.array(json.dumps(metadata, ensure_ascii=False)),
                )
            os.replace(temporary_name, target)
        finally:
            if os.path.exists(temporary_name):
                os.unlink(temporary_name)

    @classmethod
    def load(cls, path: str | Path) -> "FaceGallery":
        source = Path(path)
        gallery = cls()
        if not source.exists():
            return gallery
        with np.load(source, allow_pickle=False) as payload:
            matrix = np.asarray(payload["embeddings"], dtype=np.float32)
            metadata = json.loads(str(payload["metadata"].item()))
        if metadata.get("schema_version") != cls.SCHEMA_VERSION:
            raise ValueError("Unsupported gallery schema version")
        records = metadata.get("entries", [])
        if len(records) != len(matrix):
            raise ValueError("Gallery metadata and embeddings are inconsistent")
        for record, embedding in zip(records, matrix, strict=True):
            entry = GalleryEntry(
                person_id=record["person_id"],
                display_name=record["display_name"],
                embedding=l2_normalize(embedding),
                model_version=record["model_version"],
                enrolled_at=record["enrolled_at"],
                sample_count=int(record["sample_count"]),
            )
            gallery._entries[entry.person_id] = entry
        return gallery

