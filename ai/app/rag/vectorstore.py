"""Client ChromaDB : HttpClient (serveur dédié) ou PersistentClient (local).

Le choix se fait au runtime via la variable d'environnement ``CHROMA_HOST`` :
- définie -> on parle à un service Chroma distant (recommandé en docker-compose) ;
- absente -> on tombe sur un client persistant local sous ``CHROMA_DIR``.

Les signatures publiques (``get_collection(chroma_dir, name)`` ...) restent
inchangées ; le paramètre ``chroma_dir`` est ignoré en mode HTTP.
"""
from __future__ import annotations

import logging
import threading
from pathlib import Path

from ..config import get_settings

logger = logging.getLogger(__name__)

_LOCK = threading.Lock()
_CLIENT = None
_COLLECTIONS: dict[str, object] = {}


def _build_client(chroma_dir: Path):
    import chromadb
    from chromadb.config import Settings as ChromaSettings

    settings = get_settings()
    chroma_settings = ChromaSettings(anonymized_telemetry=False, allow_reset=True)
    if settings.chroma_host:
        logger.info(
            "Connexion à Chroma HTTP %s:%s (ssl=%s)",
            settings.chroma_host,
            settings.chroma_port,
            settings.chroma_ssl,
        )
        return chromadb.HttpClient(
            host=settings.chroma_host,
            port=settings.chroma_port,
            ssl=settings.chroma_ssl,
            settings=chroma_settings,
        )
    logger.info("Ouverture de Chroma persistant à %s", chroma_dir)
    return chromadb.PersistentClient(path=str(chroma_dir), settings=chroma_settings)


def get_client(chroma_dir: Path):
    global _CLIENT
    if _CLIENT is not None:
        return _CLIENT
    with _LOCK:
        if _CLIENT is None:
            _CLIENT = _build_client(chroma_dir)
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
