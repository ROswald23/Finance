import os
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import URL


DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "Mydata23")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "testdb")

url = URL.create(
    drivername="postgresql+psycopg2",
    username=DB_USER,
    password=DB_PASS,   # <-- pas besoin de percent-encoder
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
    # optionnel : forcer l'encodage côté client
    query={"client_encoding": "utf8"},
)

engine = create_engine(
    url,
    echo=False,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Auth simplifiée (ex: vous décoderez un JWT en vrai) ---
# class CurrentUser(BaseModel):
#     id: int
#     email: str
#
# def get_current_user() -> CurrentUser:
#     # TODO: décoder un vrai JWT. Ici: exemple.
#     return CurrentUser(id=42, email="user@example.com")
#
# # --- Schéma de sortie (pour un tableau) ---
# class WalletRow(BaseModel):
#     id: int
#     ticker: str
#     quantity: float
#     created_at: str









