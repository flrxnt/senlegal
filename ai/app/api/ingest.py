from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, status

from ..config import get_settings
from ..rag.ingestion import run_ingestion
from ..schemas import IngestResponse

router = APIRouter()


def _check_admin(token: str | None) -> None:
    settings = get_settings()
    if not token or token != settings.admin_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin token invalide.",
        )


@router.post("/ingest", response_model=IngestResponse)
def ingest(
    background: BackgroundTasks,
    force: bool = False,
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
) -> IngestResponse:
    _check_admin(x_admin_token)
    background.add_task(run_ingestion, force=force)
    return IngestResponse(
        status="scheduled",
        detail=f"Ingestion lancée en arrière-plan (force={force}).",
    )


@router.post("/ingest/sync", response_model=IngestResponse)
def ingest_sync(
    force: bool = False,
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
) -> IngestResponse:
    _check_admin(x_admin_token)
    result = run_ingestion(force=force)
    return IngestResponse(status=result.get("status", "ok"), detail=str(result))
