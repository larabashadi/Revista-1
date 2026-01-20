from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from rq import Queue
import redis

from app.core.db import get_db
from app.core.settings import settings
from app.api.deps import get_current_user, get_club_plan, get_club_or_404
from app.models.models import Project
from app.schemas.schemas import ExportRequest
from app.jobs import export_project_job
from app.services.storage import get_local_path

router = APIRouter(prefix="/api/export", tags=["export"])
redis_conn = redis.from_url(settings.REDIS_URL)
q = Queue("default", connection=redis_conn)

@router.post("/{project_id}")
def export_project(project_id: str, payload: ExportRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    proj = db.get(Project, project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    club = get_club_or_404(db, proj.club_id)
    if club.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    plan = get_club_plan(db, club.id)
    watermark = True if plan != "pro" else False
    # allow demo export with watermark for free (conversion-friendly)
    body = payload.model_dump()
    body["watermark"] = watermark
    job = q.enqueue(export_project_job, proj.id, club.id, body, settings.DATABASE_URL, job_timeout=300)
    return {"job_id": job.get_id(), "watermark": watermark, "plan": plan}

@router.get("/job/{job_id}")
def export_status(job_id: str):
    job = q.fetch_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.is_failed:
        return {"status":"failed", "error": str(job.exc_info)}
    if job.is_finished:
        return {"status":"finished", **(job.result or {})}
    return {"status":"queued"}


# Backwards-compatible alias (older frontend builds polled /status/{job_id})
@router.get("/status/{job_id}")
def export_status_alias(job_id: str):
    return export_status(job_id)

@router.get("/download/{asset_id}")
def download_export(asset_id: str):
    try:
        path = get_local_path(asset_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, media_type="application/pdf", filename="revista.pdf")
