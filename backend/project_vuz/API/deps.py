from typing import Annotated

from fastapi import Depends, HTTPException
from jwt.exceptions import PyJWTError
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import decode_access_token
from models.rating import Student

_bearer = HTTPBearer(auto_error=True)


def get_current_student(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
    db: Annotated[Session, Depends(get_db)],
) -> Student:
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        sid = int(payload["sub"])
    except PyJWTError:
        raise HTTPException(
            status_code=401,
            detail="Неверный или просроченный токен",
        ) from None
    except (KeyError, TypeError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Неверный или просроченный токен",
        ) from None

    student = db.get(Student, sid)
    if student is None:
        raise HTTPException(status_code=401, detail="Студент не найден")
    return student
