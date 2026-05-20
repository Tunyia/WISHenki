"""Баланс вишенок: начисления за посещённые мероприятия минус списания в магазине."""

from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.activity import Activity, ActivityAttendance
from models.rating import Student, Transaction


def earned_from_attended_events(db: Session, student_id: int) -> int:
    total = (
        db.query(func.coalesce(func.sum(Activity.base_reward), 0))
        .select_from(ActivityAttendance)
        .join(Activity, Activity.id == ActivityAttendance.activity_id)
        .filter(ActivityAttendance.student_id == student_id)
        .scalar()
    )
    return int(total or 0)


def spent_in_shop(db: Session, student_id: int) -> int:
    """Сумма потраченных вишенок (отрицательные транзакции)."""
    total = (
        db.query(func.coalesce(func.sum(-Transaction.points_change), 0))
        .filter(
            Transaction.student_id == student_id,
            Transaction.points_change < 0,
        )
        .scalar()
    )
    return int(total or 0)


def compute_available_points(db: Session, student_id: int) -> int:
    return earned_from_attended_events(db, student_id) - spent_in_shop(db, student_id)


def sync_student_points(db: Session, student: Student) -> None:
    """Пересчитать и сохранить баланс студента в students.*."""
    earned = earned_from_attended_events(db, student.id)
    spent = spent_in_shop(db, student.id)
    student.total_points = earned
    student.available_points = max(0, earned - spent)


def sync_all_students_points(db: Session) -> None:
    for student in db.query(Student).all():
        sync_student_points(db, student)
    db.commit()
