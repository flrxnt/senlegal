"""Génération via Ollama Cloud + garde-fou de citations + fallback déterministe (droit sénégalais)."""
from __future__ import annotations

import logging
import re
from typing import Iterator

from ..config import get_settings
from ..rag.retriever import RetrievedChunk
from .model import get_client
from .prompts import REFUSAL_TEXT, build_messages

logger = logging.getLogger(__name__)

# Format strict imposé par le prompt : [Article X — document]
STRICT_CITATION_RE = re.compile(r"\[Article\s+([^\]\—\-]+?)\s*[—\-]\s*[^\]]+\]")
# Format souple : "article 53", "art. 53", "(article premier)" etc.
LOOSE_CITATION_RE = re.compile(
    r"(?i)\b(?:article|art\.?)\s+(premier|\d+(?:[\-\.]\d+)?)\b"
)


def _normalize_art(s: str) -> str:
    return re.sub(r"\s+", "", s).lower().strip(".:-")


def _allowed_articles(chunks: list[RetrievedChunk]) -> set[str]:
    return {_normalize_art(c.article_number) for c in chunks}


def extract_cited_articles(text: str) -> list[str]:
    """Liste des articles cités, tous formats confondus (strict + libre).

    Utilisé pour l'introspection / les tests. La validation, elle, n'utilise
    que le format strict (cf. ``extract_strict_citations``).
    """
    arts: list[str] = []
    for m in STRICT_CITATION_RE.finditer(text):
        arts.append(_normalize_art(m.group(1)))
    for m in LOOSE_CITATION_RE.finditer(text):
        arts.append(_normalize_art(m.group(1)))
    seen = set()
    out: list[str] = []
    for a in arts:
        if a not in seen:
            seen.add(a)
            out.append(a)
    return out


def extract_strict_citations(text: str) -> list[str]:
    """Articles cités au format imposé [Article X — document]."""
    seen: set[str] = set()
    out: list[str] = []
    for m in STRICT_CITATION_RE.finditer(text):
        a = _normalize_art(m.group(1))
        if a not in seen:
            seen.add(a)
            out.append(a)
    return out


def validate_citations(text: str, chunks: list[RetrievedChunk]) -> bool:
    """Une réponse est valide si elle contient au moins une citation au
    format strict ``[Article X — document]`` et que TOUTES les citations
    strictes pointent vers un article présent dans le contexte.

    Les mentions libres dans le texte ("Art. 50.", "article premier") sont
    ignorées : elles peuvent provenir des extraits cités eux-mêmes et ne
    reflètent pas nécessairement une citation à valider.
    """
    allowed = _allowed_articles(chunks)
    if not allowed:
        return False
    cited = extract_strict_citations(text)
    if not cited:
        return False
    return all(c in allowed for c in cited)


def _looks_like_garbage(text: str, question: str) -> bool:
    t = text.strip()
    if len(t) < 20:
        return True
    q_norm = re.sub(r"\W+", "", question.lower())
    t_norm = re.sub(r"\W+", "", t.lower())
    if q_norm and t_norm.startswith(q_norm) and len(t_norm) < len(q_norm) * 2:
        return True
    return False


def _is_low_quality(text: str) -> bool:
    if text.count("…") + text.count("...") >= 3:
        return True
    words = re.findall(r"[A-Za-zÀ-ÿ]{3,}", text)
    return len(words) < 10


def _format_sources(chunks: list[RetrievedChunk]) -> str:
    lines = ["Sources :"]
    for c in chunks:
        lines.append(f"- Article {c.article_number} — {c.document}, p. {c.page}")
    return "\n".join(lines)


def _deterministic_answer(chunks: list[RetrievedChunk]) -> str:
    """Fallback : extrait fidèle du chunk top de qualité acceptable + sources."""
    top = next((c for c in chunks if not _is_low_quality(c.text)), chunks[0])
    snippet = top.text.strip()
    if len(snippet) > 800:
        snippet = snippet[:800].rsplit(" ", 1)[0] + "…"
    intro = (
        "D'après les textes juridiques sénégalais, voici l'extrait le plus "
        f"pertinent (Article {top.article_number} — {top.document}, p. {top.page}) :\n\n"
    )
    body = f"« {snippet} »\n\n"
    tag = f"[Article {top.article_number} — {top.document}]\n\n"
    return intro + body + tag + _format_sources(chunks[:3])


