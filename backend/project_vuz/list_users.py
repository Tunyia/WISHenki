#!/usr/bin/env python3
"""Список зарегистрированных аккаунтов (email + привязанный студент).

Запуск локально (Docker):
  docker compose exec api python list_users.py

Prod на VPS:
  docker compose -f docker-compose.prod.yml --env-file .env exec api python list_users.py

Показать всех студентов рейтинга (в т.ч. без аккаунта):
  docker compose exec api python list_users.py --all-students
"""

from __future__ import annotations

import argparse
import time

from sqlalchemy import text
from sqlalchemy.orm import Session

from core.database import SessionLocal, engine
from models.rating import Student, User


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


def print_accounts(db: Session) -> None:
    rows = (
        db.query(User, Student)
        .join(Student, User.student_id == Student.id)
        .order_by(User.id.asc())
        .all()
    )

    if not rows:
        print("Зарегистрированных аккаунтов нет.")
        print(
            "Подсказка: seed.py создаёт студентов для рейтинга, но не логины. "
            "Аккаунты появляются после регистрации на сайте."
        )
        return

    print(f"Найдено аккаунтов: {len(rows)}\n")
    print(
        f"{'User ID':>7}  {'Student ID':>10}  {'Email':<36}  "
        f"{'ФИО':<28}  {'Группа':<10}  {'Вишенки':>8}"
    )
    print("-" * 110)
    for user, student in rows:
        print(
            f"{user.id:>7}  {student.id:>10}  {user.email:<36}  "
            f"{student.full_name:<28}  {student.study_group:<10}  "
            f"{student.available_points:>8}"
        )


def print_all_students(db: Session) -> None:
    students = db.query(Student).order_by(Student.id.asc()).all()
    if not students:
        print("В таблице students никого нет.")
        return

    user_by_student = {
        u.student_id: u for u in db.query(User).order_by(User.id.asc()).all()
    }

    with_account = sum(1 for s in students if s.id in user_by_student)
    print(
        f"Студентов в рейтинге: {len(students)} "
        f"(с аккаунтом: {with_account}, без аккаунта: {len(students) - with_account})\n"
    )
    print(
        f"{'Student ID':>10}  {'Аккаунт':<36}  {'ФИО':<28}  {'Группа':<10}  {'Вишенки':>8}"
    )
    print("-" * 100)
    for student in students:
        user = user_by_student.get(student.id)
        email = user.email if user else "—"
        print(
            f"{student.id:>10}  {email:<36}  {student.full_name:<28}  "
            f"{student.study_group:<10}  {student.available_points:>8}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Показать зарегистрированные аккаунты (без паролей)"
    )
    parser.add_argument(
        "--all-students",
        action="store_true",
        help="Все записи рейтинга, включая студентов без входа по почте",
    )
    parser.add_argument("--wait", type=int, default=15, help="Секунд ждать БД")
    args = parser.parse_args()

    wait_for_db(timeout_s=args.wait)

    db = SessionLocal()
    try:
        if args.all_students:
            print_all_students(db)
        else:
            print_accounts(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
