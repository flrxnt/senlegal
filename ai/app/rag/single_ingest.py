"""Ingestion d'un seul PDF (uploadé via l'API), indexé sous un ``source_id``.

Permet à l'admin (via le backend) d'ajouter dynamiquement de nouveaux documents
RAG sans devoir relancer une ré-indexation complète depuis le système de
fichiers. Chaque chunk est étiqueté avec ``source_id`` (l'ID du Document côté
backend) afin de pouvoir le désindexer à la suppression.
"""
from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Callable

from ..config import get_settings
from .chunker import chunk_documents
from .embeddings import embed_passages
from .ingestion import _chunk_to_meta
from .pdf_loader import load_pdf
from .vectorstore import get_collection

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[int, int], None]


def ingest_pdf_bytes(
    *,
    pdf_bytes: bytes,
    filename: str,
    source_id: str,
    on_progress: ProgressCallback | None = None,
) -> dict:
    """Indexe un PDF unique en mémoire dans Chroma sous ``source_id``.

    Stratégie d'idempotence : on supprime d'abord tous les chunks portant ce
    ``source_id`` puis on ré-indexe. Permet aussi un re-ingest propre.
    """
    settings = get_settings()
    if not pdf_bytes:
        raise ValueError("PDF vide.")

    safe_name = Path(filename).name or "document.pdf"

    tmp_dir = Path(tempfile.mkdtemp(prefix="ingest_"))
    tmp_path = tmp_dir / safe_name
    tmp_path.write_bytes(pdf_bytes)

    try:
        pages = load_pdf(tmp_path)
        chunks = chunk_documents(pages, max_chunk_chars=settings.max_chunk_chars)
    finally:
        tmp_path.unlink(missing_ok=True)
        try:
            tmp_dir.rmdir()
        except OSError:
            pass

    if not chunks:
        return {
            "status": "empty",
            "source_id": source_id,
            "filename": safe_name,
            "pages": len(pages),
            "chunks": 0,
        }

    col = get_collection(settings.chroma_path, settings.collection_name)

    try:
        col.delete(where={"source_id": source_id})
    except Exception as exc:  # noqa: BLE001
        logger.warning("Suppression préalable source_id=%s : %s", source_id, exc)

    existing = set(col.get(include=[]).get("ids", []))
    if existing:
        ids_to_drop = [c.chunk_id for c in chunks if c.chunk_id in existing]
        if ids_to_drop:
            col.delete(ids=ids_to_drop)

    batch = 32
    total = 0
    for i in range(0, len(chunks), batch):
        sub = chunks[i : i + batch]
        texts = [c.text for c in sub]
        vectors = embed_passages(settings.embed_model, texts)
        metadatas = []
        for c in sub:
            m = _chunk_to_meta(c)
            m["source_id"] = source_id
            m["source_filename"] = safe_name
            metadatas.append(m)
        col.add(
            ids=[c.chunk_id for c in sub],
            documents=texts,
            metadatas=metadatas,
            embeddings=[v.tolist() for v in vectors],
        )
        total += len(sub)
        if on_progress:
            on_progress(total, len(chunks))
        logger.info(
            "[source_id=%s] indexé %d / %d chunks", source_id, total, len(chunks)
        )

    return {
        "status": "ok",
        "source_id": source_id,
        "filename": safe_name,
        "pages": len(pages),
        "chunks": len(chunks),
        "documents": sorted({c.document for c in chunks}),
        "doc_type": chunks[0].doc_type if chunks else None,
    }


def delete_source(source_id: str) -> dict:
    """Supprime tous les chunks indexés sous ce ``source_id``."""
    settings = get_settings()
    col = get_collection(settings.chroma_path, settings.collection_name)
    before = col.count()
    try:
        col.delete(where={"source_id": source_id})
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Échec suppression source {source_id}: {exc}") from exc
    after = col.count()
    return {
        "status": "ok",
        "source_id": source_id,
        "deleted": max(0, before - after),
        "remaining": after,
    }