def _post_process(text: str, chunks: list[RetrievedChunk]) -> str:
    text = _strip_intro(text)
    if re.search(r"(?i)\bsources?\s*:", text):
        return text
    return text.rstrip() + "\n\n" + _format_sources(chunks)


# Formules d'introduction à supprimer si le LLM les place malgré le prompt.
_INTRO_RE = re.compile(
    r"^\s*(?:"
    r"sur\s+la\s+base\s+(?:des|du)\s+(?:documents?|extraits?|contextes?|textes?)(?:\s+fournis?)?"
    r"|d['’]apr[èe]s\s+(?:les?|le|la)\s+(?:extraits?|contextes?|documents?|textes?)(?:\s+fournis?)?"
    r"|selon\s+(?:les?|le|la)\s+(?:extraits?|contextes?|documents?|textes?)(?:\s+fournis?)?"
    r"|en\s+me\s+basant\s+sur\s+(?:les?|le|la)\s+(?:extraits?|contextes?|documents?)"
    r"|voici\s+(?:la|une)\s+r[ée]ponse"
    r"|voici\s+ce\s+que\s+(?:disent|indique|pr[ée]cise)"
    r")\b[^\n.]*[.,:\-—]?\s*",
    re.IGNORECASE,
)


def _strip_intro(text: str) -> str:
    cleaned = _INTRO_RE.sub("", text, count=1).lstrip()
    if cleaned and cleaned[0].islower():
        cleaned = cleaned[0].upper() + cleaned[1:]
    return cleaned


def _ollama_options() -> dict:
    settings = get_settings()
    return {
        "temperature": settings.temperature,
        "top_p": 0.9,
        "repeat_penalty": settings.repetition_penalty,
        "num_predict": settings.max_new_tokens,
    }


def _chat(messages: list[dict], stream: bool):
    settings = get_settings()
    client = get_client()
    return client.chat(
        model=settings.model_name,
        messages=messages,
        options=_ollama_options(),
        stream=stream,
        keep_alive=settings.ollama_keep_alive,
    )


def _generate_once(question: str, chunks: list[RetrievedChunk]) -> str:
    messages = build_messages(question, chunks)
    response = _chat(messages, stream=False)
    # Compatibilité avec les versions du SDK (dict ou objet)
    msg = response["message"] if isinstance(response, dict) else response.message
    content = msg["content"] if isinstance(msg, dict) else msg.content
    return (content or "").strip()


def generate(question: str, chunks: list[RetrievedChunk]) -> tuple[str, bool]:
    """
    Renvoie (texte, used_context).
    - aucun chunk -> refus déterministe.
    - LLM exploitable + citations valides -> réponse post-processée.
    - LLM échoue (echo, vide) ou hallucine -> retry, puis fallback déterministe.
    - Erreur réseau Ollama -> fallback déterministe.
    """
    if not chunks:
        return REFUSAL_TEXT, False

    for attempt in range(2):
        try:
            text = _generate_once(question, chunks)
        except Exception as exc:  # noqa: BLE001
            logger.error("Erreur Ollama (tentative %d): %s", attempt + 1, exc)
            continue
        if text.strip() == REFUSAL_TEXT:
            return REFUSAL_TEXT, True
        if _looks_like_garbage(text, question):
            logger.warning("LLM inexploitable (tentative %d).", attempt + 1)
            continue
        if validate_citations(text, chunks):
            return _post_process(text, chunks), True
        logger.warning("Citation hors contexte ou absente (tentative %d).", attempt + 1)

    logger.warning("LLM non concluant -> fallback déterministe.")
    return _deterministic_answer(chunks), True


def stream_generate(question: str, chunks: list[RetrievedChunk]) -> Iterator[str]:
    """Streaming token par token via Ollama."""
    if not chunks:
        yield REFUSAL_TEXT
        return

    messages = build_messages(question, chunks)
    try:
        for part in _chat(messages, stream=True):
            msg = part["message"] if isinstance(part, dict) else part.message
            content = msg["content"] if isinstance(msg, dict) else msg.content
            if content:
                yield content
    except Exception as exc:  # noqa: BLE001
        logger.error("Erreur streaming Ollama: %s", exc)
        # Fallback streaming
        for line in _deterministic_answer(chunks).splitlines(keepends=True):
            yield line
