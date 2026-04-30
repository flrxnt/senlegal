"""Récupération des chunks pertinents depuis ChromaDB."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from .embeddings import embed_query
from .glossary import expand_query
from .vectorstore import get_collection

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    chunk_id: str
    text: str
    score: float  # similarité cosinus dans [0, 1] (1 = identique)
    article_number: str
    article_title: str
    document: str
    volume: str | None
    section: str | None
    page: int


def _query_collection(
    col,
    *,
    query: str,
    embed_model: str,
    top_k: int,
    min_score: float,
) -> list[RetrievedChunk]:
    expanded = expand_query(query)
    if expanded != query:
        logger.info("Requête enrichie via glossaire: %r -> %r", query, expanded)
    vec = embed_query(embed_model, expanded)
    res = col.query(
        query_embeddings=[vec.tolist()],
        n_results=max(top_k, 1),
        include=["documents", "metadatas", "distances"],
    )
    ids = res.get("ids", [[]])[0]
    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    dists = res.get("distances", [[]])[0]

    chunks: list[RetrievedChunk] = []
    for cid, doc, meta, dist in zip(ids, docs, metas, dists):
        # Chroma renvoie une distance cosinus dans [0, 2] ; on convertit en similarité [-1, 1].
        score = 1.0 - float(dist)
        if score < min_score:
            continue
        meta = meta or {}
        chunks.append(
            RetrievedChunk(
                chunk_id=cid,
                text=doc,
                score=score,
                article_number=str(meta.get("article_number", "?")),
                article_title=str(meta.get("article_title", "")),
                document=str(meta.get("document", "")),
                volume=meta.get("volume"),
                section=meta.get("section"),
                page=int(meta.get("page_start", 0) or 0),
            )
        )
    return chunks


def retrieve(
    *,
    query: str,
    chroma_dir: Path,
    collection_name: str,
    embed_model: str,
    top_k: int = 5,
    min_score: float = 0.0,
) -> list[RetrievedChunk]:
    col = get_collection(chroma_dir, collection_name)
    if col.count() == 0:
        return []
    return _query_collection(
        col,
        query=query,
        embed_model=embed_model,
        top_k=top_k,
        min_score=min_score,
    )


def retrieve_multi(
    *,
    queries: list[str],
    chroma_dir: Path,
    collection_name: str,
    embed_model: str,
    top_k: int = 5,
    min_score: float = 0.0,
) -> list[RetrievedChunk]:
    """Lance plusieurs requêtes et fusionne les résultats par chunk_id.

    Pour chaque chunk en commun on garde le meilleur score. Le résultat final
    est trié par score décroissant et tronqué à ``top_k``. Les requêtes vides
    ou en doublon (après nettoyage) sont ignorées.
    """
    seen_q: set[str] = set()
    cleaned: list[str] = []
    for q in queries:
        if not q:
            continue
        key = " ".join(q.split()).lower()
        if not key or key in seen_q:
            continue
        seen_q.add(key)
        cleaned.append(q)
    if not cleaned:
        return []

    col = get_collection(chroma_dir, collection_name)
    if col.count() == 0:
        return []

    # On élargit un peu chaque sous-requête pour avoir matière à fusionner.
    per_query_k = max(top_k, top_k * 2 if len(cleaned) > 1 else top_k)
    merged: dict[str, RetrievedChunk] = {}
    for q in cleaned:
        for chunk in _query_collection(
            col,
            query=q,
            embed_model=embed_model,
            top_k=per_query_k,
            min_score=min_score,
        ):
            existing = merged.get(chunk.chunk_id)
            if existing is None or chunk.score > existing.score:
                merged[chunk.chunk_id] = chunk

    ranked = sorted(merged.values(), key=lambda c: c.score, reverse=True)
    return ranked[:top_k]
