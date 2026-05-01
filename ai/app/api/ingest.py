from fastapi import APIRouter, BackgroundTasks, File, Form, Header, HTTPException, UploadFile, status

from ..config import get_settings
from ..rag.ingestion import run_ingestion
from ..rag.single_ingest import delete_source, ingest_pdf_bytes
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


@router.post("/ingest/file")
async def ingest_file(
    file: UploadFile = File(...),
    source_id: str = Form(...),
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
) -> dict:
    """Indexe un PDF unique uploadé par le backend, sous l'identifiant
    ``source_id`` (Document.id côté backend).

    Synchrone : retourne le résultat (pages, chunks, doc_type) une fois
    l'indexation terminée. Le backend appelle cet endpoint en arrière-plan
    et met à jour le statut du Document en base.
    """
    _check_admin(x_admin_token)
    if not source_id or not source_id.strip():
        raise HTTPException(status_code=400, detail="source_id requis.")
    if not file.filename:
        raise HTTPException(status_code=400, detail="filename manquant.")
    if file.content_type and "pdf" not in file.content_type.lower():
        # On reste tolérant (certains clients envoient application/octet-stream)
        pass
    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Fichier vide.")
    try:
        result = ingest_pdf_bytes(
            pdf_bytes=pdf_bytes,
            filename=file.filename,
            source_id=source_id.strip(),
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Échec ingestion : {exc}") from exc
    return result


@router.delete("/ingest/source/{source_id}")
def delete_ingest_source(
    source_id: str,
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
) -> dict:
    """Supprime tous les chunks Chroma indexés sous ce ``source_id``."""
    _check_admin(x_admin_token)
    if not source_id.strip():
        raise HTTPException(status_code=400, detail="source_id requis.")
    try:
        return delete_source(source_id.strip())
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc

