from __future__ import annotations
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.security import decode_token
from app.models.models import User, Club, Subscription

oauth2 = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2)) -> User:
    try:
        uid = decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.get(User, uid)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def get_club_or_404(db: Session, club_id: str) -> Club:
    club = db.get(Club, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    return club

def get_club_plan(db: Session, club_id: str) -> str:
    sub = db.query(Subscription).filter(Subscription.club_id==club_id, Subscription.is_active==True).order_by(Subscription.created_at.desc()).first()
    return sub.plan if sub else "free"
