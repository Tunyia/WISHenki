from __future__ import annotations

import argparse
import time

from sqlalchemy import text
from sqlalchemy.orm import Session

from core.attendance import ensure_attendance
from core.database import Base, SessionLocal, engine
from core.demo_activities import DEMO_UPCOMING_ACTIVITIES
from core.points import sync_all_students_points, sync_student_points
from models.activity import Activity, ActivityAttendance
from models.rating import Item, Student, Transaction, User


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


def grant_cherries_via_events(
    db: Session,
    student: Student,
    target: int,
    past_pool: list[Activity],
) -> None:
    """Набрать target вишенок: по одному посещению на мероприятие (без дублей)."""
    if target <= 0:
        return
    remaining = target
    for act in sorted(past_pool, key=lambda a: a.base_reward, reverse=True):
        if remaining >= act.base_reward:
            ensure_attendance(db, activity=act, student=student)
            remaining -= act.base_reward


def ensure_schema() -> None:
    Base.metadata.create_all(bind=engine)
    from core.migrate import ensure_schema_updates

    ensure_schema_updates()


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
    db.query(Transaction).delete()
    db.query(ActivityAttendance).delete()
    db.query(ActivityEnrollment).delete()
    db.query(User).delete()
    db.query(Student).delete()
    db.query(Item).delete()
    db.query(Activity).delete()
    db.commit()


def seed(db: Session) -> None:
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
        {"fullName": "Ченцов Артемий", "group": "ШЦТ-111", "cherries": 999},
        {"fullName": "Жмышенко Валерий", "group": "ГЛЭК-111", "cherries": 145},
    ]

    if db.query(Student).count() == 0:
        for row in mock_leaderboard_data:
            ensure_student(db, row["fullName"], row["group"])

    if db.query(Activity).count() == 0:
        for tpl in DEMO_UPCOMING_ACTIVITIES:
            db.add(Activity(**tpl))
        db.commit()

    past_acts = (
        db.query(Activity).filter(Activity.is_completed.is_(True)).order_by(Activity.id).all()
    )
    festival = next((a for a in past_acts if "Фестиваль" in a.title), None)
    regular_past = [a for a in past_acts if a is not festival]

    if db.query(ActivityAttendance).count() == 0 and regular_past:
        for row in mock_leaderboard_data:
            st = (
                db.query(Student)
                .filter(
                    Student.full_name == row["fullName"],
                    Student.study_group == row["group"],
                )
                .one()
            )
            target = int(row["cherries"])
            if target >= 999 and festival is not None:
                ensure_attendance(db, festival, st)
                target -= festival.base_reward
            grant_cherries_via_events(db, st, target, regular_past)
        db.commit()
        sync_all_students_points(db)


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed demo data into database")
    parser.add_argument("--force", action="store_true", help="Clear tables and seed again")
    parser.add_argument("--wait", type=int, default=30, help="Seconds to wait for DB")
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
