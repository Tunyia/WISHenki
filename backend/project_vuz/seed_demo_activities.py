#!/usr/bin/env python3
"""Добавить демо-мероприятия для записи на защите (данные в БД не удаляются).

Создаёт только предстоящие мероприятия с тегом «ДЕМО». Уже существующие
мероприятия с таким же названием пропускаются.

Запуск (Docker, из корня репозитория):
  docker compose exec api python seed_demo_activities.py
  docker compose exec api python seed_demo_activities.py --dry-run

Prod:
  docker compose -f docker-compose.prod.yml --env-file .env exec api python seed_demo_activities.py
"""

from __future__ import annotations

import argparse
import time

from sqlalchemy import text
from sqlalchemy.orm import Session

from core.database import Base, SessionLocal, engine
from core.demo_activities import DEMO_UPCOMING_ACTIVITIES
from core.migrate import ensure_schema_updates
from models.activity import Activity


def wait_for_db(timeout_s: int = 30) -> None:
    deadline = time.time() + timeout_s
    last_err: Exception | None = None
    while time.time() < deadline:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except Exception as e:
            last_err = e
            time.sleep(1)
    raise RuntimeError(f"DB is not ready after {timeout_s}s") from last_err


def ensure_schema() -> None:
    import models.activity  # noqa: F401
    import models.rating  # noqa: F401

    Base.metadata.create_all(bind=engine)
    ensure_schema_updates()


def add_demo_activities(db: Session, *, dry_run: bool) -> dict:
    added: list[str] = []
    skipped: list[str] = []

    for tpl in DEMO_UPCOMING_ACTIVITIES:
        title = tpl["title"]
        exists = (
            db.query(Activity.id).filter(Activity.title == title).limit(1).first()
        )
        if exists is not None:
            skipped.append(title)
            continue
        if not dry_run:
            db.add(Activity(**tpl))
        added.append(title)

    if not dry_run and added:
        db.commit()

    return {"added": added, "skipped": skipped, "dry_run": dry_run}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Добавить демо-мероприятия (без удаления существующих данных)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Только показать, что будет добавлено",
    )
    parser.add_argument("--wait", type=int, default=30, help="Секунд ждать БД")
    args = parser.parse_args()

    wait_for_db(timeout_s=args.wait)
    ensure_schema()

    db = SessionLocal()
    try:
        result = add_demo_activities(db, dry_run=args.dry_run)
    finally:
        db.close()

    mode = " (dry-run)" if result["dry_run"] else ""
    print(f"Демо-мероприятия{mode}:")
    if result["added"]:
        print(f"  Добавлено ({len(result['added'])}):")
        for title in result["added"]:
            print(f"    + {title}")
    else:
        print("  Новых мероприятий нет.")

    if result["skipped"]:
        print(f"  Пропущено — уже в БД ({len(result['skipped'])}):")
        for title in result["skipped"]:
            print(f"    ~ {title}")


if __name__ == "__main__":
    main()
