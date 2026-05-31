"""Поиск студента в рейтинге для привязки аккаунта при регистрации."""

from __future__ import annotations

from sqlalchemy.orm import Session

from models.rating import Student, User


def normalize_full_name(name: str) -> str:
    return " ".join(name.split())


def build_full_name(
    last_name: str,
    first_name: str,
    middle_name: str | None = None,
) -> str:
    parts = [last_name.strip(), first_name.strip()]
    if middle_name and middle_name.strip():
        parts.append(middle_name.strip())
    return normalize_full_name(" ".join(parts))


def _matches_without_patronymic(student_name: str, prefix: str) -> bool:
    normalized = normalize_full_name(student_name)
    normalized_prefix = normalize_full_name(prefix)
    return normalized == normalized_prefix or normalized.startswith(f"{normalized_prefix} ")


def find_student_for_claim(
    db: Session,
    *,
    last_name: str,
    first_name: str,
    middle_name: str | None,
    study_group: str,
) -> tuple[Student | None, str | None]:
    """Найти студента по ФИО и группе. Возвращает (student, сообщение об ошибке)."""
    group = study_group.strip()
    full_name = build_full_name(last_name, first_name, middle_name)

    student = (
        db.query(Student)
        .filter(Student.full_name == full_name, Student.study_group == group)
        .one_or_none()
    )
    if student is not None:
        return student, None

    if middle_name and middle_name.strip():
        return (
            None,
            "Студент не найден в рейтинге. Проверьте ФИО и группу или обратитесь к администратору.",
        )

    prefix = normalize_full_name(f"{last_name.strip()} {first_name.strip()}")
    in_group = db.query(Student).filter(Student.study_group == group).all()
    candidates = [s for s in in_group if _matches_without_patronymic(s.full_name, prefix)]

    if len(candidates) == 1:
        return candidates[0], None
    if len(candidates) > 1:
        return None, "Найдено несколько студентов с таким именем в группе. Укажите отчество."
    return (
        None,
        "Студент не найден в рейтинге. Проверьте ФИО и группу или обратитесь к администратору.",
    )


def student_has_account(db: Session, student: Student) -> bool:
    return (
        db.query(User.id).filter(User.student_id == student.id).limit(1).first()
        is not None
    )
