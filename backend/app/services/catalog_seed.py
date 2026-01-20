from __future__ import annotations

import json
import uuid
from sqlalchemy.orm import Session

from app.models.models import Template
from app.services.catalog_assets import ensure_catalog_assets
from app.services.template_generator import generate_catalog_template_v2

# 20 templates base (mezcladas fútbol/basket). Se siembran automáticamente si no hay catálogo gen-v2.
CATALOG: list[tuple[str, str, str]] = [
    ("Atlas Minimal", "minimal_premium", "football"),
    ("Atlas Minimal Dark", "minimal_premium", "basket"),
    ("Diario de la Jornada", "newspaper_editorial", "football"),
    ("Cancha & Datos", "tech_data", "basket"),
    ("Fotográfico Pro", "photographic", "football"),
    ("Sponsors First", "sponsors_first", "football"),
    ("Academia Youth", "academy_youth", "football"),
    ("Derbi Nocturno", "photographic", "basket"),
    ("Estadio Blanco", "minimal_premium", "football"),
    ("Revista Premium", "minimal_premium", "basket"),
    ("La Gaceta", "newspaper_editorial", "basket"),
    ("DataLab", "tech_data", "football"),
    ("Flash Sports", "photographic", "football"),
    ("Partners Weekly", "sponsors_first", "basket"),
    ("La Cantera", "academy_youth", "basket"),
    ("Portada Collage", "collage_cover", "football"),
    ("Portada Split", "split_cover", "basket"),
    ("Portada Tipográfica", "type_cover", "football"),
    ("Magazine Clean", "clean_mag", "basket"),
    ("Magazine Bold", "bold_mag", "football"),
]

def ensure_catalog_seeded(db: Session):
    # If already has any gen-v2 catalog templates, skip
    existing = db.query(Template).filter(Template.origin == "catalog_v2").count()
    if existing >= 20:
        return

    # Remove old catalog templates to avoid duplicates
    old = db.query(Template).filter(Template.origin.in_(["catalog", "generated"])).all()
    for t in old:
        db.delete(t)
    db.commit()

    pools = ensure_catalog_assets(db)

    for i, (name, style, sport) in enumerate(CATALOG):
        template_id = str(uuid.uuid4())
        doc = generate_catalog_template_v2(style=style, sport=sport, seed=10000+i, asset_pools=pools)
        t = Template(
            id=template_id,
            name=name,
            origin="catalog_v2",
            sport=sport,
            pages=len(doc.get("pages") or []),
            document_json=json.dumps(doc),
        )
        db.add(t)

    db.commit()
