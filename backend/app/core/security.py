from __future__ import annotations

from datetime import datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.settings import settings

# Argon2 avoids bcrypt dependency/version issues and the 72-byte bcrypt password limit.
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
ALGO = "HS256"

def hash_password(pw: str) -> str:
    return pwd_context.hash(pw)

def verify_password(pw: str, hashed: str) -> bool:
    return pwd_context.verify(pw, hashed)

def create_access_token(subject: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=int(settings.APP_JWT_EXPIRE_MIN))
    return jwt.encode({"sub": subject, "exp": expire}, settings.APP_SECRET_KEY, algorithm=ALGO)

def decode_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.APP_SECRET_KEY, algorithms=[ALGO])
        sub = payload.get("sub")
        if not sub:
            raise ValueError("Missing sub")
        return str(sub)
    except JWTError as e:
        raise ValueError("Invalid token") from e
