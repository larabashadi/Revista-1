from __future__ import annotations

import base64
import math
import random
from io import BytesIO
from typing import Any, Dict, List

from PIL import Image, ImageDraw, ImageFont

A4_W, A4_H = 595.2756, 841.8898

STYLE_PRESETS = {
    "minimal_premium": {"accent":"#5b8cff", "bg":"#ffffff", "ink":"#0f172a"},
    "newspaper_editorial": {"accent":"#e2b714", "bg":"#fffdf6", "ink":"#111827"},
    "photographic": {"accent":"#ff4d6d", "bg":"#0b1220", "ink":"#f8fafc"},
    "tech_data": {"accent":"#2dd4bf", "bg":"#0b1220", "ink":"#e2e8f0"},
    "sponsors_first": {"accent":"#a78bfa", "bg":"#ffffff", "ink":"#111827"},
    "academy_youth": {"accent":"#22c55e", "bg":"#ffffff", "ink":"#111827"},
    # extra cover styles
    "collage_cover": {"accent":"#f97316", "bg":"#ffffff", "ink":"#111827"},
    "split_cover": {"accent":"#06b6d4", "bg":"#ffffff", "ink":"#111827"},
    "type_cover": {"accent":"#ef4444", "bg":"#ffffff", "ink":"#111827"},
    "clean_mag": {"accent":"#0ea5e9", "bg":"#ffffff", "ink":"#111827"},
    "bold_mag": {"accent":"#f43f5e", "bg":"#0b1220", "ink":"#f8fafc"},
}

def _layer(name: str, items: list, locked: bool=False, visible: bool=True):
    return {"id": f"layer-{name}-{random.randint(1000,9999)}", "name": name, "visible": visible, "locked": locked, "items": items}

def _rect(x,y,w,h):
    return {"x":x,"y":y,"w":w,"h":h}

def _shape(x,y,w,h, fill="#eef2ff", extra=None):
    o = {"id": f"it-{random.randint(100000,999999)}", "type":"Shape", "rect":_rect(x,y,w,h), "fill":fill}
    if extra: o.update(extra)
    return o

def _text(x,y,w,h, txt, styleRef="H1", extra=None):
    o = {"id": f"it-{random.randint(100000,999999)}", "type":"TextFrame", "rect":_rect(x,y,w,h),
         "text": [{"text": txt, "marks": {}}], "styleRef": styleRef, "padding": 10}
    if extra: o.update(extra)
    return o

def _image(x,y,w,h, assetRef=None, extra=None):
    o = {"id": f"it-{random.randint(100000,999999)}", "type":"ImageFrame", "rect":_rect(x,y,w,h),
         "assetRef": assetRef, "fitMode":"cover", "crop":{"x":0,"y":0,"w":1,"h":1}}
    if extra: o.update(extra)
    return o

def _locked_logo():
    return {"id":"locked-logo", "type":"LockedLogoStamp", "rect":_rect(34, 36, 120, 120), "assetRef":"{{club.lockedLogo}}", "role":"locked_logo"}

def _styles(accent: str, ink: str):
    return {
        "textStyles": {
            "H1":{"fontFamily":"Inter","fontSize":40,"fontWeight":800,"color":ink},
            "H2":{"fontFamily":"Inter","fontSize":26,"fontWeight":750,"color":ink},
            "Body":{"fontFamily":"Inter","fontSize":13,"fontWeight":450,"color":ink},
            "Caption":{"fontFamily":"Inter","fontSize":11,"fontWeight":500,"color":"#64748b"},
        },
        "colorTokens":{"accent":accent,"ink":ink}
    }

def _page(sectionType: str, layers: list):
    return {"id": f"p-{random.randint(1000,9999)}", "sectionType": sectionType, "layers": layers}

