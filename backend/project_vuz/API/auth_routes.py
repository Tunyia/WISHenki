from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from API.deps import get_current_student
from core.database import get_db
from core.points import sync_student_points
from core.security import create_access_token, hash_password, verify_password
from models.rating import Student, User
from Shemas.auth import AuthTokenResponse, CurrentUserResponse, LoginRequest, RegisterRequest

router = APIRouter()


def _build_full_name(last_name: str, first_name: str, middle_name: str | None) -> str:
    parts = [last_name.strip(), first_name.strip()]
    if middle_name and middle_name.strip():
        parts.append(middle_name.strip())
    return " ".join(parts)


def _token_response(db: Session, student: Student, user: User) -> AuthTokenResponse:
    sync_student_points(db, student)
    db.commit()
    db.refresh(student)
    token = create_access_token(student_id=student.id, email=user.email)
    return AuthTokenResponse(
        access_token=token,
        token_type="bearer",
        student_id=student.id,
        email=user.email,
        full_name=student.full_name,
        study_group=student.study_group,
        available_points=student.available_points,
    )


@router.post("/register", response_model=AuthTokenResponse, status_code=201)
def register(
    payload: RegisterRequest,
    db: Annotated[Session, Depends(get_db)],
):
    email = payload.email.strip().lower()
    group_exists = (
        db.query(Student.id)
        .filter(Student.study_group == payload.study_group)
        .limit(1)
        .first()
    )
    if group_exists is None:
        raise HTTPException(
            status_code=400,
            detail="Указана недопустимая группа",
        )

    full_name = _build_full_name(payload.last_name, payload.first_name, payload.middle_name)

    student = Student(
        full_name=full_name,
        study_group=payload.study_group,
        total_points=0,
        available_points=0,
    )
    db.add(student)
    db.flush()

    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        student_id=student.id,
    )
    db.add(user)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Пользователь с такой почтой уже зарегистрирован",
        ) from None

    db.refresh(student)
    db.refresh(user)
    return _token_response(db, student, user)


@router.post("/login", response_model=AuthTokenResponse)
def login(
    payload: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
):
    email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email).one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверная почта или пароль")

    student = db.get(Student, user.student_id)
    if student is None:
        raise HTTPException(status_code=500, detail="Несогласованность данных аккаунта")

    return _token_response(db, student, user)


@router.get("/me", response_model=CurrentUserResponse)
def me(
    student: Annotated[Student, Depends(get_current_student)],
    db: Annotated[Session, Depends(get_db)],
):
    user = db.query(User).filter(User.student_id == student.id).one_or_none()
    if user is None:
        raise HTTPException(status_code=500, detail="Для студента нет учётной записи")
    sync_student_points(db, student)
    db.commit()
    db.refresh(student)
    return CurrentUserResponse(
        student_id=student.id,
        email=user.email,
        full_name=student.full_name,
        study_group=student.study_group,
        available_points=student.available_points,
    )
