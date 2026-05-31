"""Лёгкие миграции для учебного проекта (без Alembic)."""

from sqlalchemy import inspect, text

from core.database import engine


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
