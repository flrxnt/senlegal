"""Extraction de texte depuis les PDFs du Recueil."""
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


def _short_doc_name(filename: str) -> str:
    vol = _detect_volume(filename)
    if vol:
        return f"Recueil des textes juridiques de la commande publique — {vol}"
    return Path(filename).stem


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


def load_pdf(path: Path) -> list[PageText]:
    """Charge un PDF et renvoie une liste de PageText nettoyés."""
    document = _short_doc_name(path.name)
    volume = _detect_volume(path.name)
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
    return [
        PageText(
            document=document,
            volume=volume,
            page=i + 1,
            text=_normalize(t),
        )
        for i, t in enumerate(cleaned_pages)
        if t.strip()
    ]


def load_all_pdfs(assets_dir: Path) -> list[PageText]:
    pages: list[PageText] = []
    pdfs = sorted(assets_dir.glob("*.pdf"))
    if not pdfs:
        logger.warning("Aucun PDF trouvé dans %s", assets_dir)
    for pdf_path in pdfs:
        pages.extend(load_pdf(pdf_path))
    logger.info("Total pages extraites: %d", len(pages))
    return pages
