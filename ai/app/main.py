import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import chat as chat_api
from .api import health as health_api
from .api import ingest as ingest_api
from .api import search as search_api
from .config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("senlegal")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("Démarrage SenLegal AI — modèle=%s", settings.model_name)
    # Pré-chargement paresseux (le LLM se charge à la première requête /chat
    # pour ne pas bloquer le démarrage). Embeddings idem.
    yield
    logger.info("Arrêt SenLegal AI.")


app = FastAPI(
    title="SenLegal AI",
    description="API RAG ancrée sur le Code des marchés publics du Sénégal.",
    version="0.1.0",
    lifespan=lifespan,
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_api.router, tags=["meta"])
app.include_router(search_api.router, tags=["rag"])
app.include_router(chat_api.router, tags=["chat"])
app.include_router(ingest_api.router, tags=["admin"])
