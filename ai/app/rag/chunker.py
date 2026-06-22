"""Découpage du texte par article des textes juridiques sénégalais."""
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

# Marqueurs de sections parentes (livre, partie, titre, chapitre, section,
# sous-section, paragraphe). Accepte chiffres romains, arabes et les formes
# textuelles PREMIER/PREMIERE/PREMIÈRE courantes dans le Code de la Famille.
_NUMERAL = r"(?:[IVXLC0-9]+|PREMI(?:ER|[EÈ]RE))"
SECTION_RE = re.compile(
    r"(?im)^\s*("
    r"LIVRE\s+" + _NUMERAL + r"|"
    r"PARTIE\s+" + _NUMERAL + r"|"
    r"TITRE\s+" + _NUMERAL + r"|"
    r"CHAPITRE\s+" + _NUMERAL + r"|"
    r"SECTION\s+" + _NUMERAL + r"|"
    r"SOUS[\s\-]SECTION\s+" + _NUMERAL + r"|"
    r"Sous[\s\-]section\s+" + _NUMERAL + r"|"
    r"Paragraphe\s+" + _NUMERAL + r"|"
    r"PARAGRAPHE\s+" + _NUMERAL +
    r")\b\s*[\.\:\-\—]?\s*(.*)$",
)

# Référence de loi modificative : "(Loi n° 89-01 du 17 janvier 1989)"
_LOI_REF_RE = re.compile(
    r"\(Loi\s+n[°o]\s*[\d\-]+\s+du\s+\d{1,2}\s*\w+\s+\d{4}\)",
    re.IGNORECASE,
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
    doc_type: str = "code"
    decision_number: str | None = None
    decision_date: str | None = None
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


def _extract_title_from_body(body: str, inline_title: str) -> tuple[str, str | None]:
    """Extrait le titre d'un article et une éventuelle référence de loi modificative.

    Dans le Code de la Famille, le titre est sur la ligne suivant "Article X",
    pas sur la même ligne. Si `inline_title` (capturé par le regex sur la même
    ligne) est vide, on prend la première ligne non-vide du body après le header.

    Retourne (titre, loi_modificative | None).
    """
    loi_ref: str | None = None
    loi_match = _LOI_REF_RE.search(body[:300])
    if loi_match:
        loi_ref = loi_match.group(0).strip("()")

    if inline_title:
        return inline_title[:200], loi_ref

    lines = body.split("\n")
    # La 1ère ligne est le header "Article X" lui-même ; on cherche le titre
    # dans les lignes suivantes.
    for line in lines[1:]:
        stripped = line.strip()
        if not stripped:
            continue
        # Ignorer les références de loi modificative
        if stripped.startswith("(Loi ") or stripped.startswith("(loi "):
            continue
        # Ignorer si la ligne est trop longue (probablement du corps de texte)
        if len(stripped) > 80:
            break
        # Ignorer si ça commence comme du corps (phrase commençant par une minuscule
        # ou un déterminant long)
        if stripped[0].islower():
            break
        return stripped[:200], loi_ref

    return "", loi_ref


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
        if text.count("…") + text.count("...") >= 3:
            return True
        toc_lines = re.findall(r".{0,80}[\.\…]{3,}\s*\d{1,4}\s*$", text, flags=re.M)
        if len(toc_lines) >= 2:
            return True
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
        inline_title = m.group(2).strip()
        article_title, loi_modificative = _extract_title_from_body(body, inline_title)

        page_start = _page_for_offset(offsets, start)
        page_end = _page_for_offset(offsets, max(start, end - 1))
        section = section_at(start)

        extra_meta: dict = {}
        if loi_modificative:
            extra_meta["loi_modificative"] = loi_modificative

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
                    metadata=extra_meta,
                )
            )
    return chunks


def chunk_documents(pages: list[PageText], max_chunk_chars: int = 1500) -> list[Chunk]:
    """Groupe les pages par document puis chunke chacun.

    Dispatch automatiquement vers ``chunk_pages`` (Code) ou ``chunk_decision``
    (décisions ARCOP) selon le ``doc_type`` des pages.
    """
    by_doc: dict[str, list[PageText]] = {}
    for p in pages:
        by_doc.setdefault(p.document, []).append(p)
    out: list[Chunk] = []
    for doc, doc_pages in by_doc.items():
        doc_pages.sort(key=lambda x: x.page)
        if doc_pages and doc_pages[0].doc_type == "decision":
            out.extend(chunk_decision(doc_pages, max_chunk_chars=max_chunk_chars))
        else:
            out.extend(chunk_pages(doc_pages, max_chunk_chars=max_chunk_chars))
    return out


# ---------------------------------------------------------------------------
# Chunker spécifique aux décisions ARCOP / CRD
# ---------------------------------------------------------------------------

