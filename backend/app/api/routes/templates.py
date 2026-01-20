from __future__ import annotations
import json, time, uuid
from fastapi import APIRouter, Depends, HTTPException
from importlib import import_module
from fastapi.responses import Response
from PIL import Image, ImageDraw, ImageFont
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.api.deps import get_current_user
from app.models.models import Template, Asset
from app.schemas.schemas import TemplateOut, TemplateGenerateRequest
# NOTE:
# We intentionally avoid importing the template generator at module import time.
# If the generator module has any runtime error or is partially upgraded, a top-level
# import would crash the whole API (uvicorn can't import the app). We lazy-load it
# per request and return a clear error.


def _get_generate_fn():
    mod = import_module("app.services.template_generator")
    fn = getattr(mod, "generate_template", None)
    if fn is None:
        # backward compatibility / safety net
        fn = getattr(mod, "generate_template_document", None)
    if fn is None:
        raise RuntimeError("Template generator function not found")
    return fn

router = APIRouter(prefix="/api/templates", tags=["templates"])


def _render_template_thumbnail(document: dict, db: Session, size: int = 320, page_index: int = 0) -> bytes:
    """Render rápido (no perfecto) de la 1ª página como PNG.

    - Sirve para que el usuario elija plantilla por 'look & feel' sin abrirla.
    - No intenta renderizar fuentes exactas ni estilos avanzados: es un preview "suficiente".
    """
    A4_W = 595.2756
    A4_H = 841.8898
    scale = size / A4_W
    w = int(A4_W * scale)
    h = int(A4_H * scale)

    im = Image.new("RGBA", (w + 16, h + 16), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    # shadow
    draw.rounded_rectangle((8, 8, w + 8, h + 8), radius=14, fill=(0, 0, 0, 55))
    # page
    draw.rounded_rectangle((0, 0, w, h), radius=14, fill=(255, 255, 255, 255), outline=(220, 225, 235, 255), width=2)

    pages = document.get("pages") or []
    if not pages:
        import io
        out = Image.new("RGBA", (w, h), (255, 255, 255, 255))
        buf = io.BytesIO()
        out.save(buf, format="PNG", optimize=True)
        return buf.getvalue()
    page = pages[max(0, min(int(page_index), len(pages) - 1))]
    layers = page.get("layers") or []
    items = []
    for layer in layers:
        if layer.get("visible") is False:
            continue
        items.extend(layer.get("items") or [])

    # simple font
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    for it in items:
        r = (it.get("rect") or {})
        x = int(r.get("x", 0) * scale)
        y = int(r.get("y", 0) * scale)
        rw = int(r.get("w", 0) * scale)
        rh = int(r.get("h", 0) * scale)
        if rw <= 0 or rh <= 0:
            continue
        t = it.get("type")

        # Avoid showing PDF background as a giant image (it would be blank anyway).
        if it.get("role") == "pdf_background":
            continue

        if t == "Shape":
            fill = it.get("fill") or "#eef2ff"
            # crude hex parsing
            try:
                if isinstance(fill, str) and fill.startswith("#") and len(fill) in (7, 9):
                    rr = int(fill[1:3], 16)
                    gg = int(fill[3:5], 16)
                    bb = int(fill[5:7], 16)
                    col = (rr, gg, bb, 255)
                else:
                    col = (238, 242, 255, 255)
            except Exception:
                col = (238, 242, 255, 255)
            draw.rounded_rectangle((x, y, x + rw, y + rh), radius=10, fill=col, outline=(210, 215, 225, 255), width=1)

        elif t in ("ImageFrame", "LockedLogoStamp"):
            draw.rounded_rectangle((x, y, x + rw, y + rh), radius=10, fill=(240, 243, 248, 255), outline=(210, 215, 225, 255), width=1)
            # cross
            draw.line((x + 6, y + 6, x + rw - 6, y + rh - 6), fill=(200, 205, 215, 255), width=2)
            draw.line((x + rw - 6, y + 6, x + 6, y + rh - 6), fill=(200, 205, 215, 255), width=2)

        elif t == "TextFrame":
            draw.rounded_rectangle((x, y, x + rw, y + rh), radius=10, fill=(255, 255, 255, 0), outline=(210, 215, 225, 255), width=1)
            txt = "".join([(run.get("text") or "") for run in (it.get("richTextRuns") or [])]).strip()
            if txt:
                sample = (txt[:60] + "…") if len(txt) > 60 else txt
                draw.text((x + 8, y + 8), sample, fill=(30, 35, 45, 255), font=font)
            else:
                # placeholder lines
                for k in range(3):
                    yy = y + 10 + k * 12
                    draw.line((x + 8, yy, x + min(rw - 8, 120), yy), fill=(200, 205, 215, 255), width=2)

    # crop padding and return png
    im = im.crop((0, 0, w + 8, h + 8))
    import io
    buf = io.BytesIO()
    im.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


@router.get("/{template_id}/thumbnail")
def get_template_thumbnail(template_id: str, size: int = 320, page: int = 0, db: Session = Depends(get_db)):
    """Thumbnail público (sin auth) para mostrar previews en el catálogo."""
    t = db.get(Template, template_id)
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    try:
        doc = json.loads(t.document_json)
    except Exception:
        doc = {}
    png = _render_template_thumbnail(doc, db, size=max(200, min(int(size), 720)), page_index=page)
    return Response(content=png, media_type="image/png")

@router.get("", response_model=list[TemplateOut])
def list_templates(db: Session = Depends(get_db)):
    items = db.query(Template).order_by(Template.created_at.desc()).all()
    return [TemplateOut(id=t.id, name=t.name, origin=t.origin, sport=t.sport, pages=t.pages) for t in items]

@router.get("/{template_id}")
def get_template(template_id: str, db: Session = Depends(get_db)):
    t = db.get(Template, template_id)
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"id":t.id,"name":t.name,"origin":t.origin,"sport":t.sport,"pages":t.pages,"document":json.loads(t.document_json),"layoutSignature":json.loads(t.layout_signature or "{}")}

