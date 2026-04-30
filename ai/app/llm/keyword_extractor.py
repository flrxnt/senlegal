"""Extraction de mots-clés et de correspondances juridiques pour enrichir le RAG.

L'utilisateur formule sa question en langage naturel (« je n'ai pas été
sélectionné, que faire ? »). Les textes officiels utilisent du vocabulaire
juridique précis (« candidat évincé », « recours », « Comité de Règlement des
Différends »…). On demande au LLM de proposer une liste courte de termes et
synonymes du domaine, qui seront concaténés à la requête envoyée au retriever.

L'objectif n'est PAS de répondre à la question, mais d'enrichir le vecteur de
recherche pour rapprocher la requête utilisateur du vocabulaire des textes.
"""
from __future__ import annotations

import json
import logging
import re

from ..config import get_settings
from .model import get_client

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = (
    "Tu es un assistant qui extrait des mots-clés du vocabulaire juridique du "
    "Code des marchés publics du Sénégal et du Recueil de la commande publique.\n"
    "À partir d'une question utilisateur formulée en langage courant, tu produis "
    "une liste courte (max 10) de termes, synonymes, expressions et sigles "
    "officiels susceptibles d'apparaître dans les textes de loi sénégalais sur la "
    "commande publique et qui aideraient à retrouver les articles pertinents.\n\n"
    "RÈGLES :\n"
    "- N'invente pas de noms d'institutions ou de procédures qui n'existent pas.\n"
    "- Préfère le vocabulaire juridique formel (ex. \"candidat évincé\" plutôt que "
    "\"perdant\", \"soumissionnaire\" plutôt que \"participant\").\n"
    "- Inclus les sigles connus (ARCOP, DCMP, CRD, AOO, AOR, DRP, CMP, etc.) et "
    "leurs formes développées quand c'est pertinent.\n"
    "- Pas de phrases, uniquement des expressions courtes (1 à 5 mots).\n"
    "- Réponds UNIQUEMENT avec un objet JSON de la forme : "
    '{\"keywords\": [\"...\", \"...\"]}. Aucun texte avant ou après.'
)


_FEWSHOT_USER = (
    "Question : J'ai en tant que fournisseur soumis à un appel d'offres mais je "
    "n'ai pas été sélectionné, que faire ?"
)
_FEWSHOT_ASSISTANT = json.dumps(
    {
        "keywords": [
            "soumissionnaire",
            "candidat évincé",
            "attribution provisoire",
            "notification d'attribution",
            "recours",
            "contestation",
            "Comité de Règlement des Différends",
            "CRD",
            "ARCOP",
            "débriefing",
        ]
    },
    ensure_ascii=False,
)


_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


def _parse_keywords(content: str) -> list[str]:
    if not content:
        return []
    match = _JSON_OBJECT_RE.search(content)
    if not match:
        return []
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return []
    raw = data.get("keywords") if isinstance(data, dict) else None
    if not isinstance(raw, list):
        return []
    seen: set[str] = set()
    out: list[str] = []
    for item in raw:
        if not isinstance(item, str):
            continue
        kw = " ".join(item.split()).strip(" .;,:-")
        if not kw or len(kw) > 80:
            continue
        key = kw.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(kw)
        if len(out) >= 10:
            break
    return out


def extract_keywords(question: str) -> list[str]:
    """Renvoie une liste de termes juridiques utiles pour enrichir le RAG.

    Toujours non-bloquant : en cas d'erreur LLM ou de réponse mal formée,
    renvoie une liste vide et le pipeline retombe sur la requête nettoyée.
    """
    settings = get_settings()
    if not settings.keyword_extraction_enabled:
        return []
    if not question or not question.strip():
        return []

    try:
        client = get_client()
        response = client.chat(
            model=settings.model_name,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": _FEWSHOT_USER},
                {"role": "assistant", "content": _FEWSHOT_ASSISTANT},
                {"role": "user", "content": f"Question : {question.strip()}"},
            ],
            options={
                "temperature": 0,
                "top_p": 0.1,
                "num_predict": 256,
            },
            stream=False,
            format="json",
            keep_alive=settings.ollama_keep_alive,
        )
        msg = response["message"] if isinstance(response, dict) else response.message
        content = msg["content"] if isinstance(msg, dict) else msg.content
        keywords = _parse_keywords(content or "")
        if keywords:
            logger.info("Mots-clés extraits pour RAG: %s", keywords)
        else:
            logger.warning("Aucun mot-clé exploitable (réponse LLM: %r)", content)
        return keywords
    except TypeError:
        # Certaines anciennes versions du SDK ollama ne supportent pas `format="json"`.
        try:
            client = get_client()
            response = client.chat(
                model=settings.model_name,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": _FEWSHOT_USER},
                    {"role": "assistant", "content": _FEWSHOT_ASSISTANT},
                    {"role": "user", "content": f"Question : {question.strip()}"},
                ],
                options={
                    "temperature": 0,
                    "top_p": 0.1,
                    "num_predict": 256,
                },
                stream=False,
                keep_alive=settings.ollama_keep_alive,
            )
            msg = response["message"] if isinstance(response, dict) else response.message
            content = msg["content"] if isinstance(msg, dict) else msg.content
            return _parse_keywords(content or "")
        except Exception as exc:  # noqa: BLE001
            logger.warning("Extraction de mots-clés indisponible: %s", exc)
            return []
    except Exception as exc:  # noqa: BLE001
        logger.warning("Extraction de mots-clés indisponible: %s", exc)
        return []


def build_enriched_query(question: str, keywords: list[str]) -> str:
    """Concatène la question et les mots-clés pour l'embedding du retriever."""
    if not keywords:
        return question
    return f"{question.strip()} | mots-clés: {', '.join(keywords)}"
