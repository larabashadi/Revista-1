from __future__ import annotations
import time
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.api.deps import get_current_user, get_club_plan
from app.models.models import Club, Subscription, Asset
from app.schemas.schemas import ClubCreate, ClubOut
from app.services.storage import save_local_file

router = APIRouter(prefix="/api/clubs", tags=["clubs"])

@router.post("", response_model=ClubOut)
def create_club(payload: ClubCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    club = Club(owner_id=user.id, name=payload.name, sport=payload.sport, language=payload.language,
                primary_color=payload.primary_color, secondary_color=payload.secondary_color,
                font_primary=payload.font_primary, font_secondary=payload.font_secondary)
    db.add(club); db.commit(); db.refresh(club)
    sub = Subscription(club_id=club.id, plan="free", is_active=True, renews_automatically=True, current_period_end=int(time.time())+365*24*3600)
    db.add(sub); db.commit()
    return ClubOut(id=club.id, name=club.name, sport=club.sport, language=club.language,
                   primary_color=club.primary_color, secondary_color=club.secondary_color,
                   font_primary=club.font_primary, font_secondary=club.font_secondary,
                   locked_logo_asset_id=club.locked_logo_asset_id, plan="free")

@router.get("", response_model=list[ClubOut])
def list_my_clubs(db: Session = Depends(get_db), user=Depends(get_current_user)):
    clubs = db.query(Club).filter(Club.owner_id==user.id).order_by(Club.created_at.desc()).all()
    out=[]
    for c in clubs:
        out.append(ClubOut(id=c.id, name=c.name, sport=c.sport, language=c.language,
                           primary_color=c.primary_color, secondary_color=c.secondary_color,
                           font_primary=c.font_primary, font_secondary=c.font_secondary,
                           locked_logo_asset_id=c.locked_logo_asset_id, plan=get_club_plan(db, c.id)))
    return out

@router.post("/{club_id}/locked-logo", response_model=ClubOut)
async def upload_locked_logo(club_id: str, file: UploadFile = File(...), db: Session = Depends(get_db), user=Depends(get_current_user)):
    club = db.get(Club, club_id)
    if not club or club.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Club not found")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty upload")
    asset_id, path = save_local_file(content, file.filename or "logo.png")
    asset = Asset(id=asset_id, club_id=club.id, filename=file.filename or "logo.png", mime=file.content_type or "image/png", storage_path=path)
    db.add(asset)
    club.locked_logo_asset_id = asset_id
    db.commit(); db.refresh(club)
    return ClubOut(id=club.id, name=club.name, sport=club.sport, language=club.language,
                   primary_color=club.primary_color, secondary_color=club.secondary_color,
                   font_primary=club.font_primary, font_secondary=club.font_secondary,
                   locked_logo_asset_id=club.locked_logo_asset_id, plan=get_club_plan(db, club.id))

@router.post("/{club_id}/dev/activate-pro", response_model=ClubOut)
def dev_activate_pro(club_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    club = db.get(Club, club_id)
    if not club or club.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Club not found")
    sub = Subscription(club_id=club.id, plan="pro", is_active=True, renews_automatically=True, current_period_end=int(time.time())+365*24*3600)
    db.add(sub); db.commit()
    return ClubOut(id=club.id, name=club.name, sport=club.sport, language=club.language,
                   primary_color=club.primary_color, secondary_color=club.secondary_color,
                   font_primary=club.font_primary, font_secondary=club.font_secondary,
                   locked_logo_asset_id=club.locked_logo_asset_id, plan="pro")
