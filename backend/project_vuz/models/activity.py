from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(String, index=True)
    organizer: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str] = mapped_column(Text)

    # Храним как массив строк (PostgreSQL JSONB)
    categories: Mapped[list[str]] = mapped_column(JSONB, default=list)

    base_reward: Mapped[int] = mapped_column(Integer, default=0)

    # В учебном проекте пока оставим как человекочитаемую строку, как в текущем фронте
    event_date: Mapped[str] = mapped_column(String)

    # Имена файлов или пути вида "kot.png", "/photos/kot.png", либо полный URL
    images: Mapped[list[str]] = mapped_column(JSONB, default=list)

    # Прошедшее мероприятие (посещения и начисление вишенок)
    is_completed: Mapped[bool] = mapped_column(default=False, index=True)


class ActivityEnrollment(Base):
    """Запись студента на мероприятие."""

    __tablename__ = "activity_enrollments"
    __table_args__ = (
        UniqueConstraint(
            "activity_id",
            "student_id",
            name="uq_enrollment_activity_student",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    activity_id: Mapped[int] = mapped_column(
        ForeignKey("activities.id", ondelete="CASCADE"),
        index=True,
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"),
        index=True,
    )


class ActivityAttendance(Base):
    """Факт посещения прошедшего мероприятия — даёт base_reward вишенок."""

    __tablename__ = "activity_attendances"
    __table_args__ = (
        UniqueConstraint(
            "activity_id",
            "student_id",
            name="uq_attendance_activity_student",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    activity_id: Mapped[int] = mapped_column(
        ForeignKey("activities.id", ondelete="CASCADE"),
        index=True,
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"),
        index=True,
    )

