"""On-disk cache of topic embeddings (one compressed file per model).

Computing embeddings for the whole catalogue (~2000 topics) is the slow part of
semantic search, but the corpus barely changes between runs. This cache persists
the vectors in a compressed ``.npz`` keyed by a per-model filename, so only new
topics are ever embedded. It stores plain vectors and is unaware of the domain.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np

from coffee.config import Settings


class EmbeddingCache:
    """Persists ``{key: vector}`` for a single embedding model."""

    def __init__(self, settings: Settings, model_id: str) -> None:
        safe = re.sub(r"[^a-z0-9]+", "_", model_id.lower()).strip("_")
        self._dir = settings.cache_dir / "embeddings"
        self._path = self._dir / f"{safe}.npz"

    def load(self) -> dict[str, np.ndarray]:
        """Return the cached vectors, or an empty mapping if there is none."""
        if not self._path.exists():
            return {}
        try:
            data = np.load(self._path, allow_pickle=False)
            return {key: vector for key, vector in zip(data["keys"], data["vectors"])}
        except (OSError, ValueError, KeyError):
            return {}  # a corrupt cache is treated as empty and rebuilt

    def save(self, vectors: dict[str, np.ndarray]) -> None:
        """Persist the mapping atomically (write to .tmp, then replace)."""
        if not vectors:
            return
        self._dir.mkdir(parents=True, exist_ok=True)
        keys = np.array(list(vectors.keys()))
        matrix = np.array(list(vectors.values()), dtype=np.float32)
        tmp = self._path.with_suffix(".tmp.npz")
        np.savez_compressed(tmp, keys=keys, vectors=matrix)
        tmp.replace(self._path)