def _cover(style: str, sport: str, pools: Dict[str,List[str]], preset: Dict[str,str]):
    accent = preset["accent"]
    bg = preset["bg"]
    ink = preset["ink"]
    hero_pool = pools["hero_football"] if sport=="football" else pools["hero_basket"]
    hero = random.choice(hero_pool)
    bg_asset = random.choice(pools["bg"])
    items_bg = [_image(0,0,A4_W,A4_H, assetRef=bg_asset, extra={"role":"page_background","locked":True})]
    items_fg = []
    items_fg.append(_locked_logo())
    title = f"{{{{club.name}}}} · Revista"
    if style in ("photographic","bold_mag"):
        items_fg.append(_shape(0,0,A4_W,A4_H, fill="#0b1220"))
        items_fg.append(_image(0,0,A4_W,A4_H, assetRef=hero, extra={"opacity":0.9}))
        items_fg.append(_shape(0,520,A4_W,321, fill="rgba(0,0,0,0.55)"))
        items_fg.append(_text(44,560,510,120, title, "H1", extra={"fill":"#ffffff"}))
        items_fg.append(_text(44,690,510,80, "Jornada · Crónica · Cantera · Sponsors", "H2", extra={"fill":"#e2e8f0"}))
    elif style=="newspaper_editorial":
        items_fg.append(_shape(0,0,A4_W,A4_H, fill="#fffdf6"))
        items_fg.append(_shape(40,160,A4_W-80,4, fill=accent))
        items_fg.append(_text(40,70,A4_W-80,90, title, "H1"))
        items_fg.append(_text(40,176,A4_W-80,60, "Especial Jornada · Análisis táctico · Entrevistas", "Body"))
        items_fg.append(_image(40,250,A4_W-80,360, assetRef=hero))
        items_fg.append(_shape(40,630,A4_W-80,160, fill="#ffffff"))
        items_fg.append(_text(52,640,A4_W-104,140, "EDITORIAL: La temporada se decide en los detalles. Trabajo, cohesión y ambición.", "Body"))
    elif style=="collage_cover":
        items_fg.append(_shape(0,0,A4_W,A4_H, fill=bg))
        # collage
        items_fg.append(_image(40,140,250,320, assetRef=hero))
        items_fg.append(_image(305,140,250,190, assetRef=random.choice(pools["portrait"])))
        items_fg.append(_image(305,340,250,120, assetRef=random.choice(pools["sponsor"])))
        items_fg.append(_shape(40,480,A4_W-80,8, fill=accent))
        items_fg.append(_text(40,60,A4_W-80,70, title, "H1"))
        items_fg.append(_text(40,510,A4_W-80,260, "Dentro: crónica con datos, fichas de jugadores, calendario, cantera y dossier de sponsors.", "Body"))
    elif style=="split_cover":
        items_fg.append(_shape(0,0,A4_W/2,A4_H, fill=accent))
        items_fg.append(_image(A4_W/2,0,A4_W/2,A4_H, assetRef=hero))
        items_fg.append(_text(38,90,A4_W/2-70,150, title, "H1", extra={"fill":"#ffffff"}))
        items_fg.append(_text(38,250,A4_W/2-70,110, "La revista oficial del club.\nEdición semanal/mensual.", "Body", extra={"fill":"#e2e8f0"}))
        items_fg.append(_shape(38,390,A4_W/2-70,6, fill="#ffffff"))
        items_fg.append(_text(38,420,A4_W/2-70,130, "Patrocinadores · Comunidad · Resultados · Historia", "Caption", extra={"fill":"#f8fafc"}))
    elif style=="type_cover":
        items_fg.append(_shape(0,0,A4_W,A4_H, fill=bg))
        items_fg.append(_text(40,80,A4_W-80,160, f"LA JORNADA · {{{{club.name}}}}", "H1"))
        items_fg.append(_shape(40,250,A4_W-80,8, fill=accent))
        items_fg.append(_text(40,280,A4_W-80,120, "Crónica, análisis y protagonistas", "H2"))
        items_fg.append(_image(40,420,A4_W-80,360, assetRef=hero))
    else:
        # minimal/clean
        items_fg.append(_shape(0,0,A4_W,A4_H, fill=bg))
        items_fg.append(_text(40,80,A4_W-80,120, title, "H1"))
        items_fg.append(_shape(40,210,220,10, fill=accent))
        items_fg.append(_image(40,260,A4_W-80,420, assetRef=hero))
        items_fg.append(_text(40,700,A4_W-80,120, "Resultados · Clasificación · Entrevistas · Cantera · Sponsors", "Body"))
    return _page("Cover", [
        _layer("BG", items_bg, locked=True),
        _layer("Content", items_fg),
    ])

