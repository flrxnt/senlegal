from __future__ import annotations

import logging
import threading
import time
from typing import Any

from fastapi import APIRouter, BackgroundTasks, File, Form, Header, HTTPException, UploadFile, status

from ..config import get_settings
from ..rag.ingestion import run_ingestion
from ..rag.single_ingest import delete_source, ingest_pdf_bytes
from ..schemas import IngestResponse

router = APIRouter()
logger = logging.getLogger(__name__)

# ── Suivi des tâches d'ingestion en mémoire ──────────────────────────────────
# Clé = source_id, valeur = dict avec status / progress / result / error.
# Réinitialisé au redémarrage du service (le backend re-poll et re-déclenche
# si nécessaire via le statut PROCESSING en base).
_tasks: dict[str, dict[str, Any]] = {}
_tasks_lock = threading.Lock()

_TASK_TTL_SECONDS = 3600  # nettoyage après 1 h


def _cleanup_old_tasks() -> None:
    now = time.time()
    with _tasks_lock:
        expired = [
            sid for sid, t in _tasks.items()
            if t.get("status") in ("ok", "failed", "empty") and now - t.get("finished_at", now) > _TASK_TTL_SECONDS
        ]
        for sid in expired:
            del _tasks[sid]


def _check_admin(token: str | None) -> None:
    settings = get_settings()
    if not token or token != settings.admin_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin token invalide.",
        )


# ── Background worker ────────────────────────────────────────────────────────

def _run_ingest_worker(source_id: str, pdf_bytes: bytes, filename: str) -> None:
    """Exécuté dans un thread dédié — ne bloque pas le worker uvicorn."""
    def on_progress(done: int, total: int) -> None:
        with _tasks_lock:
            task = _tasks.get(source_id)
            if task:
                task["chunks_done"] = done
                task["chunks_total"] = total

    try:
        result = ingest_pdf_bytes(
            pdf_bytes=pdf_bytes,
            filename=filename,
            source_id=source_id,
            on_progress=on_progress,
        )
        with _tasks_lock:
            _tasks[source_id] = {
                **result,
                "finished_at": time.time(),
            }
        logger.info("Ingestion terminée source_id=%s chunks=%s", source_id, result.get("chunks"))
    except Exception as exc:  # noqa: BLE001
        logger.error("Ingestion échouée source_id=%s : %s", source_id, exc)
        with _tasks_lock:
            _tasks[source_id] = {
                "status": "failed",
                "source_id": source_id,
                "error": str(exc),
                "finished_at": time.time(),
            }


# ── Routes ────────────────────────────────────────────────────────────────────

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


@router.post("/ingest/file", status_code=202)
async def ingest_file(
    file: UploadFile = File(...),
    source_id: str = Form(...),
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
) -> dict:
    """Accepte un PDF et lance l'indexation dans un thread dédié.

    Retourne immédiatement ``202 Accepted``. Le backend peut suivre
    la progression via ``GET /ingest/status/{source_id}``.
    """
    _check_admin(x_admin_token)
    sid = source_id.strip()
    if not sid:
        raise HTTPException(status_code=400, detail="source_id requis.")
    if not file.filename:
        raise HTTPException(status_code=400, detail="filename manquant.")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Fichier vide.")

    with _tasks_lock:
        current = _tasks.get(sid)
        if current and current.get("status") == "processing":
            raise HTTPException(status_code=409, detail="Ingestion déjà en cours pour ce source_id.")
        _tasks[sid] = {
            "status": "processing",
            "source_id": sid,
            "chunks_done": 0,
            "chunks_total": 0,
        }

    thread = threading.Thread(
        target=_run_ingest_worker,
        args=(sid, pdf_bytes, file.filename),
        daemon=True,
    )
    thread.start()

    _cleanup_old_tasks()

    return {"status": "accepted", "source_id": sid}


@router.get("/ingest/status/{source_id}")
def ingest_status(
    source_id: str,
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
) -> dict:
    """Retourne la progression / le résultat de l'ingestion d'un source_id."""
    _check_admin(x_admin_token)
    with _tasks_lock:
        task = _tasks.get(source_id.strip())
    if not task:
        return {"status": "not_found", "source_id": source_id}
    return task


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