@router.post("/generate")
def generate_templates(payload: TemplateGenerateRequest, db: Session = Depends(get_db)):
    existing = db.query(Template).filter(Template.origin.in_(["catalog","generated"])).all()
    existing_sigs = [json.loads(t.layout_signature or "{}") for t in existing]
    base_seed = int(time.time())
    options=[]
    gen = _get_generate_fn()
    for i in range(3):
        doc = gen(seed=base_seed+i*97, sport=payload.sport, style=payload.style, weights=payload.weights, density=payload.density, image_bias=payload.image_bias, existing_sigs=existing_sigs)
        options.append({"name":f"Generada {payload.style} #{i+1}","document":doc,"layoutSignature":doc.get("layoutSignature",{}),"generator":doc.get("generator",{})})
    return {"options": options}

@router.post("/save-generated")
def save_generated(body: dict, db: Session = Depends(get_db), user=Depends(get_current_user)):
    name = (body.get("name") or "Plantilla generada").strip()
    doc = body.get("document")
    if not isinstance(doc, dict) or not doc.get("pages"):
        raise HTTPException(status_code=400, detail="Invalid document")
    sport = body.get("sport") or doc.get("generator",{}).get("params",{}).get("sport","football")
    template_id = "gen_" + uuid.uuid4().hex
    t = Template(id=template_id, name=name, origin="generated", sport=sport, pages=len(doc.get("pages",[])),
                 layout_signature=json.dumps(body.get("layoutSignature") or doc.get("layoutSignature") or {}, ensure_ascii=False),
                 document_json=json.dumps(doc, ensure_ascii=False))
    db.add(t); db.commit()
    return {"id": t.id, "name": t.name, "origin": t.origin, "sport": t.sport, "pages": t.pages}
