from __future__ import annotations
from typing import Dict, Any, List, Tuple
import uuid
import fitz
from sqlalchemy.orm import Session

from app.models.models import Asset
from app.services.storage import save_local_file

A4_W, A4_H = 595.2756, 841.8898

def _render_page_image(doc: fitz.Document, page_index: int, scale: float=2.0) -> bytes:
    page = doc.load_page(page_index)
    mat = fitz.Matrix(scale, scale)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    return pix.tobytes("png")

def _map_rect(r: fitz.Rect, page_w: float, page_h: float):
    sx = A4_W / page_w
    sy = A4_H / page_h
    return {"x": float(r.x0 * sx), "y": float(r.y0 * sy), "w": float((r.x1 - r.x0) * sx), "h": float((r.y1 - r.y0) * sy)}

def _mk_asset(db: Session, club_id: str, png_bytes: bytes, base_name: str) -> str:
    # Use the same id on disk and in the DB so every pipeline (editor, exporter, importer) can resolve assets reliably.
    asset_id, _path = save_local_file(png_bytes, f"{base_name}.png")
    db.add(Asset(id=asset_id, club_id=club_id, filename=f"{base_name}.png", mime="image/png", storage_path=asset_id, is_catalog=False))
    return asset_id

def import_pdf_to_document(db: Session, club_id: str, pdf_bytes: bytes, mode: str="safe", preset: str="smart") -> Tuple[Dict[str, Any], List[str]]:
    """Import PDF into native-ish document.

    - Always creates a background raster of each page (safe mode).
    - Extracts text blocks into editable TextFrames.
    - Extracts embedded images into ImageFrames when possible.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages=[]
    created_asset_ids: List[str] = []

    for i in range(doc.page_count):
        page = doc.load_page(i)
        page_w, page_h = float(page.rect.width), float(page.rect.height)

        # Background raster
        bg_png = _render_page_image(doc, i, scale=2.0)
        bg_asset_id = _mk_asset(db, club_id, bg_png, f"import_bg_p{i+1}")
        created_asset_ids.append(bg_asset_id)

        bg_item = {
            "id": f"bg-{i}",
            "type":"ImageFrame",
            "rect":{"x":0,"y":0,"w":A4_W,"h":A4_H},
            "assetRef": bg_asset_id,
            "fitMode":"cover",
            "crop":{"x":0,"y":0,"w":1,"h":1},
            "locked": True,
            "role":"pdf_background"
        }

        overlay_items: List[Dict[str,Any]] = []

        # Text extraction
        try:
            td = page.get_text("dict")
            for b in td.get("blocks", []):
                if b.get("type") != 0:
                    continue
                # block bbox
                x0,y0,x1,y1 = b.get("bbox", [0,0,0,0])
                rect = _map_rect(fitz.Rect(x0,y0,x1,y1), page_w, page_h)
                # build text
                lines=[]
                for ln in b.get("lines", []):
                    segs=[]
                    for sp in ln.get("spans", []):
                        segs.append(sp.get("text",""))
                    if segs:
                        lines.append("".join(segs))
                text = "\n".join([l.strip() for l in lines if l.strip()])
                if not text:
                    continue
                overlay_items.append({
                    "id": f"tx-{i}-{len(overlay_items)}",
                    "type":"TextFrame",
                    "rect": rect,
                    "text":[{"text": text, "marks": {}}],
                    "styleRef":"Body",
                    "padding": 6,
                })
        except Exception:
            pass

        # Image extraction (embedded)
        try:
            imgs = page.get_images(full=True)
            seen=set()
            for img in imgs:
                xref = img[0]
                if xref in seen:
                    continue
                seen.add(xref)
                rects = page.get_image_rects(xref)
                if not rects:
                    continue
                raw = doc.extract_image(xref)
                im_bytes = raw.get("image")
                if not im_bytes:
                    continue
                # Convert to PNG via pixmap for consistency
                try:
                    pix = fitz.Pixmap(doc, xref)
                    if pix.n >= 5:  # CMYK etc
                        pix = fitz.Pixmap(fitz.csRGB, pix)
                    im_bytes = pix.tobytes("png")
                except Exception:
                    pass
                asset_id = _mk_asset(db, club_id, im_bytes, f"import_img_{i+1}_{xref}")
                created_asset_ids.append(asset_id)
                for r in rects[:4]:
                    rr = _map_rect(r, page_w, page_h)
                    if rr["w"] < 10 or rr["h"] < 10:
                        continue
                    overlay_items.append({
                        "id": f"im-{i}-{xref}-{len(overlay_items)}",
                        "type":"ImageFrame",
                        "rect": rr,
                        "assetRef": asset_id,
                        "fitMode":"cover",
                        "crop":{"x":0,"y":0,"w":1,"h":1},
                        "role":"imported_image",
                    })
        except Exception:
            pass

        # Layers: background locked, overlay editable
        layers=[
            {"id":"bg","name":"PDF Fondo","visible":True,"locked":True,"items":[bg_item]},
            {"id":"overlay","name":"Detectado","visible":True,"locked":False,"items":overlay_items},
        ]
        pages.append({"id": f"p-{i}", "sectionType":"Imported", "layers": layers})

    out_doc = {
        "id": str(uuid.uuid4()),
        "format":"A4",
        "spreads": True,
        "settings":{"marginsMirror": True, "bleedMm":3, "cropMarks": True, "colorMode":"RGB"},
        "styles": {
            "textStyles":{
                "H1":{"fontFamily":"Inter","fontSize":40,"fontWeight":800,"color":"#0f172a"},
                "H2":{"fontFamily":"Inter","fontSize":26,"fontWeight":750,"color":"#0f172a"},
                "Body":{"fontFamily":"Inter","fontSize":13,"fontWeight":450,"color":"#111827"},
                "Caption":{"fontFamily":"Inter","fontSize":11,"fontWeight":500,"color":"#64748b"},
            },
            "colorTokens":{"accent":"#5b8cff","ink":"#0f172a"}
        },
        "pages": pages,
        "componentsLibrary": [],
        "variables": {},
        "generator": {"version":"import-v2", "mode": mode, "preset": preset},
    }
    db.commit()
    return out_doc, created_asset_ids