def _two_col_article(title: str, body: str, preset: Dict[str,str], hero: str|None=None):
    items=[]
    items.append(_shape(0,0,A4_W,A4_H, fill=preset["bg"]))
    items.append(_text(40,50,A4_W-80,60,title,"H2"))
    items.append(_shape(40,118,A4_W-80,3, fill=preset["accent"]))
    if hero:
        items.append(_image(40,140,A4_W-80,220, assetRef=hero))
        y0=380
    else:
        y0=140
    # columns
    items.append(_text(40,y0, (A4_W-100)/2, A4_H-y0-80, body, "Body"))
    items.append(_text(60+(A4_W-100)/2, y0, (A4_W-100)/2, A4_H-y0-80, body, "Body"))
    items.append(_text(40,A4_H-55,A4_W-80,30,"{{club.name}} · Revista deportiva","Caption"))
    return _page("Report", [_layer("Content", items)])

def _players_page(preset: Dict[str,str], pools: Dict[str,List[str]]):
    items=[]
    items.append(_shape(0,0,A4_W,A4_H, fill=preset["bg"]))
    items.append(_text(40,40,A4_W-80,60,"Protagonistas","H2"))
    items.append(_shape(40,104,A4_W-80,3, fill=preset["accent"]))
    # 3 cards
    x0=40; y0=130; card_w=(A4_W-120)/3; card_h=260
    for i in range(3):
        x=x0+i*(card_w+20)
        items.append(_shape(x,y0,card_w,card_h, fill="#ffffff"))
        items.append(_image(x+10,y0+10,card_w-20,card_h-120, assetRef=random.choice(pools["portrait"])))
        items.append(_text(x+10,y0+card_h-100,card_w-20,30,f"Jugador {i+1}","H2", extra={"styleRef":"H2"}))
        items.append(_text(x+10,y0+card_h-70,card_w-20,60,"Rendimiento, liderazgo y constancia.\nDatos clave de la jornada.","Body"))
    return _page("Player", [_layer("Content", items)])

def _sponsors_page(preset: Dict[str,str], pools: Dict[str,List[str]]):
    items=[]
    items.append(_shape(0,0,A4_W,A4_H, fill=preset["bg"]))
    items.append(_text(40,40,A4_W-80,60,"Patrocinadores","H2"))
    items.append(_shape(40,104,A4_W-80,3, fill=preset["accent"]))
    y=140
    for i in range(4):
        items.append(_image(60,y, A4_W-120, 120, assetRef=random.choice(pools["sponsor"])))
        y += 150
    items.append(_text(40,A4_H-60,A4_W-80,40,"¿Quieres aparecer aquí? Contacta con el club.","Caption"))
    return _page("Sponsors", [_layer("Content", items)])

def generate_catalog_template_v2(style: str, sport: str, seed: int, asset_pools: Dict[str, List[str]]) -> Dict[str, Any]:
    rnd = random.Random(seed)
    random.seed(seed)

    preset = STYLE_PRESETS.get(style) or STYLE_PRESETS["minimal_premium"]
    doc = {
        "id": f"tpl-{seed}",
        "sport": sport,
        "format": "A4",
        "spreads": True,
        "settings": {"marginsMirror": True, "bleedMm": 3, "cropMarks": True, "colorMode": "RGB"},
        "brandKit": {"lockedLogoAssetId": "{{club.lockedLogo}}"},
        "styles": _styles(preset["accent"], preset["ink"]),
        "pages": [],
        "componentsLibrary": [],
        "variables": {"clubName": "{{club.name}}"},
        "generator": {"version": "gen-v2", "style": style, "seed": seed},
    }

    # Cover
    doc["pages"].append(_cover(style, sport, asset_pools, preset))

    # Build a real 40-page magazine with repeated section patterns, varied by style.
    bodies = [
        "El equipo compitió con personalidad. En fútbol, la presión tras pérdida marcó el ritmo; en basket, el rebote defensivo fue clave.",
        "El plan de partido funcionó: intensidad, orden y una idea clara. La lectura de espacios permitió generar ventajas.",
        "Los detalles deciden: balón parado, transiciones y concentración. El grupo respondió en los momentos de máxima exigencia.",
    ]
    hero_pool = asset_pools["hero_football"] if sport=="football" else asset_pools["hero_basket"]
    for i in range(1, 13):
        doc["pages"].append(_two_col_article(
            title=f"Crónica {i}: {{club.name}} en la jornada",
            body=bodies[i % len(bodies)] + "\n\n" + bodies[(i+1) % len(bodies)],
            preset=preset,
            hero=rnd.choice(hero_pool) if i % 2 == 0 else None,
        ))
        if len(doc["pages"]) >= 40:
            break
        if i % 3 == 0 and len(doc["pages"]) < 40:
            doc["pages"].append(_players_page(preset, asset_pools))
        if i % 4 == 0 and len(doc["pages"]) < 40:
            doc["pages"].append(_sponsors_page(preset, asset_pools))

    # pad to 40 pages
    while len(doc["pages"]) < 40:
        doc["pages"].append(_two_col_article(
            title="Agenda y calendario",
            body="Calendario de próximos partidos, entrenamientos y eventos del club.\n\nActualiza esta sección con tus fechas reales.",
            preset=preset,
            hero=rnd.choice(hero_pool),
        ))
    return doc


