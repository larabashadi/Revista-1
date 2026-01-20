from __future__ import annotations
import json
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.models.models import Project, Club
from app.services.pdf_exporter import export_document_to_pdf
from app.services.storage import get_local_path, save_local_file

def resolve_asset_path(asset_id: str) -> str:
    return get_local_path(asset_id)

def export_project_job(project_id: str, club_id: str, payload: Dict[str, Any], db_url: str):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    engine = create_engine(db_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    db: Session = SessionLocal()
    try:
        proj: Project | None = db.get(Project, project_id)
        club: Club | None = db.get(Club, club_id)
        if not proj or not club:
            return {"ok": False, "error": "Project/Club not found"}
        doc = json.loads(proj.document_json)
        locked = club.locked_logo_asset_id
        if locked:
            for p in doc.get("pages", [])[:1]:
                for layer in p.get("layers", []):
                    for it in layer.get("items", []):
                        if it.get("type")=="LockedLogoStamp" and str(it.get("assetRef","")).startswith("{{"):
                            it["assetRef"] = locked
        pdf_bytes = export_document_to_pdf(doc, resolve_asset_path, quality=payload.get("quality","web"), bleed_mm=float(payload.get("bleed_mm",3.0)), crop_marks=bool(payload.get("crop_marks",True)), watermark=bool(payload.get("watermark",False)))
        export_id, _ = save_local_file(pdf_bytes, f"{proj.name}.pdf")
        return {"ok": True, "export_asset_id": export_id}
    finally:
        db.close()
