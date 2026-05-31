"""Посещения мероприятий и начисление вишенок (база + бонус)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from models.activity import Activity, ActivityAttendance
from models.rating import Student


def cherries_for_attendance(activity: Activity, attendance: ActivityAttendance) -> int:
    """Вишенки за одно посещение: фиксированная база мероприятия + индивидуальный бонус."""
    return int(activity.base_reward) + int(attendance.bonus_points or 0)


def ensure_attendance(
    db: Session,
    activity: Activity,
    student: Student,
    *,
    bonus_points: int = 0,
) -> ActivityAttendance:
    """Создать посещение, если его ещё нет (бонус по умолчанию 0)."""
    pair = (activity.id, student.id)
    for pending in db.new:
        if (
            isinstance(pending, ActivityAttendance)
            and (pending.activity_id, pending.student_id) == pair
        ):
            return pending

    row = (
        db.query(ActivityAttendance)
        .filter(
            ActivityAttendance.activity_id == activity.id,
            ActivityAttendance.student_id == student.id,
        )
        .first()
    )
    if row is None:
        row = ActivityAttendance(
            activity_id=activity.id,
            student_id=student.id,
            bonus_points=max(0, int(bonus_points)),
        )
        db.add(row)
    return row


def upsert_attendance(
    db: Session,
    activity: Activity,
    student: Student,
    *,
    bonus_points: int,
) -> ActivityAttendance:
    """Создать или обновить посещение (для импорта из Excel и ручных правок)."""
    bonus = max(0, int(bonus_points))
    row = (
        db.query(ActivityAttendance)
        .filter(
            ActivityAttendance.activity_id == activity.id,
            ActivityAttendance.student_id == student.id,
        )
        .first()
    )
    if row is None:
        row = ActivityAttendance(
            activity_id=activity.id,
            student_id=student.id,
            bonus_points=bonus,
        )
        db.add(row)
    else:
        row.bonus_points = bonus
    return row
