from __future__ import annotations

import os
from typing import Callable, Dict, Any

import fitz  # PyMuPDF

MM_TO_PT = 72.0 / 25.4


def _pt_bleed(mm: float) -> float:
    return float(mm or 0.0) * MM_TO_PT


def _safe_color(rgb: Any) -> tuple[float, float, float]:
    # Accept [0..1] or [0..255]
    if not isinstance(rgb, (list, tuple)) or len(rgb) != 3:
        return (0, 0, 0)
    vals = []
    for v in rgb:
        try:
            fv = float(v)
        except Exception:
            fv = 0.0
        if fv > 1.0:
            fv = fv / 255.0
        vals.append(max(0.0, min(1.0, fv)))
    return (vals[0], vals[1], vals[2])


def _collect_text(item: Dict[str, Any]) -> str:
    runs = item.get("richTextRuns") or []
    if isinstance(runs, list) and runs:
        parts = []
        for r in runs:
            t = r.get("text") if isinstance(r, dict) else ""
            if t:
                parts.append(str(t))
        return "".join(parts).strip()
    return str(item.get("text") or "").strip()


def export_document_to_pdf(
    document: Dict[str, Any],
    resolve_asset_path: Callable[[str], str | None],
    quality: str = "web",
    bleed_mm: float = 3.0,
    crop_marks: bool = False,
    watermark: bool = False,
) -> bytes:
    """Render the scene-graph document into a PDF.

    This is intentionally pragmatic: it outputs a correct PDF for previews/prints,
    but does not aim for perfect typography at this stage.
    """

    settings = document.get("settings") or {}
    pages = document.get("pages") or []

    # Default A4 points
    base_w = float(settings.get("pageWidth") or 595.0)
    base_h = float(settings.get("pageHeight") or 842.0)

    bleed_pt = _pt_bleed(float(bleed_mm or 0.0))
    page_w = base_w + 2 * bleed_pt
    page_h = base_h + 2 * bleed_pt

    pdf = fitz.open()

    for page in pages:
        p = pdf.new_page(width=page_w, height=page_h)

        # Draw page background if provided
        bg = page.get("background")
        if isinstance(bg, dict) and bg.get("fill"):
            fill = _safe_color(bg.get("fill"))
            p.draw_rect(fitz.Rect(0, 0, page_w, page_h), color=None, fill=fill)

        for layer in (page.get("layers") or []):
            if not isinstance(layer, dict):
                continue
            if not layer.get("visible", True) or layer.get("locked"):
                # even if locked, we still render; 'locked' only affects editing.
                pass

            for item in (layer.get("items") or []):
                if not isinstance(item, dict):
                    continue
                t = item.get("type")
                rect = item.get("rect") or {}
                x = float(rect.get("x") or 0.0) + bleed_pt
                y = float(rect.get("y") or 0.0) + bleed_pt
                w = float(rect.get("w") or 0.0)
                h = float(rect.get("h") or 0.0)
                r = fitz.Rect(x, y, x + w, y + h)

                if t in ("Shape", "Rect", "Rectangle"):
                    fill = _safe_color(item.get("fill") or [0, 0, 0]) if item.get("fill") else None
                    stroke = _safe_color(item.get("stroke") or [0, 0, 0]) if item.get("stroke") else None
                    sw = float(item.get("strokeWidth") or 0.0)
                    p.draw_rect(r, color=stroke, fill=fill, width=sw)

                elif t in ("Line",):
                    stroke = _safe_color(item.get("stroke") or [0, 0, 0])
                    sw = float(item.get("strokeWidth") or 1.0)
                    x2 = float(item.get("x2") or (x + w))
                    y2 = float(item.get("y2") or (y + h))
                    p.draw_line(fitz.Point(x, y), fitz.Point(x2, y2), color=stroke, width=sw)

                elif t in ("ImageFrame", "LockedLogoStamp"):
                    asset_id = item.get("assetRef") or item.get("assetId")
                    if not asset_id:
                        continue
                    path = resolve_asset_path(str(asset_id))
                    if path and os.path.exists(path):
                        try:
                            p.insert_image(r, filename=path, keep_proportion=False)
                        except Exception:
                            # Ignore broken images
                            pass

                elif t == "TextFrame":
                    txt = _collect_text(item)
                    if not txt:
                        continue
                    # Basic typography
                    color = _safe_color(item.get("color") or item.get("fill") or [0, 0, 0])
                    fontsize = float(item.get("fontSize") or 12)
                    align = item.get("align") or "left"
                    align_map = {"left": 0, "center": 1, "right": 2, "justify": 3}
                    a = align_map.get(str(align).lower(), 0)
                    try:
                        p.insert_textbox(
                            r,
                            txt,
                            fontsize=fontsize,
                            fontname="helv",
                            color=color,
                            align=a,
                        )
                    except Exception:
                        pass

        # Crop marks (very simple)
        if crop_marks and bleed_pt > 0:
            m = bleed_pt
            cm = 12
            # top-left
            p.draw_line((m, 0), (m, cm), color=(0, 0, 0), width=0.5)
            p.draw_line((0, m), (cm, m), color=(0, 0, 0), width=0.5)
            # top-right
            p.draw_line((page_w - m, 0), (page_w - m, cm), color=(0, 0, 0), width=0.5)
            p.draw_line((page_w - cm, m), (page_w, m), color=(0, 0, 0), width=0.5)
            # bottom-left
            p.draw_line((m, page_h - cm), (m, page_h), color=(0, 0, 0), width=0.5)
            p.draw_line((0, page_h - m), (cm, page_h - m), color=(0, 0, 0), width=0.5)
            # bottom-right
            p.draw_line((page_w - m, page_h - cm), (page_w - m, page_h), color=(0, 0, 0), width=0.5)
            p.draw_line((page_w - cm, page_h - m), (page_w, page_h - m), color=(0, 0, 0), width=0.5)

        if watermark:
            p.insert_text(
                (page_w * 0.15, page_h * 0.5),
                "PREVIEW",
                fontsize=80,
                rotate=25,
                color=(0.7, 0.7, 0.7),
                render_mode=0,
                overlay=True,
            )

    # Optimize slightly
    if quality == "web":
        pdf.saveIncr()

    out = pdf.tobytes()
    pdf.close()
    return out