# ---------------------------------------------------------------------------
# Compatibility wrapper expected by API routes (generate_template)
# ---------------------------------------------------------------------------

def _png_data_uri(width: int, height: int, title: str, subtitle: str = "", seed: int = 0, accent: str = "#19c37d") -> str:
    """Offline-safe placeholder image as **PNG** data URI.

    We intentionally use PNG (not SVG) because the PDF export pipeline (PyMuPDF) can embed
    PNG streams reliably offline.
    """
    import hashlib

    # deterministic palette per seed/title
    base = int(hashlib.sha256(f"{seed}-{title}".encode("utf-8")).hexdigest()[:8], 16)
    def _h(n: int) -> int:
        return (base + n * 2654435761) & 0xFFFFFFFF

    bg1 = (_h(1) % 255, _h(2) % 255, _h(3) % 255)
    bg2 = (_h(4) % 255, _h(5) % 255, _h(6) % 255)
    acc = accent.lstrip("#")
    try:
        acc_rgb = (int(acc[0:2], 16), int(acc[2:4], 16), int(acc[4:6], 16))
    except Exception:
        acc_rgb = (25, 195, 125)

    img = Image.new("RGB", (width, height), bg1)
    draw = ImageDraw.Draw(img)

    # simple diagonal gradient
    for y in range(height):
        t = y / max(1, height - 1)
        r = int(bg1[0] * (1 - t) + bg2[0] * t)
        g = int(bg1[1] * (1 - t) + bg2[1] * t)
        b = int(bg1[2] * (1 - t) + bg2[2] * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    pad_x = int(width * 0.06)
    pad_y = int(height * 0.08)
    box_w = int(width * 0.88)
    box_h = int(height * 0.84)

    # overlay frame
    draw.rounded_rectangle(
        [pad_x, pad_y, pad_x + box_w, pad_y + box_h],
        radius=max(10, int(min(width, height) * 0.03)),
        outline=acc_rgb,
        width=max(2, int(min(width, height) * 0.006)),
    )

    # typography (fallback to default bitmap font)
    f1 = ImageFont.load_default()
    f2 = ImageFont.load_default()

    def _center_text(y: int, text: str, font: ImageFont.ImageFont, fill: tuple[int, int, int], stroke=None):
        if not text:
            return
        tw, th = draw.textsize(text, font=font)
        x = (width - tw) // 2
        draw.text((x, y), text, font=font, fill=fill)

    _center_text(int(height * 0.44), title[:40], f1, (255, 255, 255))
    _center_text(int(height * 0.54), subtitle[:60], f2, (240, 240, 240))
    _center_text(int(height * 0.90), "Placeholder (editable)", f2, (20, 20, 20))

    out = BytesIO()
    img.save(out, format="PNG", optimize=True)
    b64 = base64.b64encode(out.getvalue()).decode("ascii")
    return "data:image/png;base64," + b64

def _build_asset_pools(seed:int, sport:str, style:str, image_bias:float|None) -> Dict[str, List[str]]:
    style_accent = {
        "minimal_premium":"#19c37d",
        "newspaper_editorial":"#f59e0b",
        "photographic":"#a855f7",
        "tech_data":"#38bdf8",
        "sponsors_first":"#22c55e",
        "academy_youth":"#fb7185",
        "collage_cover":"#f43f5e",
        "split_cover":"#60a5fa",
        "type_cover":"#ffffff",
        "clean_mag":"#eab308",
        "bold_mag":"#ef4444",
    }.get(style, "#19c37d")

    sport_label = "Fútbol" if sport == "football" else ("Basket" if sport == "basket" else "Deporte")
    bias = float(image_bias or 0.5)

    hero_count = 6 if bias >= 0.55 else 4
    bg_count = 6
    portrait_count = 10
    sponsor_count = 10

    pools = {"bg": [], "hero_football": [], "hero_basket": [], "portrait": [], "sponsor": []}

    for i in range(bg_count):
        pools["bg"].append(_svg_data_uri(1200, 1600, f"Fondo {i+1}", f"{style} • {sport_label}", seed=seed+i, accent=style_accent))

    for i in range(hero_count):
        pools["hero_football"].append(_svg_data_uri(1600, 900, f"Hero Fútbol {i+1}", "Portada / Reportaje", seed=seed+100+i, accent=style_accent))
        pools["hero_basket"].append(_svg_data_uri(1600, 900, f"Hero Basket {i+1}", "Portada / Reportaje", seed=seed+200+i, accent=style_accent))

    for i in range(portrait_count):
        pools["portrait"].append(_svg_data_uri(900, 1200, f"Jugador {i+1}", "Retrato", seed=seed+300+i, accent=style_accent))

    for i in range(sponsor_count):
        pools["sponsor"].append(_svg_data_uri(1200, 600, f"SPONSOR {i+1}", "Logo placeholder", seed=seed+400+i, accent=style_accent))

    return pools

def _stable_signature(doc: Dict[str, Any], *, sport:str, style:str, density:float|None, weights:Dict[str,float]|None, image_bias:float|None, seed:int) -> Dict[str, Any]:
    section_counts = {}
    for p in (doc.get("pages") or []):
        st = p.get("sectionType","Custom")
        section_counts[st] = section_counts.get(st, 0) + 1

    return {
        "v": 2,
        "sport": sport,
        "style": style,
        "seed": int(seed),
        "density": float(density or 0.5),
        "image_bias": float(image_bias or 0.5),
        "sections": section_counts,
        "weights": weights or {},
    }

def _sig_key(sig: Dict[str, Any]) -> str:
    import json
    return json.dumps(sig, sort_keys=True, ensure_ascii=False)

def generate_template(
    seed: int,
    sport: str,
    style: str,
    weights: Dict[str, float] | None = None,
    density: float | None = None,
    image_bias: float | None = None,
    existing_sigs: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """
    Backwards-compatible generator used by /api/templates/generate and seeding.

    - Offline-safe SVG placeholders (works even without internet).
    - Adds `layoutSignature` + `generator` metadata expected by the API/UI.
    """
    sport = (sport or "football").lower()
    style = (style or "minimal_premium").strip() or "minimal_premium"

    if style in ("auto", "smart", "random"):
        styles = list(STYLE_PRESETS.keys())
        idx = (seed + int((density or 0.5) * 1000)) % len(styles)
        style = styles[idx]

    pools = _build_asset_pools(seed=seed, sport=sport, style=style, image_bias=image_bias)

    existing_keys = set(_sig_key(s) for s in (existing_sigs or []))

    chosen_doc = None
    chosen_sig = None
    chosen_seed = seed

    for attempt in range(0, 12):
        s = seed + attempt
        doc = generate_catalog_template_v2(style=style, sport=sport, seed=s, asset_pools=pools)
        sig = _stable_signature(doc, sport=sport, style=style, density=density, weights=weights, image_bias=image_bias, seed=s)
        if _sig_key(sig) not in existing_keys:
            chosen_doc, chosen_sig, chosen_seed = doc, sig, s
            break

    if chosen_doc is None:
        chosen_doc = generate_catalog_template_v2(style=style, sport=sport, seed=seed, asset_pools=pools)
        chosen_sig = _stable_signature(chosen_doc, sport=sport, style=style, density=density, weights=weights, image_bias=image_bias, seed=seed)
        chosen_seed = seed

    chosen_doc["layoutSignature"] = chosen_sig
    chosen_doc["generator"] = {
        "name": "native-template-generator",
        "version": "v2",
        "style": style,
        "sport": sport,
        "seed": chosen_seed,
        "density": float(density or 0.5),
        "image_bias": float(image_bias or 0.5),
        "notes": "Offline-safe SVG placeholders; editable content.",
    }
    chosen_doc.setdefault("name", f"{style.replace('_',' ').title()} • {sport.upper()}")
    return chosen_doc
