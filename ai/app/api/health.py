from fastapi import APIRouter

from ..config import get_settings
from ..llm.model import health_check, is_loaded
from ..rag.vectorstore import count
from ..schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    chunks = count(settings.chroma_path, settings.collection_name)
    ollama = health_check()
    return HealthResponse(
        status="ok" if ollama["ok"] else "degraded",
        llm_loaded=is_loaded() and ollama["ok"],
        embedder_loaded=True,
        chunks_indexed=chunks,
        collection=settings.collection_name,
    )
