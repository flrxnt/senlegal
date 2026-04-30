"""Réécriture conservative des requêtes utilisateur avant RAG.

Le but est uniquement de remettre la question au propre : orthographe,
espacement, ponctuation, accents et casse. Le sens, les entités citées,
les sigles et l'intention doivent rester strictement inchangés.
"""
from __future__ import annotations

import logging
import re

from ..config import get_settings
from .model import get_client

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Tu corriges uniquement la forme d'une question utilisateur en français. "
    "Corrige l'orthographe, les accents, la ponctuation, les apostrophes, la casse "
    "et les espaces. N'ajoute aucune information. N'enlève aucune information. "
    "Ne reformule pas le sens. Ne développe pas les sigles. Ne réponds pas à la question. "
    "Retourne uniquement la question nettoyée, sur une seule ligne."
)


def _basic_cleanup(text: str) -> str:
    cleaned = " ".join(text.split())
    cleaned = re.sub(r"\s+([,;:!?])", r"\1", cleaned)
    cleaned = re.sub(r"([([{])\s+", r"\1", cleaned)
    cleaned = re.sub(r"\s+([)\]}])", r"\1", cleaned)
    cleaned = re.sub(r"\b[cC]\s+est\b", "C'est", cleaned)
    cleaned = re.sub(r"\b[jJ]\s+ai\b", "J'ai", cleaned)
    cleaned = re.sub(r"\b[dD]\s+accord\b", "d'accord", cleaned)
    if cleaned and cleaned[0].isalpha():
        cleaned = cleaned[0].upper() + cleaned[1:]
    return cleaned.strip()


def _is_safe_rewrite(original: str, rewritten: str) -> bool:
    if not rewritten:
        return False
    original_tokens = re.findall(r"\w+", original.lower())
    rewritten_tokens = re.findall(r"\w+", rewritten.lower())
    if not original_tokens or not rewritten_tokens:
        return False
    overlap = set(original_tokens) & set(rewritten_tokens)
    return len(overlap) >= max(1, int(len(set(original_tokens)) * 0.6))


def rewrite_query(query: str) -> str:
    """Nettoie la requête pour le retriever, sans modifier son sens."""
    settings = get_settings()
    baseline = _basic_cleanup(query)
    if not settings.query_rewrite_enabled:
        return baseline

    try:
        client = get_client()
        response = client.chat(
            model=settings.model_name,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": query},
            ],
            options={
                "temperature": 0,
                "num_predict": 96,
                "top_p": 0.1,
            },
            stream=False,
            keep_alive=settings.ollama_keep_alive,
        )
        msg = response["message"] if isinstance(response, dict) else response.message
        content = msg["content"] if isinstance(msg, dict) else msg.content
        rewritten = _basic_cleanup((content or "").strip())
        if _is_safe_rewrite(query, rewritten):
            if rewritten != query:
                logger.info("Requête nettoyée pour RAG: %r -> %r", query, rewritten)
            return rewritten
        logger.warning("Réécriture rejetée, fallback local utilisé: %r", rewritten)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Réécriture indisponible, fallback local utilisé: %s", exc)

    return baseline