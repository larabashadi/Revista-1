from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Any, Optional, Dict

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserCreate(BaseModel):
    email: str
    password: str

class ClubCreate(BaseModel):
    name: str
    sport: str = "football"
    language: str = "es"
    primary_color: str = "#5b8cff"
    secondary_color: str = "#2dd4bf"
    font_primary: str = "Inter"
    font_secondary: str = "Inter"

class ClubOut(BaseModel):
    id: str
    name: str
    sport: str
    language: str
    primary_color: str
    secondary_color: str
    font_primary: str
    font_secondary: str
    locked_logo_asset_id: Optional[str] = None
    plan: str = "free"

class TemplateOut(BaseModel):
    id: str
    name: str
    origin: str
    sport: str
    pages: int

class TemplateGenerateRequest(BaseModel):
    sport: str = "football"
    style: str = "minimal_premium"
    weights: Dict[str, float] = Field(default_factory=lambda: {
        "matches": 0.25, "players": 0.25, "sponsors": 0.2, "academy": 0.15, "interviews": 0.1, "custom": 0.05
    })
    density: str = "medium"
    image_bias: str = "medium"

class ProjectCreate(BaseModel):
    template_id: str
    name: str

class ProjectOut(BaseModel):
    id: str
    club_id: str
    name: str
    template_id: str
    document: Dict[str, Any]

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    document: Dict[str, Any]

class ExportRequest(BaseModel):
    quality: str = "web"
    color_mode: str = "rgb"
    bleed_mm: float = 3.0
    crop_marks: bool = True
    watermark: bool = False

class ImportPdfRequest(BaseModel):
    mode: str = "safe"
    preset: str = "smart"
