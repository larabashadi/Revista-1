from __future__ import annotations
import json, uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.settings import settings
from app.models.models import Template
from app.services.template_generator import generate_template

CATALOG = [
    ("Atlas Minimal", "minimal_premium", "football", 10101),
    ("Prensa Clásica", "newspaper_editorial", "football", 10202),
    ("Foto Hero", "photographic", "football", 10303),
    ("Data Tech", "tech_data", "football", 10404),
    ("Sponsors Pro", "sponsors_first", "football", 10505),
    ("Cantera Viva", "academy_youth", "football", 10606),
    ("Derby Minimal", "minimal_premium", "football", 10707),
    ("Crónica Deluxe", "photographic", "football", 10808),
    ("Club Journal", "newspaper_editorial", "football", 10909),
    ("Stats Focus", "tech_data", "football", 11010),
    ("Basket Minimal", "minimal_premium", "basket", 20101),
    ("Basket Press", "newspaper_editorial", "basket", 20202),
    ("Basket Photo", "photographic", "basket", 20303),
    ("Basket Data", "tech_data", "basket", 20404),
    ("Basket Sponsors", "sponsors_first", "basket", 20505),
    ("Basket Cantera", "academy_youth", "basket", 20606),
    ("Impact Neon", "tech_data", "football", 11111),
    ("Vintage Paper", "newspaper_editorial", "football", 11212),
    ("Gallery Pro", "photographic", "basket", 20707),
    ("Clean Studio", "minimal_premium", "basket", 20808),
]

def main():
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    db = SessionLocal()
    try:
        for name, style, sport, seed in CATALOG:
            template_id = "cat_" + uuid.uuid4().hex[:10]
            doc = generate_template(seed=seed, sport=sport, style=style, weights={
                "matches":0.25,"players":0.25,"sponsors":0.2,"academy":0.15,"interviews":0.1,"custom":0.05
            }, density="medium", image_bias="medium", existing_sigs=[])
            t = Template(id=template_id, name=name, origin="catalog", sport=sport, pages=len(doc.get("pages",[])),
                         layout_signature=json.dumps(doc.get("layoutSignature", {}), ensure_ascii=False),
                         document_json=json.dumps(doc, ensure_ascii=False))
            db.add(t)
        db.commit()
        print("Seeded catalog templates:", len(CATALOG))
    finally:
        db.close()

if __name__ == "__main__":
    main()
