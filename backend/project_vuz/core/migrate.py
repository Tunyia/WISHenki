"""Лёгкие миграции для учебного проекта (без Alembic)."""

from sqlalchemy import inspect, text

from core.activity_tags import with_imported_past_tag
from core.database import SessionLocal, engine


def ensure_imported_past_tag() -> None:
    """Добавить тег «прошедшие» импортированным мероприятиям, если его ещё нет."""
    import models.activity  # noqa: F401
    from models.activity import Activity

    with SessionLocal() as db:
        activities = (
            db.query(Activity)
            .filter(
                Activity.is_completed.is_(True),
                Activity.organizer == "ДПИШ",
                Activity.description.like("Импорт из Excel%"),
            )
            .all()
        )
        changed = False
        for act in activities:
            updated = with_imported_past_tag(list(act.categories or []))
            if updated != (act.categories or []):
                act.categories = updated
                changed = True
        if changed:
            db.commit()


def ensure_schema_updates() -> None:
    """Добавить новые колонки/таблицы в уже существующую БД после обновления кода."""
    insp = inspect(engine)
    if insp.has_table("activities") and "is_completed" not in {
        c["name"] for c in insp.get_columns("activities")
    }:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "ALTER TABLE activities "
                    "ADD COLUMN is_completed BOOLEAN NOT NULL DEFAULT FALSE"
                )
            )

    if insp.has_table("activity_attendances") and "bonus_points" not in {
        c["name"] for c in insp.get_columns("activity_attendances")
    }:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "ALTER TABLE activity_attendances "
                    "ADD COLUMN bonus_points INTEGER NOT NULL DEFAULT 0"
                )
            )

    ensure_imported_past_tag()
