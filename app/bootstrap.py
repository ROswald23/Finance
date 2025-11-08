# app/bootstrap.py
from app.db import engine
from app.models import Base

if __name__ == "__main__":
    print("Création des tables dans ma database : testdb...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables créées avec succès !")
