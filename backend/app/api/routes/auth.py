from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.models.models import User
from app.schemas.schemas import UserCreate, TokenOut

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register", response_model=TokenOut)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    if db.query(User).filter(User.email==email).first():
        raise HTTPException(status_code=400, detail="Email already exists")
    user = User(email=email, password_hash=hash_password(payload.password))
    db.add(user); db.commit(); db.refresh(user)
    return TokenOut(access_token=create_access_token(user.id))

@router.post("/login", response_model=TokenOut)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    email = (form.username or "").strip().lower()
    user = db.query(User).filter(User.email==email).first()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenOut(access_token=create_access_token(user.id))
