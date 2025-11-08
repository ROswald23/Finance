# app/security.py
import os, time, jwt
from passlib.context import CryptContext
from typing import Tuple


pwd_ctx = CryptContext(schemes=["bcrypt_sha256", "bcrypt"], deprecated="auto")

JWT_SECRET = os.getenv("JWT_SECRET", "CHANGEMOI-super-secret")
JWT_ALGO = "HS256"
ACCESS_TTL = int(os.getenv("ACCESS_TTL_SECONDS", "900"))      # 15 min
REFRESH_TTL = int(os.getenv("REFRESH_TTL_SECONDS", "1209600")) # 14 jours



def hash_password(plain: str) -> str:
    return pwd_ctx.hash(plain.strip())

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain.strip(), hashed)

def needs_rehash(hashed: str) -> bool:
    return pwd_ctx.needs_update(hashed)

def _make_token(sub: str, ttl: int) -> str:
    now = int(time.time())
    payload = {"sub": sub, "iat": now, "exp": now + ttl}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)

def create_token_pair(user_id: int) -> Tuple[str, str]:
    return _make_token(str(user_id), ACCESS_TTL), _make_token(str(user_id), REFRESH_TTL)

def decode_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])

