"""Découpage du texte par article du Code des marchés publics."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Iterable

from .pdf_loader import PageText


# Détecte une entête d'article :
#  - "Article premier", "Article 1", "Article 12.", "Article 7-1 :"
#  - forme abrégée des décrets : "Art. premier", "Art. 50.", "Art. 7-1 :"
# La forme abrégée doit être en début de ligne (après éventuels espaces) pour
# éviter de matcher "art." cité au milieu d'une phrase.
ARTICLE_RE = re.compile(
    r"(?im)^\s*(?:Article|Art\.)\s+(premier|\d+(?:[\-\.]\d+)?)\s*[\.\:\-\—]?\s*(.*)$",
)

# Marqueurs de sections parentes (titre, chapitre, section, livre, partie)
SECTION_RE = re.compile(
    r"(?im)^\s*("
    r"LIVRE\s+[IVXLC0-9]+|"
    r"PARTIE\s+[IVXLC0-9]+|"
    r"TITRE\s+[IVXLC0-9]+|"
    r"CHAPITRE\s+[IVXLC0-9]+|"
    r"SECTION\s+[IVXLC0-9]+|"
    r"Sous-section\s+[IVXLC0-9]+"
    r")\b\s*[\.\:\-\—]?\s*(.*)$",
)


@dataclass
class Chunk:
    chunk_id: str
    text: str
    article_number: str
    article_title: str
    document: str
    volume: str | None
    section: str | None
    page_start: int
    page_end: int
    part: int = 0  # numéro de sous-partie si l'article a été re-splitté
    metadata: dict = field(default_factory=dict)


def _make_id(document: str, article_number: str, part: int, page: int, offset: int) -> str:
    # offset garantit l'unicité même si plusieurs textes juridiques du même volume
    # commencent par "Article premier".
    raw = f"{document}|art:{article_number}|p:{page}|off:{offset}|part:{part}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _flatten(pages: Iterable[PageText]) -> tuple[str, list[tuple[int, int]]]:
    """Concatène les pages et retourne aussi un index (offset_start, page_number)."""
    parts: list[str] = []
    offsets: list[tuple[int, int]] = []
    cursor = 0
    for p in pages:
        offsets.append((cursor, p.page))
        parts.append(p.text)
        cursor += len(p.text) + 1  # +1 pour le \n
    return "\n".join(parts), offsets


def _page_for_offset(offsets: list[tuple[int, int]], offset: int) -> int:
    page = offsets[0][1]
    for start, pg in offsets:
        if start <= offset:
            page = pg
        else:
            break
    return page


def _split_long(text: str, max_chars: int) -> list[str]:
    """Sub-split d'un article trop long, en respectant les paragraphes."""
    if len(text) <= max_chars:
        return [text]
    paragraphs = re.split(r"\n\s*\n", text)
    chunks: list[str] = []
    buf = ""
    for para in paragraphs:
        if not buf:
            buf = para
        elif len(buf) + len(para) + 2 <= max_chars:
            buf += "\n\n" + para
        else:
            chunks.append(buf.strip())
            buf = para
    if buf.strip():
        chunks.append(buf.strip())
    # Si un paragraphe seul dépasse encore, hard-split
    final: list[str] = []
    for c in chunks:
        if len(c) <= max_chars:
            final.append(c)
        else:
            for i in range(0, len(c), max_chars):
                final.append(c[i : i + max_chars])
    return final


def chunk_pages(
    pages: list[PageText], max_chunk_chars: int = 1500
) -> list[Chunk]:
    """Découpe les pages d'un même document en chunks par article."""
    if not pages:
        return []
    document = pages[0].document
    volume = pages[0].volume

    full_text, offsets = _flatten(pages)

    # Détecte tous les articles
    article_matches = list(ARTICLE_RE.finditer(full_text))
    if not article_matches:
        return []

    # Map offset -> dernière section connue
    section_events: list[tuple[int, str]] = []
    for m in SECTION_RE.finditer(full_text):
        label = re.sub(r"\s+", " ", m.group(0)).strip()
        section_events.append((m.start(), label))

    def section_at(offset: int) -> str | None:
        current: str | None = None
        for off, label in section_events:
            if off <= offset:
                current = label
            else:
                break
        return current

    def _is_toc(text: str) -> bool:
        """Détecte une entrée de table des matières (lignes pleines de '......')."""
        # Beaucoup de points de conduite, ou ratio mots/ponctuation déséquilibré
        if text.count("…") + text.count("...") >= 3:
            return True
        # Lignes courtes terminées par un n° de page : "Article 42 ......... 223"
        toc_lines = re.findall(r".{0,80}[\.\…]{3,}\s*\d{1,4}\s*$", text, flags=re.M)
        if len(toc_lines) >= 2:
            return True
        # Très peu de mots utiles (juste le titre + chiffres)
        words = re.findall(r"[A-Za-zÀ-ÿ]{3,}", text)
        if len(words) < 8:
            return True
        return False

    chunks: list[Chunk] = []
    for i, m in enumerate(article_matches):
        start = m.start()
        end = article_matches[i + 1].start() if i + 1 < len(article_matches) else len(full_text)
        body = full_text[start:end].strip()
        if not body:
            continue
        if _is_toc(body):
            continue

        article_number = m.group(1).strip()
        # Première ligne après "Article X" = titre potentiel
        first_line = m.group(2).strip()
        article_title = first_line[:200] if first_line else ""

        page_start = _page_for_offset(offsets, start)
        page_end = _page_for_offset(offsets, max(start, end - 1))
        section = section_at(start)

        sub_texts = _split_long(body, max_chunk_chars)
        for part_idx, sub in enumerate(sub_texts):
            chunk_id = _make_id(document, article_number, part_idx, page_start, start)
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    text=sub,
                    article_number=article_number,
                    article_title=article_title,
                    document=document,
                    volume=volume,
                    section=section,
                    page_start=page_start,
                    page_end=page_end,
                    part=part_idx,
                )
            )
    return chunks


def chunk_documents(pages: list[PageText], max_chunk_chars: int = 1500) -> list[Chunk]:
    """Groupe les pages par document puis chunke chacun."""
    by_doc: dict[str, list[PageText]] = {}
    for p in pages:
        by_doc.setdefault(p.document, []).append(p)
    out: list[Chunk] = []
    for doc, doc_pages in by_doc.items():
        doc_pages.sort(key=lambda x: x.page)
        out.extend(chunk_pages(doc_pages, max_chunk_chars=max_chunk_chars))
    return out
