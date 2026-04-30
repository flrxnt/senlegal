"""Client ChromaDB persistant."""
from __future__ import annotations

import logging
import threading
from pathlib import Path

logger = logging.getLogger(__name__)

_LOCK = threading.Lock()
_CLIENT = None
_COLLECTIONS: dict[str, object] = {}


def get_client(chroma_dir: Path):
    global _CLIENT
    if _CLIENT is not None:
        return _CLIENT
    with _LOCK:
        if _CLIENT is None:
            import chromadb
            from chromadb.config import Settings as ChromaSettings

            logger.info("Ouverture de Chroma à %s", chroma_dir)
            _CLIENT = chromadb.PersistentClient(
                path=str(chroma_dir),
                settings=ChromaSettings(anonymized_telemetry=False, allow_reset=True),
            )
    return _CLIENT


def get_collection(chroma_dir: Path, name: str):
    if name in _COLLECTIONS:
        return _COLLECTIONS[name]
    client = get_client(chroma_dir)
    col = client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )
    _COLLECTIONS[name] = col
    return col


def reset_collection(chroma_dir: Path, name: str):
    client = get_client(chroma_dir)
    try:
        client.delete_collection(name)
    except Exception:  # noqa: BLE001
        pass
    _COLLECTIONS.pop(name, None)
    return get_collection(chroma_dir, name)


def count(chroma_dir: Path, name: str) -> int:
    try:
        return get_collection(chroma_dir, name).count()
    except Exception:  # noqa: BLE001
        return 0
