from __future__ import annotations
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.api.deps import get_current_user, get_club_or_404
from app.models.models import Project, Template
from app.schemas.schemas import ProjectCreate, ProjectOut, ProjectUpdate

router = APIRouter(prefix="/api/projects", tags=["projects"])

@router.get("/{club_id}")
def list_projects(club_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    club = get_club_or_404(db, club_id)
    if club.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    items = db.query(Project).filter(Project.club_id==club_id).order_by(Project.updated_at.desc()).all()
    return {"projects":[{"id":p.id,"name":p.name,"template_id":p.template_id,"updated_at":p.updated_at.isoformat()+"Z"} for p in items]}

@router.post("/{club_id}", response_model=ProjectOut)
def create_project(club_id: str, payload: ProjectCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    club = get_club_or_404(db, club_id)
    if club.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    t = db.get(Template, payload.template_id)
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    doc = json.loads(t.document_json)
    proj = Project(club_id=club_id, name=payload.name, template_id=t.id, document_json=json.dumps(doc, ensure_ascii=False))
    db.add(proj); db.commit(); db.refresh(proj)
    return ProjectOut(id=proj.id, club_id=proj.club_id, name=proj.name, template_id=proj.template_id, document=doc)

@router.get("/item/{project_id}", response_model=ProjectOut)
def get_project(project_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    proj = db.get(Project, project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    club = get_club_or_404(db, proj.club_id)
    if club.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return ProjectOut(id=proj.id, club_id=proj.club_id, name=proj.name, template_id=proj.template_id, document=json.loads(proj.document_json))

@router.put("/item/{project_id}", response_model=ProjectOut)
def update_project(project_id: str, payload: ProjectUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    proj = db.get(Project, project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    club = get_club_or_404(db, proj.club_id)
    if club.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    if payload.name is not None:
        proj.name = payload.name
    proj.document_json = json.dumps(payload.document, ensure_ascii=False)
    proj.updated_at = datetime.utcnow()
    db.commit(); db.refresh(proj)
    return ProjectOut(id=proj.id, club_id=proj.club_id, name=proj.name, template_id=proj.template_id, document=json.loads(proj.document_json))
