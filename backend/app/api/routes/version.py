from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["meta"])

@router.get("/version")
def version():
    return {"version": "10.3.1-completa+build3"}
