"""Client Ollama Cloud singleton."""
from __future__ import annotations

import logging
import threading

from ..config import get_settings

logger = logging.getLogger(__name__)

_LOCK = threading.Lock()
_CLIENT = None


def get_client():
    """Renvoie un client Ollama configuré pour le cloud (ou local si OLLAMA_HOST=localhost)."""
    global _CLIENT
    if _CLIENT is not None:
        return _CLIENT
    with _LOCK:
        if _CLIENT is None:
            from ollama import Client

            settings = get_settings()
            headers = {}
            if settings.ollama_api_key:
                headers["Authorization"] = f"Bearer {settings.ollama_api_key}"
            logger.info("Initialisation client Ollama: %s", settings.ollama_host)
            _CLIENT = Client(host=settings.ollama_host, headers=headers, timeout=120)
    return _CLIENT


def is_loaded() -> bool:
    """Compatibilité avec l'ancien get_llm — toujours True dès que la config existe."""
    settings = get_settings()
    return bool(settings.ollama_host) and (
        settings.ollama_host.startswith("http://localhost")
        or settings.ollama_host.startswith("http://127.")
        or bool(settings.ollama_api_key)
    )


def health_check() -> dict:
    """Ping rapide du backend Ollama."""
    try:
        client = get_client()
        # /api/tags est l'endpoint le plus léger
        client.list()
        return {"ok": True}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}
