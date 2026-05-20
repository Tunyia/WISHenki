from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from core.config import ALGORITHM, SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES


def hash_password(password: str) -> str:
    data = password.encode("utf-8")
    if len(data) > 72:
        data = data[:72]
    return bcrypt.hashpw(data, bcrypt.gensalt()).decode("ascii")


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        data = plain_password.encode("utf-8")
        if len(data) > 72:
            data = data[:72]
        return bcrypt.checkpw(data, password_hash.encode("ascii"))
    except (ValueError, TypeError):
        return False


def create_access_token(*, student_id: int, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(student_id),
        "email": email,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
