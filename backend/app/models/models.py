from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Boolean, ForeignKey, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.db import Base

def _uuid() -> str:
    return uuid.uuid4().hex

class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    clubs: Mapped[list["Club"]] = relationship("Club", back_populates="owner")

class Club(Base):
    __tablename__ = "clubs"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    owner_id: Mapped[str] = mapped_column(String(32), ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    sport: Mapped[str] = mapped_column(String(32), default="football")
    language: Mapped[str] = mapped_column(String(8), default="es")
    primary_color: Mapped[str] = mapped_column(String(16), default="#5b8cff")
    secondary_color: Mapped[str] = mapped_column(String(16), default="#2dd4bf")
    font_primary: Mapped[str] = mapped_column(String(128), default="Inter")
    font_secondary: Mapped[str] = mapped_column(String(128), default="Inter")
    locked_logo_asset_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    owner: Mapped["User"] = relationship("User", back_populates="clubs")
    subscriptions: Mapped[list["Subscription"]] = relationship("Subscription", back_populates="club")
    projects: Mapped[list["Project"]] = relationship("Project", back_populates="club")

class Subscription(Base):
    __tablename__ = "subscriptions"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    club_id: Mapped[str] = mapped_column(String(32), ForeignKey("clubs.id"), index=True)
    plan: Mapped[str] = mapped_column(String(32), default="free")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    renews_automatically: Mapped[bool] = mapped_column(Boolean, default=True)
    current_period_end: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    club: Mapped["Club"] = relationship("Club", back_populates="subscriptions")

class Template(Base):
    __tablename__ = "templates"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    origin: Mapped[str] = mapped_column(String(32), default="catalog")
    sport: Mapped[str] = mapped_column(String(32), default="football")
    pages: Mapped[int] = mapped_column(Integer, default=40)
    layout_signature: Mapped[str] = mapped_column(Text, default="{}")
    document_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Project(Base):
    __tablename__ = "projects"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    club_id: Mapped[str] = mapped_column(String(32), ForeignKey("clubs.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    template_id: Mapped[str] = mapped_column(String(64), default="")
    document_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    club: Mapped["Club"] = relationship("Club", back_populates="projects")

class Asset(Base):
    __tablename__ = "assets"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    club_id: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    filename: Mapped[str] = mapped_column(String(255))
    mime: Mapped[str] = mapped_column(String(128))
    storage_path: Mapped[str] = mapped_column(String(512))
    is_catalog: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
