from __future__ import annotations

import argparse
import time

from sqlalchemy import text
from sqlalchemy.orm import Session

from core.database import Base, SessionLocal, engine
from core.points import sync_all_students_points, sync_student_points
from models.activity import Activity, ActivityAttendance, ActivityEnrollment
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


def ensure_attendance(db: Session, activity: Activity, student: Student) -> None:
    pair = (activity.id, student.id)
    for pending in db.new:
        if (
            isinstance(pending, ActivityAttendance)
            and (pending.activity_id, pending.student_id) == pair
        ):
            return
    exists = (
        db.query(ActivityAttendance)
        .filter(
            ActivityAttendance.activity_id == activity.id,
            ActivityAttendance.student_id == student.id,
        )
        .first()
    )
    if exists is None:
        db.add(ActivityAttendance(activity_id=activity.id, student_id=student.id))


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
        past_templates = [
            {
                "title": "Лекция по GeoAI",
                "organizer": "Деканат",
                "description": "Обсуждаем современные тренды в геоаналитике, цифровые двойники городов и спутниковые снимки.",
                "categories": ["Наука", "Геодезия"],
                "base_reward": 15,
                "event_date": "12 Сентября, 14:30",
                "images": [],
                "is_completed": True,
            },
            {
                "title": "Лекция по Python",
                "organizer": "Деканат",
                "description": "Обсуждаем python!",
                "categories": ["Наука", "IT"],
                "base_reward": 15,
                "event_date": "5 Сентября, 14:30",
                "images": [],
                "is_completed": True,
            },
            {
                "title": "Хакатон «Code & Chill» (осень)",
                "organizer": "IT-Клуб",
                "description": "Прошедший хакатон: разработка решений для университета за 24 часа.",
                "categories": ["IT", "Хакатон"],
                "base_reward": 50,
                "event_date": "1 Сентября, 10:00",
                "images": ["kot.png", "kot2.png", "nekot.png"],
                "is_completed": True,
            },
            {
                "title": "Волонтёрство на Дне открытых дверей",
                "organizer": "Университет",
                "description": "Помощь абитуриентам и родителям навигации по кампусу.",
                "categories": ["Социальное", "Волонтерство"],
                "base_reward": 30,
                "event_date": "25 Августа, 09:00",
                "images": [],
                "is_completed": True,
            },
            {
                "title": "Фестиваль «ВИШенка»",
                "organizer": "Студсовет",
                "description": "Главное осеннее мероприятие института.",
                "categories": ["Социальное", "ВУЗ"],
                "base_reward": 999,
                "event_date": "20 Августа, 18:00",
                "images": [],
                "is_completed": True,
            },
        ]
        upcoming_templates = [
            {
                "title": "Хакатон «Code & Chill»",
                "organizer": "IT-Клуб",
                "description": "Разработка инновационных решений для университета за 24 часа. Приходи с командой или найди её на месте!",
                "categories": ["Программирование", "Хакатон", "IT"],
                "base_reward": 50,
                "event_date": "15 Октября, 10:00",
                "images": ["kot.png", "kot2.png", "nekot.png"],
                "is_completed": False,
            },
            {
                "title": "Волонтерство на Дне Открытых Дверей",
                "organizer": "Университет",
                "description": "Помощь в организации навигации для абитуриентов и их родителей.",
                "categories": ["Социальное", "Волонтерство", "ВУЗ"],
                "base_reward": 30,
                "event_date": "20 Октября, 09:00",
                "images": [],
                "is_completed": False,
            },
            {
                "title": "Лекция: карьера в IT",
                "organizer": "Деканат",
                "description": "Приглашённые спикеры из индустрии.",
                "categories": ["IT", "Наука"],
                "base_reward": 20,
                "event_date": "22 Октября, 16:00",
                "images": [],
                "is_completed": False,
            },
        ]
        for tpl in past_templates + upcoming_templates:
            db.add(Activity(**tpl))
        db.commit()

    past_acts = (
        db.query(Activity).filter(Activity.is_completed.is_(True)).order_by(Activity.id).all()
    )
    festival = next((a for a in past_acts if "Фестиваль" in a.title), None)
    regular_past = [a for a in past_acts if a is not festival]

    if db.query(ActivityAttendance).count() == 0:
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

    if db.query(ActivityEnrollment).count() == 0:
        upcoming = (
            db.query(Activity)
            .filter(Activity.is_completed.is_(False))
            .order_by(Activity.id.asc())
            .first()
        )
        if upcoming is not None:
            for st in db.query(Student).order_by(Student.id.asc()).limit(6).all():
                db.add(ActivityEnrollment(activity_id=upcoming.id, student_id=st.id))
            db.commit()


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
