from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from API.deps import get_current_student
from core.database import get_db
from core.points import sync_student_points
from core.security import create_access_token, hash_password, verify_password
from core.student_claim import find_student_for_claim, student_has_account
from models.rating import Student, User
from Shemas.auth import (
    AuthTokenResponse,
    CheckStudentRequest,
    CheckStudentResponse,
    CurrentUserResponse,
    LoginRequest,
    RegisterRequest,
)

router = APIRouter()


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


def _resolve_claimable_student(
    db: Session,
    *,
    last_name: str,
    first_name: str,
    middle_name: str | None,
    study_group: str,
) -> Student:
    student, error = find_student_for_claim(
        db,
        last_name=last_name,
        first_name=first_name,
        middle_name=middle_name,
        study_group=study_group,
    )
    if student is None:
        raise HTTPException(status_code=404, detail=error or "Студент не найден")

    if student_has_account(db, student):
        raise HTTPException(
            status_code=409,
            detail="Аккаунт для этого студента уже создан. Войдите в систему.",
        )
    return student


@router.post("/check-student", response_model=CheckStudentResponse)
def check_student(
    payload: CheckStudentRequest,
    db: Annotated[Session, Depends(get_db)],
):
    student, error = find_student_for_claim(
        db,
        last_name=payload.last_name,
        first_name=payload.first_name,
        middle_name=payload.middle_name,
        study_group=payload.study_group,
    )
    if student is None:
        return CheckStudentResponse(found=False, message=error or "Студент не найден")

    if student_has_account(db, student):
        return CheckStudentResponse(
            found=True,
            already_registered=True,
            full_name=student.full_name,
            study_group=student.study_group,
            message="Аккаунт уже создан. Войдите в систему.",
        )

    return CheckStudentResponse(
        found=True,
        full_name=student.full_name,
        study_group=student.study_group,
        message=f"Найден в списке: {student.full_name}, группа {student.study_group}",
    )


@router.post("/register", response_model=AuthTokenResponse, status_code=201)
def register(
    payload: RegisterRequest,
    db: Annotated[Session, Depends(get_db)],
):
    email = payload.email.strip().lower()
    student = _resolve_claimable_student(
        db,
        last_name=payload.last_name,
        first_name=payload.first_name,
        middle_name=payload.middle_name,
        study_group=payload.study_group,
    )

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
