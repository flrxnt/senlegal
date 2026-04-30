"""Pipeline complet d'ingestion : PDFs -> chunks -> embeddings -> Chroma."""
from __future__ import annotations

import json
import logging
from pathlib import Path

from ..config import get_settings
from .chunker import Chunk, chunk_documents
from .embeddings import embed_passages
from .pdf_loader import load_all_pdfs
from .vectorstore import get_collection, reset_collection

logger = logging.getLogger(__name__)


def _chunk_to_meta(c: Chunk) -> dict:
    return {
        "article_number": c.article_number,
        "article_title": c.article_title,
        "document": c.document,
        "volume": c.volume or "",
        "section": c.section or "",
        "page_start": c.page_start,
        "page_end": c.page_end,
        "part": c.part,
    }


def _save_chunks_cache(chunks: list[Chunk], processed_dir: Path) -> None:
    out = processed_dir / "chunks.json"
    payload = [
        {
            "chunk_id": c.chunk_id,
            "text": c.text,
            **_chunk_to_meta(c),
        }
        for c in chunks
    ]
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Cache chunks écrit: %s (%d chunks)", out, len(chunks))


def run_ingestion(force: bool = False) -> dict:
    settings = get_settings()
    assets = settings.assets_path
    if not assets.exists():
        raise FileNotFoundError(f"Dossier assets introuvable: {assets}")

    logger.info("Démarrage de l'ingestion depuis %s", assets)
    pages = load_all_pdfs(assets)
    chunks = chunk_documents(pages, max_chunk_chars=settings.max_chunk_chars)
    logger.info("Chunks générés: %d", len(chunks))

    if not chunks:
        return {"status": "empty", "pages": len(pages), "chunks": 0}

    _save_chunks_cache(chunks, settings.processed_path)

    if force:
        col = reset_collection(settings.chroma_path, settings.collection_name)
    else:
        col = get_collection(settings.chroma_path, settings.collection_name)
        # Idempotence : on retire les ids existants avant ré-upsert
        existing = set(col.get(include=[]).get("ids", []))
        if existing:
            ids_to_drop = [c.chunk_id for c in chunks if c.chunk_id in existing]
            if ids_to_drop:
                col.delete(ids=ids_to_drop)

    # Embeddings par lots
    batch = 32
    total = 0
    for i in range(0, len(chunks), batch):
        sub = chunks[i : i + batch]
        texts = [c.text for c in sub]
        vectors = embed_passages(settings.embed_model, texts)
        col.add(
            ids=[c.chunk_id for c in sub],
            documents=texts,
            metadatas=[_chunk_to_meta(c) for c in sub],
            embeddings=[v.tolist() for v in vectors],
        )
        total += len(sub)
        logger.info("Indexé %d / %d", total, len(chunks))

    return {
        "status": "ok",
        "pages": len(pages),
        "chunks": len(chunks),
        "documents": sorted({c.document for c in chunks}),
    }