# Sections canoniques d'une décision ARCOP. L'ordre n'est pas garanti et toutes
# les sections ne sont pas présentes dans toutes les décisions (les recours
# déclarés irrecevables n'ont par ex. ni "FAITS" ni "EXAMEN").
# Clé = identifiant court (servira de ``article_number``).
# Valeur = expression régulière reconnaissant l'en-tête de section.
_DECISION_SECTIONS: list[tuple[str, re.Pattern[str]]] = [
    (
        "VISAS",
        re.compile(r"(?im)^\s*LA\s+CHAMBRE\s+DES\s+MARCH[ÉE]S\b"),
    ),
    (
        "RECEVABILITE",
        re.compile(r"(?im)^\s*SUR\s+LA\s+RECEVABILIT[ÉE]\s+DU\s+RECOURS\b"),
    ),
    (
        "FAITS",
        re.compile(r"(?im)^\s*LES\s+FAITS\b"),
    ),
    (
        "MOYENS_REQUERANT",
        re.compile(
            r"(?im)^\s*LES\s+(?:MOYENS|MOTIFS)"
            r"(?:\s+D[ÉE]VELOPP[ÉE]S)?\s+(?:A|À)\s+L['']?APPUI\s+DU\s+RECOURS\b"
        ),
    ),
    (
        "MOTIFS_AUTORITE",
        re.compile(
            r"(?im)^\s*LES\s+MOTIFS\s+DONN[ÉE]S\s+PAR\s+L['']?AUTORIT[ÉE]\s+CONTRACTANTE\b"
        ),
    ),
    (
        "OBJET",
        re.compile(r"(?im)^\s*(?:L['']?\s*)?OBJET\s+DU\s+LITIGE\b"),
    ),
    (
        "EXAMEN",
        re.compile(r"(?im)^\s*EXAMEN\s+DU\s+LITIGE\b"),
    ),
    (
        "DISPOSITIF",
        re.compile(r"(?im)^\s*PAR\s+CES\s+MOTIFS\b"),
    ),
]

_DECISION_SECTION_LABELS = {
    "VISAS": "Visas et composition",
    "RECEVABILITE": "Sur la recevabilité du recours",
    "FAITS": "Les faits",
    "MOYENS_REQUERANT": "Moyens développés à l'appui du recours",
    "MOTIFS_AUTORITE": "Motifs donnés par l'autorité contractante",
    "OBJET": "Objet du litige",
    "EXAMEN": "Examen du litige",
    "DISPOSITIF": "Par ces motifs",
}


def chunk_decision(
    pages: list[PageText], max_chunk_chars: int = 1500
) -> list[Chunk]:
    """Découpe une décision ARCOP en chunks par grandes sections.

    Stratégie : on repère les en-têtes de sections canoniques (FAITS, MOYENS,
    EXAMEN, PAR CES MOTIFS…), on délimite leurs bornes dans le texte concaténé
    et on crée un Chunk par section. Les sections trop longues sont re-découpées
    via ``_split_long``. Le "DISPOSITIF" (PAR CES MOTIFS) est toujours conservé
    en un seul chunk si possible car c'est la décision proprement dite.
    """
    if not pages:
        return []
    document = pages[0].document
    decision_number = pages[0].decision_number
    decision_date = pages[0].decision_date

    full_text, offsets = _flatten(pages)

    # Trouve la 1ère occurrence de chaque section
    found: list[tuple[int, str]] = []  # (offset, section_key)
    for key, pattern in _DECISION_SECTIONS:
        m = pattern.search(full_text)
        if m:
            found.append((m.start(), key))
    found.sort()

    if not found:
        # Pas de section reconnue : on indexe quand même le document entier en
        # le découpant brutalement, pour ne pas perdre le contenu.
        return _fallback_decision_chunks(
            full_text=full_text,
            offsets=offsets,
            document=document,
            decision_number=decision_number,
            decision_date=decision_date,
            max_chunk_chars=max_chunk_chars,
        )

    # Crée les bornes [start, end[ pour chaque section
    bounds: list[tuple[str, int, int]] = []
    for i, (start, key) in enumerate(found):
        end = found[i + 1][0] if i + 1 < len(found) else len(full_text)
        bounds.append((key, start, end))

    # Préambule (avant la 1ère section reconnue) : visas, composition, saisine.
    first_start = found[0][0]
    if first_start > 200:
        bounds.insert(0, ("PREAMBULE", 0, first_start))

    chunks: list[Chunk] = []
    section_label = decision_number or document
    for key, start, end in bounds:
        body = full_text[start:end].strip()
        if not body:
            continue

        page_start = _page_for_offset(offsets, start)
        page_end = _page_for_offset(offsets, max(start, end - 1))
        title = _DECISION_SECTION_LABELS.get(key, key.title())

        sub_texts = _split_long(body, max_chunk_chars)
        for part_idx, sub in enumerate(sub_texts):
            chunk_id = _make_id(document, key, part_idx, page_start, start)
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    text=sub,
                    article_number=key,
                    article_title=title,
                    document=document,
                    volume=None,
                    section=section_label,
                    page_start=page_start,
                    page_end=page_end,
                    part=part_idx,
                    doc_type="decision",
                    decision_number=decision_number,
                    decision_date=decision_date,
                )
            )
    return chunks


def _fallback_decision_chunks(
    *,
    full_text: str,
    offsets: list[tuple[int, int]],
    document: str,
    decision_number: str | None,
    decision_date: str | None,
    max_chunk_chars: int,
) -> list[Chunk]:
    chunks: list[Chunk] = []
    sub_texts = _split_long(full_text.strip(), max_chunk_chars)
    for part_idx, sub in enumerate(sub_texts):
        page = _page_for_offset(offsets, 0) if part_idx == 0 else 0
        chunk_id = _make_id(document, "DECISION", part_idx, page, part_idx)
        chunks.append(
            Chunk(
                chunk_id=chunk_id,
                text=sub,
                article_number="DECISION",
                article_title=decision_number or document,
                document=document,
                volume=None,
                section=decision_number or document,
                page_start=page,
                page_end=page,
                part=part_idx,
                doc_type="decision",
                decision_number=decision_number,
                decision_date=decision_date,
            )
        )
    return chunks
