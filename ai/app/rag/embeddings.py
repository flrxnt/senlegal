"""Wrapper autour de sentence-transformers (E5 multilingual)."""
from __future__ import annotations

import logging
import threading
from typing import Sequence

import numpy as np

logger = logging.getLogger(__name__)

_LOCK = threading.Lock()
_MODEL = None
_MODEL_NAME: str | None = None


def get_embedder(model_name: str):
    global _MODEL, _MODEL_NAME
    if _MODEL is not None and _MODEL_NAME == model_name:
        return _MODEL
    with _LOCK:
        if _MODEL is None or _MODEL_NAME != model_name:
            from sentence_transformers import SentenceTransformer

            logger.info("Chargement du modèle d'embeddings: %s", model_name)
            _MODEL = SentenceTransformer(model_name, device="cpu")
            _MODEL_NAME = model_name
    return _MODEL


def embed_passages(model_name: str, texts: Sequence[str]) -> np.ndarray:
    model = get_embedder(model_name)
    prefixed = [f"passage: {t}" for t in texts]
    return model.encode(
        prefixed,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
        batch_size=16,
    )


def embed_query(model_name: str, text: str) -> np.ndarray:
    model = get_embedder(model_name)
    out = model.encode(
        [f"query: {text}"],
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )
    return out[0]
