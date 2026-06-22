"""Extraction de texte depuis les PDFs juridiques sénégalais."""
from __future__ import annotations

import logging
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import pdfplumber

logger = logging.getLogger(__name__)


@dataclass
class PageText:
    document: str
    volume: str | None
    page: int
    text: str
    doc_type: str = "code"  # "code" (Recueil) ou "decision" (CRD ARCOP)
    decision_number: str | None = None
    decision_date: str | None = None


_LIGATURES = {
    "\u00ad": "",  # soft hyphen
    "\ufb00": "ff",
    "\ufb01": "fi",
    "\ufb02": "fl",
    "\ufb03": "ffi",
    "\ufb04": "ffl",
    "\u2019": "'",
    "\u2018": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u00a0": " ",
}


def _normalize(text: str) -> str:
    for k, v in _LIGATURES.items():
        text = text.replace(k, v)
    # Recolle les mots coupés par tiret en fin de ligne : "appro-\nprié" -> "approprié"
    text = re.sub(r"-\n(\w)", r"\1", text)
    # Espaces multiples
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def _detect_volume(filename: str) -> str | None:
    m = re.search(r"VOL[-_\s]?(\d+)", filename, flags=re.I)
    return f"Volume {m.group(1)}" if m else None


_DOC_NAME_MAP: dict[str, str] = {
    "code-de-la-famille": "Code de la Famille",
    "code_de_la_famille": "Code de la Famille",
    "codefamille": "Code de la Famille",
    "code-du-travail": "Code du Travail",
    "code-penal": "Code Pénal",
    "code-des-obligations": "Code des Obligations Civiles et Commerciales",
}


def _short_doc_name(filename: str) -> str:
    vol = _detect_volume(filename)
    if vol:
        return f"Recueil des textes juridiques — {vol}"
    stem = Path(filename).stem.lower()
    for pattern, name in _DOC_NAME_MAP.items():
        if pattern in stem:
            return name
    return Path(filename).stem


# Reconnait les en-têtes de décision ARCOP : "DECISION N°041/2026/ARCOP/CRD/DEF"
# (avec ou sans accents, espaces variables, et année optionnelle car certaines
# décisions ont la forme "DÉCISION N°042 /ARCOP/CRD/DEF").
DECISION_HEADER_RE = re.compile(
    r"D[ÉE]CISION\s*N°?\s*(\d+)\s*(?:/\s*(\d{4})\s*)?/\s*ARCOP\s*/\s*CRD(?:\s*/\s*([A-Z]+))?",
    re.IGNORECASE,
)
DECISION_DATE_RE = re.compile(
    r"DU\s+(\d{1,2}\s*(?:er)?)\s+"
    r"(janvier|f[ée]vrier|mars|avril|mai|juin|juillet|ao[ûu]t|septembre|octobre|novembre|d[ée]cembre)\s+"
    r"(\d{4})",
    re.IGNORECASE,
)


def _detect_decision_metadata(text: str) -> tuple[str, str | None] | None:
    """Cherche un en-tête de décision ARCOP dans le texte de la 1ère page.

    Retourne (numero_decision, date_str) ou None si ce n'est pas une décision.
    """
    m = DECISION_HEADER_RE.search(text)
    if not m:
        return None
    num, year, suffix = m.group(1), m.group(2), m.group(3)
    suffix_part = f"/{suffix.upper()}" if suffix else ""
    year_part = f"/{year}" if year else ""
    decision_number = f"N°{num}{year_part}/ARCOP/CRD{suffix_part}"

    date_str: str | None = None
    md = DECISION_DATE_RE.search(text)
    if md:
        day = re.sub(r"\s*er\s*", "er ", md.group(1)).strip()
        date_str = f"{day} {md.group(2).lower()} {md.group(3)}"
    return decision_number, date_str


def _strip_repeated_lines(pages: list[str], min_repeats: int = 3) -> list[str]:
    """Supprime les lignes (header/footer) qui se répètent sur la majorité des pages."""
    if len(pages) < min_repeats * 2:
        return pages
    counter: Counter[str] = Counter()
    for p in pages:
        lines = [ln.strip() for ln in p.splitlines() if ln.strip()]
        # On regarde uniquement les premières et dernières lignes (où sont les headers/footers)
        for ln in lines[:2] + lines[-2:]:
            if 3 <= len(ln) <= 120:
                counter[ln] += 1
    threshold = max(min_repeats, int(0.3 * len(pages)))
    repeated = {ln for ln, c in counter.items() if c >= threshold}
    if not repeated:
        return pages
    cleaned = []
    for p in pages:
        kept = [ln for ln in p.splitlines() if ln.strip() not in repeated]
        cleaned.append("\n".join(kept))
    return cleaned


def load_pdf(path: Path, *, assets_dir: Path | None = None) -> list[PageText]:
    """Charge un PDF et renvoie une liste de PageText nettoyés.

    Détecte automatiquement s'il s'agit d'une décision ARCOP (via l'en-tête
    "DECISION N°.../ARCOP/CRD" ou via le sous-dossier "decisions/") et enrichit
    chaque PageText avec doc_type, decision_number et decision_date.
    """
    raw_pages: list[str] = []
    logger.info("Lecture du PDF : %s", path.name)
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            try:
                txt = page.extract_text() or ""
            except Exception as exc:  # noqa: BLE001
                logger.warning("Page %s illisible: %s", page.page_number, exc)
                txt = ""
            raw_pages.append(txt)

    cleaned_pages = _strip_repeated_lines(raw_pages)

    # Détection du type de document
    in_decisions_dir = False
    if assets_dir is not None:
        try:
            in_decisions_dir = "decisions" in path.relative_to(assets_dir).parts
        except ValueError:
            in_decisions_dir = False

    decision_meta: tuple[str, str | None] | None = None
    first_text = next((t for t in cleaned_pages if t.strip()), "")
    if in_decisions_dir or DECISION_HEADER_RE.search(first_text):
        decision_meta = _detect_decision_metadata(first_text)

    if decision_meta:
        decision_number, decision_date = decision_meta
        doc_type = "decision"
        suffix = f" du {decision_date}" if decision_date else ""
        document = f"Décision {decision_number}{suffix}"
        volume = None
    else:
        decision_number = None
        decision_date = None
        doc_type = "code"
        document = _short_doc_name(path.name)
        volume = _detect_volume(path.name)

    return [
        PageText(
            document=document,
            volume=volume,
            page=i + 1,
            text=_normalize(t),
            doc_type=doc_type,
            decision_number=decision_number,
            decision_date=decision_date,
        )
        for i, t in enumerate(cleaned_pages)
        if t.strip()
    ]


def load_all_pdfs(assets_dir: Path) -> list[PageText]:
    pages: list[PageText] = []
    pdfs = sorted(assets_dir.rglob("*.pdf"))
    if not pdfs:
        logger.warning("Aucun PDF trouvé dans %s", assets_dir)
    for pdf_path in pdfs:
        pages.extend(load_pdf(pdf_path, assets_dir=assets_dir))
    logger.info("Total pages extraites: %d", len(pages))
    return pages
