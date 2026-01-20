from __future__ import annotations

import io, os, uuid, math, random
from typing import Dict, List, Tuple
from PIL import Image, ImageDraw, ImageFont

from sqlalchemy.orm import Session
from app.models.models import Asset
from app.services.storage import save_local_file

# Simple, copyright-safe placeholder assets that look "editorial".
# These are NOT real photos; they are generated compositions.

def _font(size: int):
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size=size)
    except Exception:
        return ImageFont.load_default()

def _gradient(w: int, h: int, c1: Tuple[int,int,int], c2: Tuple[int,int,int]):
    im = Image.new("RGB", (w, h), c1)
    px = im.load()
    for y in range(h):
        t = y / max(1, h-1)
        r = int(c1[0]*(1-t) + c2[0]*t)
        g = int(c1[1]*(1-t) + c2[1]*t)
        b = int(c1[2]*(1-t) + c2[2]*t)
        for x in range(w):
            px[x,y] = (r,g,b)
    return im

def _hero(kind: str, accent: Tuple[int,int,int]) -> bytes:
    w,h = 1600, 1000
    base = _gradient(w,h, (15,18,30), accent)
    d = ImageDraw.Draw(base)
    # geometric waves
    for i in range(10):
        y = int(h*(i/10))
        d.ellipse((-200, y-80, w+200, y+200), outline=(255,255,255,30), width=3)
    # title stamp
    d.rounded_rectangle((60,60,560,180), radius=26, fill=(0,0,0,120))
    d.text((90,92), f"HERO {kind.upper()}", fill=(255,255,255,235), font=_font(46))
    # fake action silhouette
    cx, cy = int(w*0.72), int(h*0.62)
    d.ellipse((cx-210, cy-210, cx+210, cy+210), fill=(255,255,255,28))
    d.rounded_rectangle((cx-60, cy-180, cx+60, cy+200), radius=60, fill=(255,255,255,65))
    d.ellipse((cx-80, cy-260, cx+80, cy-100), fill=(255,255,255,85))
    buf = io.BytesIO()
    base.save(buf, format="PNG", optimize=True)
    return buf.getvalue()

def _portrait(label: str, accent: Tuple[int,int,int]) -> bytes:
    w,h = 900, 1100
    base = _gradient(w,h, (245,247,252), (220,230,255))
    d = ImageDraw.Draw(base)
    # frame
    d.rounded_rectangle((40,40,w-40,h-40), radius=46, outline=accent+(255,), width=10)
    # face
    cx, cy = w//2, int(h*0.42)
    d.ellipse((cx-160, cy-160, cx+160, cy+160), fill=(230,235,245))
    d.ellipse((cx-60, cy-40, cx-10, cy+10), fill=(120,130,150))
    d.ellipse((cx+10, cy-40, cx+60, cy+10), fill=(120,130,150))
    d.arc((cx-70, cy+20, cx+70, cy+120), start=0, end=180, fill=(120,130,150), width=6)
    d.text((70, h-200), label, fill=(20,24,32), font=_font(44))
    d.text((70, h-140), "Foto de ejemplo", fill=(80,90,110), font=_font(28))
    buf = io.BytesIO()
    base.save(buf, format="PNG", optimize=True)
    return buf.getvalue()

def _sponsor_logo(name: str, accent: Tuple[int,int,int]) -> bytes:
    w,h = 900, 500
    base = Image.new("RGBA", (w,h), (255,255,255,0))
    d = ImageDraw.Draw(base)
    d.rounded_rectangle((20,20,w-20,h-20), radius=60, fill=(255,255,255,245), outline=accent+(255,), width=8)
    d.ellipse((70,120,230,280), fill=accent+(255,))
    d.text((260,155), name, fill=(25,25,35,255), font=_font(60))
    d.text((260,240), "Sponsor", fill=(110,120,140,255), font=_font(34))
    buf = io.BytesIO()
    base.save(buf, format="PNG", optimize=True)
    return buf.getvalue()

def ensure_catalog_assets(db: Session) -> Dict[str, List[str]]:
    """Create catalog assets (if missing) and return pools of asset IDs."""
    pools: Dict[str, List[str]] = {"hero_football":[], "hero_basket":[], "portrait":[], "sponsor":[], "bg": []}

    existing = db.query(Asset).filter(Asset.club_id == None, Asset.is_catalog == True).all()  # noqa: E711
    if existing:
        # Build pools from existing naming convention
        for a in existing:
            n = (a.filename or "").lower()
            if n.startswith("hero-football"):
                pools["hero_football"].append(a.id)
            elif n.startswith("hero-basket"):
                pools["hero_basket"].append(a.id)
            elif n.startswith("portrait"):
                pools["portrait"].append(a.id)
            elif n.startswith("sponsor"):
                pools["sponsor"].append(a.id)
            elif n.startswith("bg"):
                pools["bg"].append(a.id)
        # Ensure not empty
        if all(pools.values()):
            return pools

    accents = [(91,140,255),(255,77,109),(45,212,191),(226,183,20),(155,116,255)]
    # create a few per pool
    def add_asset(name: str, content: bytes) -> str:
        # Use the same id for DB + disk so any consumer (editor/exporter) can resolve paths reliably.
        asset_id, _path = save_local_file(content, f"{name}.png")
        a = Asset(id=asset_id, club_id=None, filename=f"{name}.png", mime="image/png", storage_path=asset_id, is_catalog=True)
        db.add(a)
        return asset_id

    for i in range(6):
        pools["hero_football"].append(add_asset(f"hero-football-{i+1}", _hero("football", accents[i % len(accents)])))
    for i in range(6):
        pools["hero_basket"].append(add_asset(f"hero-basket-{i+1}", _hero("basket", accents[(i+2) % len(accents)])))
    for i in range(10):
        pools["portrait"].append(add_asset(f"portrait-{i+1}", _portrait(f"Jugador {i+1}", accents[i % len(accents)])))
    sponsor_names = ["NOVA", "ATLAS", "SYNERGY", "VITA", "ZENITH", "ORBIT", "LUMEN", "PULSE"]
    for i, n in enumerate(sponsor_names):
        pools["sponsor"].append(add_asset(f"sponsor-{n.lower()}", _sponsor_logo(n, accents[i % len(accents)])))
    # backgrounds
    for i in range(6):
        pools["bg"].append(add_asset(f"bg-{i+1}", _hero("background", accents[(i+1) % len(accents)])))

    db.commit()
    return pools
