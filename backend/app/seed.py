"""Run once after setting up the DB: python -m app.seed"""
from app.database import SessionLocal, Base, engine
from app.models import HCP

Base.metadata.create_all(bind=engine)

SAMPLE_HCPS = [
    {"name": "Dr. Anita Mehta", "specialty": "Cardiology", "institution": "City General Hospital",
     "email": "a.mehta@citygeneral.example", "phone": "555-0101"},
    {"name": "Dr. Rohan Kapoor", "specialty": "Endocrinology", "institution": "Sunrise Clinic",
     "email": "r.kapoor@sunriseclinic.example", "phone": "555-0102"},
    {"name": "Dr. Sarah Lin", "specialty": "Oncology", "institution": "Metro Cancer Institute",
     "email": "s.lin@metrocancer.example", "phone": "555-0103"},
]


def seed():
    db = SessionLocal()
    try:
        for data in SAMPLE_HCPS:
            exists = db.query(HCP).filter(HCP.email == data["email"]).first()
            if not exists:
                db.add(HCP(**data))
        db.commit()
        print(f"Seeded {len(SAMPLE_HCPS)} sample HCPs.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
