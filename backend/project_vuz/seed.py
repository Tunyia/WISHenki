from __future__ import annotations

import argparse
import time

from sqlalchemy import text
from sqlalchemy.orm import Session

from core.database import Base, SessionLocal, engine
from models.activity import Activity
from models.rating import Item, Student, Transaction


def ensure_student(db: Session, full_name: str, study_group: str) -> Student:
    st = (
        db.query(Student)
        .filter(Student.full_name == full_name, Student.study_group == study_group)
        .one_or_none()
    )
    if st is not None:
        return st

    st = Student(
        full_name=full_name,
        study_group=study_group,
        total_points=0,
        available_points=0,
    )
    db.add(st)
    db.commit()
    db.refresh(st)
    return st


def ensure_item(db: Session, name: str, type_: str) -> Item:
    it = db.query(Item).filter(Item.name == name).one_or_none()
    if it is not None:
        return it

    it = Item(name=name, type=type_)
    db.add(it)
    db.commit()
    db.refresh(it)
    return it


def apply_points(db: Session, student: Student, item: Item, points_change: int) -> Transaction:
    # Повторяем бизнес-логику из API: total_points растёт только при начислении,
    # available_points может и уменьшаться (но не уходит в минус).
    new_available = student.available_points + points_change
    if new_available < 0:
        raise ValueError("Not enough available_points for this operation")

    if points_change > 0:
        student.total_points += points_change
    student.available_points = new_available

    tx = Transaction(
        student_id=student.id,
        item_id=item.id,
        points_change=points_change,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


def ensure_schema() -> None:
    # Важно: после "очистки" БД таблицы могут ещё не существовать.
    # В API они создаются при старте приложения, но сидер должен уметь работать сам.
    Base.metadata.create_all(bind=engine)


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


def clear_all(db: Session) -> None:
    # Порядок важен из-за FK: transactions -> students/items
    db.query(Transaction).delete()
    db.query(Student).delete()
    db.query(Item).delete()
    db.query(Activity).delete()
    db.commit()


def seed(db: Session) -> None:
    # ---- Студенты (бывшие моки из фронта) ----
    mock_leaderboard_data = [
        {"fullName": "Алексей Смирнов", "group": "ШЦТ-111", "cherries": 114},
        {"fullName": "Екатерина Иванова", "group": "ШЦТ-112", "cherries": 130},
        {"fullName": "Иван Петров", "group": "ШЦТ-111", "cherries": 115},
        {"fullName": "Анна Сидорова", "group": "ШЦТ-112", "cherries": 90},
        {"fullName": "Дмитрий Волков", "group": "ШЦТ-111", "cherries": 85},
        {"fullName": "Волк Дмитриев", "group": "ШЦТ-111", "cherries": 85},
        {"fullName": "Студентович 1", "group": "ШЦТ-111", "cherries": 0},
        {"fullName": "Студентович 2", "group": "ШЦТ-111", "cherries": 0},
        {"fullName": "Студентович 3", "group": "ШЦТ-111", "cherries": 0},
        {"fullName": "Студентович 4", "group": "ШЦТ-111", "cherries": 0},
        {"fullName": "Студентович 5", "group": "ШЦТ-111", "cherries": 0},
        {"fullName": "Студентович 6", "group": "ШЦТ-111", "cherries": 0},
        {"fullName": "Студентович 7", "group": "ШЦТ-111", "cherries": 0},
        {"fullName": "Студентович 8", "group": "ШЦТ-111", "cherries": 0},
        {"fullName": "Студентович 9", "group": "ШЦТ-112", "cherries": 0},
        {"fullName": "Студентович 10", "group": "ШЦТ-112", "cherries": 0},
        {"fullName": "Студентович 10", "group": "ШЦТ-112", "cherries": 0},
        {"fullName": "Ченцов Артемий", "group": "ШЦТ-111", "cherries": 999},
        {"fullName": "Жмышенко Валерий", "group": "ГЛЭК-111", "cherries": 145},
    ]

    if db.query(Student).count() == 0:
        # Основание начисления
        points_item = ensure_item(db, "Начисление/списание ВИШенок", "points")

        for row in mock_leaderboard_data:
            st = ensure_student(db, row["fullName"], row["group"])
            if row["cherries"] > 0:
                apply_points(db, st, points_item, int(row["cherries"]))

    # ---- Мероприятия (бывшие моки из фронта) ----
    mock_activities_data = [
        {
            "title": "Хакатон «Code & Chill»",
            "organizer": "IT-Клуб",
            "description": "Разработка инновационных решений для университета за 24 часа. Приходи с командой или найди её на месте!",
            "categories": ["Программирование", "Хакатон", "IT"],
            "base_reward": 50,
            "event_date": "15 Октября, 10:00",
            "images": ["photos/kot.png", "photos/kot2.png", "photos/nekot.png"],
        },
        {
            "title": "Лекция по GeoAI",
            "organizer": "Деканат",
            "description": "Обсуждаем современные тренды в геоаналитике, цифровые двойники городов и спутниковые снимки.",
            "categories": ["Наука", "Геодезия"],
            "base_reward": 15,
            "event_date": "18 Октября, 14:30",
            "images": [],
        },
        {
            "title": "Волонтерство на Дне Открытых Дверей",
            "organizer": "Университет",
            "description": "Помощь в организации навигации для абитуриентов и их родителей. Нужны ответственные ребята.",
            "categories": ["Социальное", "Волонтерство", "ВУЗ"],
            "base_reward": 30,
            "event_date": "20 Октября, 09:00",
            "images": [],
        },
        {
            "title": "Хакатон «Code & Chill»",
            "organizer": "IT-Клуб",
            "description": "Разработка инновационных решений для университета за 24 часа.",
            "categories": ["IT", "Хакатон"],
            "base_reward": 50,
            "event_date": "15 Октября, 10:00",
            "images": [],
        },
        {
            "title": "Лекция по Python",
            "organizer": "Деканат",
            "description": "Обсуждаем python!",
            "categories": ["Наука", "IT"],
            "base_reward": 15,
            "event_date": "18 Октября, 14:30",
            "images": [],
        },
    ]

    if db.query(Activity).count() == 0:
        for a in mock_activities_data:
            db.add(
                Activity(
                    title=a["title"],
                    organizer=a["organizer"],
                    description=a["description"],
                    categories=a["categories"],
                    base_reward=a["base_reward"],
                    event_date=a["event_date"],
                    images=a["images"],
                )
            )
        db.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed demo data into database")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Clear tables and seed again",
    )
    parser.add_argument(
        "--wait",
        type=int,
        default=30,
        help="Seconds to wait for DB readiness (default: 30)",
    )
    args = parser.parse_args()

    wait_for_db(timeout_s=args.wait)
    ensure_schema()

    db = SessionLocal()
    try:
        if args.force:
            clear_all(db)
        seed(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()

