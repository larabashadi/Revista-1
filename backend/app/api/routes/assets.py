from __future__ import annotations
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.api.deps import get_current_user
from app.models.models import Club, Asset
from app.services.storage import save_local_file, get_local_path

router = APIRouter(prefix="/api/assets", tags=["assets"])

@router.post("/{club_id}")
async def upload_asset(club_id: str, file: UploadFile = File(...), db: Session = Depends(get_db), user=Depends(get_current_user)):
    club = db.get(Club, club_id)
    if not club or club.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Club not found")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty upload")
    asset_id, _path = save_local_file(content, file.filename or "asset.bin")
    # Store the logical storage key (asset_id). The storage service knows how to resolve it.
    asset = Asset(
        id=asset_id,
        club_id=club.id,
        filename=file.filename or "asset.bin",
        mime=file.content_type or "application/octet-stream",
        storage_path=asset_id,
    )
    db.add(asset); db.commit()
    return {"id": asset_id, "url": f"/api/assets/file/{asset_id}", "filename": asset.filename, "mime": asset.mime}

@router.get("/file/{asset_id}")
def get_asset_file(asset_id: str):
    try:
        path = get_local_path(asset_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Asset not found")
    return FileResponse(path)
