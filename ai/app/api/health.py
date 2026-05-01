from fastapi import APIRouter

from ..config import get_settings
from ..llm.model import health_check, is_loaded
from ..rag.vectorstore import count
from ..schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    chroma_ok = True
    try:
        chunks = count(settings.chroma_path, settings.collection_name)
    except Exception:  # noqa: BLE001
        chunks = 0
        chroma_ok = False
    ollama = health_check()
    return HealthResponse(
        status="ok" if (ollama["ok"] and chroma_ok) else "degraded",
        llm_loaded=is_loaded() and ollama["ok"],
        embedder_loaded=True,
        chunks_indexed=chunks,
        collection=settings.collection_name,
        chroma_ok=chroma_ok,
        chroma_mode="http" if settings.chroma_host else "persistent",
    )
