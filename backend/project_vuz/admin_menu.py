#!/usr/bin/env python3
"""Интерактивное консольное меню администратора.

Запуск (Docker, интерактивный режим — флаг -it):
  docker compose exec -it api python admin_menu.py

Prod:
  docker compose -f docker-compose.prod.yml --env-file .env exec -it api python admin_menu.py
"""

from __future__ import annotations

import argparse
import sys
import time

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from core.attendance import cherries_for_attendance, upsert_attendance
from core.database import Base, SessionLocal, engine
from core.migrate import ensure_schema_updates
from core.points import sync_student_points
from core.demo_activities import DEMO_TAG
from core.security import hash_password
from models.activity import Activity, ActivityAttendance, ActivityEnrollment
from models.merch import MerchOrder, MerchOrderItem
from models.rating import Student, Transaction, User

PAGE_SIZE = 25


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
    import models.merch  # noqa: F401
    import models.rating  # noqa: F401

    Base.metadata.create_all(bind=engine)
    ensure_schema_updates()


def pause() -> None:
    input("\nEnter — продолжить...")


def clear_screen() -> None:
    print("\n" * 2)


def read_int(prompt: str, *, allow_empty: bool = False) -> int | None:
    while True:
        raw = input(prompt).strip()
        if allow_empty and not raw:
            return None
        try:
            return int(raw)
        except ValueError:
            print("Введите число.")


def read_str(prompt: str, *, allow_empty: bool = False) -> str | None:
    raw = input(prompt).strip()
    if not raw and not allow_empty:
        print("Поле не может быть пустым.")
        return read_str(prompt, allow_empty=allow_empty)
    return raw if raw else None


def read_yes_no(prompt: str) -> bool:
    while True:
        raw = input(f"{prompt} (д/н): ").strip().lower()
        if raw in {"д", "y", "yes", "да"}:
            return True
        if raw in {"н", "n", "no", "нет"}:
            return False
        print("Ответьте «д» или «н».")


def get_user_map(db: Session) -> dict[int, User]:
    return {u.student_id: u for u in db.query(User).all()}


def find_student(db: Session, student_id: int) -> Student | None:
    return db.get(Student, student_id)


def find_activity(db: Session, activity_id: int) -> Activity | None:
    return db.get(Activity, activity_id)


def print_header(title: str) -> None:
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def print_stats(db: Session) -> None:
    students = db.query(Student).count()
    users = db.query(User).count()
    upcoming = db.query(Activity).filter(Activity.is_completed.is_(False)).count()
    past = db.query(Activity).filter(Activity.is_completed.is_(True)).count()
    enrollments = db.query(ActivityEnrollment).count()
    attendances = db.query(ActivityAttendance).count()
    print_header("Статистика")
    print(f"  Студентов в рейтинге:     {students}")
    print(f"  С аккаунтом (users):      {users}")
    print(f"  Без аккаунта:             {students - users}")
    print(f"  Мероприятий предстоящих:  {upcoming}")
    print(f"  Мероприятий прошедших:    {past}")
    print(f"  Записей на мероприятия:   {enrollments}")
    print(f"  Посещений (архив):        {attendances}")
    merch_orders = db.query(MerchOrder).count()
    total_merch_points = int(
        db.query(func.coalesce(func.sum(MerchOrder.total_points), 0)).scalar() or 0
    )
    print(f"  Заказов мерча:            {merch_orders}")
    print(f"  Списано на мерч (вишенки): {total_merch_points}")


def print_students_table(
    db: Session,
    *,
    only_auth: bool | None = None,
    search: str | None = None,
    offset: int = 0,
) -> int:
    """Показать таблицу студентов. Возвращает число показанных строк."""
    user_map = get_user_map(db)
    q = db.query(Student).order_by(Student.id.asc())
    if search:
        like = f"%{search}%"
        q = q.filter(
            (Student.full_name.ilike(like))
            | (Student.study_group.ilike(like))
        )
    rows = q.all()
    if only_auth is True:
        rows = [s for s in rows if s.id in user_map]
    elif only_auth is False:
        rows = [s for s in rows if s.id not in user_map]

    total = len(rows)
    page = rows[offset : offset + PAGE_SIZE]

    label = "Все студенты"
    if only_auth is True:
        label = "Студенты с аккаунтом"
    elif only_auth is False:
        label = "Студенты без аккаунта"
    if search:
        label += f" (поиск: {search!r})"

    print_header(f"{label} — {total} шт., показано {offset + 1}–{offset + len(page)}")
    print(
        f"{'ID':>6}  {'Акк.':<4}  {'Email':<32}  "
        f"{'ФИО':<26}  {'Группа':<10}  {'Дост.':>6}  {'Всего':>6}"
    )
    print("-" * 100)
    for s in page:
        u = user_map.get(s.id)
        acc = "да" if u else "—"
        email = (u.email[:32] if u else "—")[:32]
        name = s.full_name[:26]
        print(
            f"{s.id:>6}  {acc:<4}  {email:<32}  "
            f"{name:<26}  {s.study_group:<10}  "
            f"{s.available_points:>6}  {s.total_points:>6}"
        )
    if offset + PAGE_SIZE < total:
        print(f"\n... ещё {total - offset - PAGE_SIZE} (след. страница: offset {offset + PAGE_SIZE})")
    return len(page)


def print_student_detail(db: Session, student: Student) -> None:
    user = db.query(User).filter(User.student_id == student.id).one_or_none()
    print_header(f"Студент #{student.id}")
    print(f"  ФИО:              {student.full_name}")
    print(f"  Группа:           {student.study_group}")
    print(f"  Доступно вишенок: {student.available_points}")
    print(f"  Всего за семестр: {student.total_points}")
    if user:
        print(f"  Аккаунт:          да (user_id={user.id}, {user.email})")
    else:
        print("  Аккаунт:          нет")

    upcoming = (
        db.query(Activity, ActivityEnrollment)
        .join(ActivityEnrollment, ActivityEnrollment.activity_id == Activity.id)
        .filter(
            ActivityEnrollment.student_id == student.id,
            Activity.is_completed.is_(False),
        )
        .order_by(Activity.id.asc())
        .all()
    )
    print(f"\n  Записан на предстоящие ({len(upcoming)}):")
    for act, _ in upcoming:
        print(f"    [{act.id}] {act.title[:50]}")

    past = (
        db.query(Activity, ActivityAttendance)
        .join(ActivityAttendance, ActivityAttendance.activity_id == Activity.id)
        .filter(
            ActivityAttendance.student_id == student.id,
            Activity.is_completed.is_(True),
        )
        .order_by(Activity.id.asc())
        .all()
    )
    print(f"\n  Посещал прошедшие ({len(past)}):")
    for act, att in past:
        earned = cherries_for_attendance(act, att)
        print(
            f"    [{act.id}] {act.title[:45]} — "
            f"бонус {att.bonus_points}, итого {earned}"
        )


def print_activities_table(
    db: Session,
    *,
    upcoming: bool | None = None,
    offset: int = 0,
) -> None:
    q = db.query(Activity).order_by(Activity.id.asc())
    if upcoming is True:
        q = q.filter(Activity.is_completed.is_(False))
        title = "Предстоящие мероприятия"
    elif upcoming is False:
        q = q.filter(Activity.is_completed.is_(True))
        title = "Прошедшие мероприятия"
    else:
        title = "Все мероприятия"

    rows = q.all()
    total = len(rows)
    page = rows[offset : offset + PAGE_SIZE]

    print_header(f"{title} — {total} шт.")
    print(f"{'ID':>5}  {'Тип':<10}  {'База':>5}  {'Название'}")
    print("-" * 80)
    for a in page:
        kind = "архив" if a.is_completed else "скоро"
        print(f"{a.id:>5}  {kind:<10}  {a.base_reward:>5}  {a.title[:55]}")


def print_activity_participants(db: Session, activity: Activity) -> None:
    print_header(f"Мероприятие #{activity.id}: {activity.title[:50]}")
    print(f"  Тип: {'прошедшее' if activity.is_completed else 'предстоящее'}")
    print(f"  Базовая награда: {activity.base_reward}")

    if activity.is_completed:
        rows = (
            db.query(Student, ActivityAttendance)
            .join(ActivityAttendance, ActivityAttendance.student_id == Student.id)
            .filter(ActivityAttendance.activity_id == activity.id)
            .order_by(ActivityAttendance.bonus_points.desc())
            .all()
        )
        print(f"\n  Посетили ({len(rows)}):")
        for st, att in rows[:50]:
            print(
                f"    [{st.id}] {st.full_name[:30]} — "
                f"бонус {att.bonus_points}, "
                f"итого {cherries_for_attendance(activity, att)}"
            )
        if len(rows) > 50:
            print(f"    ... и ещё {len(rows) - 50}")
    else:
        rows = (
            db.query(Student)
            .join(ActivityEnrollment, ActivityEnrollment.student_id == Student.id)
            .filter(ActivityEnrollment.activity_id == activity.id)
            .order_by(Student.full_name.asc())
            .all()
        )
        print(f"\n  Записались ({len(rows)}):")
        for st in rows[:50]:
            print(f"    [{st.id}] {st.full_name} ({st.study_group})")
        if len(rows) > 50:
            print(f"    ... и ещё {len(rows) - 50}")


def delete_user_account(db: Session, student: Student) -> bool:
    user = db.query(User).filter(User.student_id == student.id).one_or_none()
    if user is None:
        print("У студента нет аккаунта.")
        return False
    email = user.email
    db.delete(user)
    db.commit()
    print(f"Аккаунт {email} удалён. Студент #{student.id} остался в рейтинге без входа.")
    return True


def reset_user_password(db: Session, student: Student) -> bool:
    user = db.query(User).filter(User.student_id == student.id).one_or_none()
    if user is None:
        print("У студента нет аккаунта.")
        return False
    pwd = read_str("Новый пароль: ")
    if not pwd:
        return False
    user.password_hash = hash_password(pwd)
    db.commit()
    print(f"Пароль для {user.email} обновлён.")
    return True


def delete_student_completely(db: Session, student: Student) -> bool:
    if not read_yes_no(
        f"Удалить студента #{student.id} {student.full_name} и ВСЕ связанные данные?"
    ):
        print("Отменено.")
        return False

    db.query(Transaction).filter(Transaction.student_id == student.id).delete()
    db.query(User).filter(User.student_id == student.id).delete()
    db.query(ActivityEnrollment).filter(
        ActivityEnrollment.student_id == student.id
    ).delete()
    db.query(ActivityAttendance).filter(
        ActivityAttendance.student_id == student.id
    ).delete()
    db.delete(student)
    db.commit()
    print("Студент удалён из БД.")
    return True


def enroll_student(db: Session, activity: Activity, student: Student) -> bool:
    if activity.is_completed:
        print("Мероприятие уже прошло — используйте «отметить посещение».")
        return False
    exists = (
        db.query(ActivityEnrollment)
        .filter(
            ActivityEnrollment.activity_id == activity.id,
            ActivityEnrollment.student_id == student.id,
        )
        .first()
    )
    if exists:
        print("Уже записан.")
        return False
    db.add(ActivityEnrollment(activity_id=activity.id, student_id=student.id))
    db.commit()
    print(f"Студент #{student.id} записан на «{activity.title[:40]}».")
    return True


def unenroll_student(db: Session, activity: Activity, student: Student) -> bool:
    if activity.is_completed:
        print("Для прошедших — «снять посещение».")
        return False
    row = (
        db.query(ActivityEnrollment)
        .filter(
            ActivityEnrollment.activity_id == activity.id,
            ActivityEnrollment.student_id == student.id,
        )
        .first()
    )
    if row is None:
        print("Не был записан.")
        return False
    db.delete(row)
    db.commit()
    print("Запись снята.")
    return True


def add_attendance(
    db: Session,
    activity: Activity,
    student: Student,
    bonus_points: int = 0,
) -> bool:
    if not activity.is_completed:
        print("Мероприятие ещё не завершено — используйте «записать».")
        return False
    row = upsert_attendance(db, activity, student, bonus_points=bonus_points)
    sync_student_points(db, student)
    db.commit()
    db.refresh(student)
    earned = cherries_for_attendance(activity, row)
    print(
        f"Посещение добавлено. Бонус={bonus_points}, "
        f"итого за мероприятие={earned}. Баланс студента: {student.available_points}"
    )
    return True


def remove_attendance(db: Session, activity: Activity, student: Student) -> bool:
    row = (
        db.query(ActivityAttendance)
        .filter(
            ActivityAttendance.activity_id == activity.id,
            ActivityAttendance.student_id == student.id,
        )
        .first()
    )
    if row is None:
        print("Посещения не было.")
        return False
    db.delete(row)
    sync_student_points(db, student)
    db.commit()
    db.refresh(student)
    print(f"Посещение снято. Баланс: {student.available_points}")
    return True


def pick_student(db: Session) -> Student | None:
    sid = read_int("ID студента: ")
    if sid is None:
        return None
    st = find_student(db, sid)
    if st is None:
        print("Студент не найден.")
    return st


def pick_activity(db: Session) -> Activity | None:
    aid = read_int("ID мероприятия: ")
    if aid is None:
        return None
    act = find_activity(db, aid)
    if act is None:
        print("Мероприятие не найдено.")
    return act


def collect_known_tags(db: Session) -> list[str]:
    tags: set[str] = {DEMO_TAG}
    for act in db.query(Activity).all():
        for cat in act.categories or []:
            if cat:
                tags.add(cat)
    return sorted(tags, key=str.casefold)


def pick_tags(db: Session) -> list[str]:
    known = collect_known_tags(db)
    print("\nДоступные теги (номера через запятую, обязательно хотя бы один):")
    for i, tag in enumerate(known, start=1):
        print(f"  {i} — {tag}")
    raw = input("Выбор: ").strip()
    if not raw:
        return []
    selected: list[str] = []
    for part in raw.replace(";", ",").split(","):
        part = part.strip()
        if not part:
            continue
        if part.isdigit():
            idx = int(part) - 1
            if 0 <= idx < len(known):
                tag = known[idx]
                if tag not in selected:
                    selected.append(tag)
            else:
                print(f"  Пропущен номер {part}")
        elif part not in selected:
            selected.append(part)
    return selected


def create_activity(db: Session) -> bool:
    title = read_str("Название: ")
    if not title:
        return False
    if db.query(Activity).filter(Activity.title == title).first():
        print("Мероприятие с таким названием уже есть.")
        return False
    organizer = read_str("Организатор: ") or "—"
    description = read_str("Описание: ") or ""
    event_date = read_str("Дата (строка, напр. «25 Мая, 10:00»): ") or "—"
    base_reward = read_int("Базовая награда (вишенки): ") or 0
    categories = pick_tags(db)
    if not categories:
        print("Нужно выбрать хотя бы один тег.")
        return False

    act = Activity(
        title=title,
        organizer=organizer,
        description=description,
        categories=categories,
        base_reward=max(0, base_reward),
        event_date=event_date,
        images=[],
        is_completed=False,
    )
    db.add(act)
    db.commit()
    db.refresh(act)
    print(f"Создано мероприятие #{act.id}: {act.title}")
    print(f"  Теги: {', '.join(categories)}")
    return True


def delete_activity(db: Session, activity: Activity) -> bool:
    enrollments = (
        db.query(ActivityEnrollment)
        .filter(ActivityEnrollment.activity_id == activity.id)
        .count()
    )
    attendances = (
        db.query(ActivityAttendance)
        .filter(ActivityAttendance.activity_id == activity.id)
        .count()
    )
    print(
        f"Мероприятие #{activity.id}: {activity.title}\n"
        f"  Записей: {enrollments}, посещений: {attendances}"
    )
    if not read_yes_no("Удалить мероприятие и все связанные записи?"):
        print("Отменено.")
        return False

    db.query(ActivityEnrollment).filter(
        ActivityEnrollment.activity_id == activity.id
    ).delete()
    db.query(ActivityAttendance).filter(
        ActivityAttendance.activity_id == activity.id
    ).delete()
    db.delete(activity)
    db.commit()
    print("Мероприятие удалено.")
    return True


def menu_students(db: Session) -> None:
    offset = 0
    while True:
        print_header("Студенты")
        print("  1 — все студенты")
        print("  2 — только с аккаунтом")
        print("  3 — только без аккаунта")
        print("  4 — поиск по ФИО / группе")
        print("  5 — карточка студента")
        print("  6 — удалить только аккаунт (студент остаётся)")
        print("  7 — сбросить пароль аккаунта")
        print("  8 — удалить студента из БД полностью")
        print("  9 — следующая страница списка")
        print("  0 — назад")
        choice = read_int("Выбор: ")

        if choice == 0:
            return
        if choice == 1:
            offset = 0
            print_students_table(db, only_auth=None, offset=offset)
            pause()
        elif choice == 2:
            offset = 0
            print_students_table(db, only_auth=True, offset=offset)
            pause()
        elif choice == 3:
            offset = 0
            print_students_table(db, only_auth=False, offset=offset)
            pause()
        elif choice == 4:
            q = read_str("Строка поиска: ", allow_empty=False)
            offset = 0
            print_students_table(db, search=q, offset=offset)
            pause()
        elif choice == 5:
            st = pick_student(db)
            if st:
                print_student_detail(db, st)
                pause()
        elif choice == 6:
            st = pick_student(db)
            if st:
                delete_user_account(db, st)
                pause()
        elif choice == 7:
            st = pick_student(db)
            if st:
                reset_user_password(db, st)
                pause()
        elif choice == 8:
            st = pick_student(db)
            if st:
                delete_student_completely(db, st)
                pause()
        elif choice == 9:
            offset += PAGE_SIZE
            print_students_table(db, offset=offset)
            pause()
        else:
            print("Неверный пункт.")


def menu_activities(db: Session) -> None:
    while True:
        print_header("Мероприятия")
        print("  1 — все мероприятия")
        print("  2 — предстоящие")
        print("  3 — прошедшие (архив)")
        print("  4 — участники / посетители мероприятия")
        print("  5 — записать студента (предстоящее)")
        print("  6 — выписать студента (предстоящее)")
        print("  7 — отметить посещение + бонус (архив)")
        print("  8 — снять посещение (архив)")
        print("  9 — добавить предстоящее мероприятие")
        print(" 10 — удалить мероприятие")
        print("  0 — назад")
        choice = read_int("Выбор: ")

        if choice == 0:
            return
        if choice in {1, 2, 3}:
            upcoming = {1: None, 2: True, 3: False}[choice]
            print_activities_table(db, upcoming=upcoming)
            pause()
        elif choice == 4:
            act = pick_activity(db)
            if act:
                print_activity_participants(db, act)
                pause()
        elif choice == 5:
            act = pick_activity(db)
            st = pick_student(db)
            if act and st:
                enroll_student(db, act, st)
                pause()
        elif choice == 6:
            act = pick_activity(db)
            st = pick_student(db)
            if act and st:
                unenroll_student(db, act, st)
                pause()
        elif choice == 7:
            act = pick_activity(db)
            st = pick_student(db)
            if act and st:
                bonus = read_int("Бонусные вишенки (0 если только база): ") or 0
                add_attendance(db, act, st, bonus_points=max(0, bonus))
                pause()
        elif choice == 8:
            act = pick_activity(db)
            st = pick_student(db)
            if act and st:
                remove_attendance(db, act, st)
                pause()
        elif choice == 9:
            create_activity(db)
            pause()
        elif choice == 10:
            act = pick_activity(db)
            if act:
                delete_activity(db, act)
                pause()
        else:
            print("Неверный пункт.")


def menu_accounts(db: Session) -> None:
    while True:
        print_header("Аккаунты")
        print("  1 — список всех аккаунтов")
        print("  2 — удалить аккаунт по user_id")
        print("  3 — удалить аккаунт по email")
        print("  0 — назад")
        choice = read_int("Выбор: ")

        if choice == 0:
            return
        if choice == 1:
            rows = (
                db.query(User, Student)
                .join(Student, User.student_id == Student.id)
                .order_by(User.id.asc())
                .all()
            )
            print(f"\nАккаунтов: {len(rows)}\n")
            for u, s in rows:
                print(f"  user={u.id}  student={s.id}  {u.email}  {s.full_name}")
            pause()
        elif choice == 2:
            uid = read_int("user_id: ")
            if uid is None:
                continue
            user = db.get(User, uid)
            if not user:
                print("Не найден.")
                continue
            st = find_student(db, user.student_id)
            if st and read_yes_no(f"Удалить аккаунт {user.email}?"):
                delete_user_account(db, st)
            pause()
        elif choice == 3:
            email = read_str("Email: ")
            if not email:
                continue
            user = db.query(User).filter(User.email == email.lower()).one_or_none()
            if not user:
                print("Не найден.")
                continue
            st = find_student(db, user.student_id)
            if st and read_yes_no(f"Удалить аккаунт {user.email}?"):
                delete_user_account(db, st)
            pause()
        else:
            print("Неверный пункт.")


def format_order_datetime(value) -> str:
    if value is None:
        return "—"
    try:
        return value.strftime("%d.%m.%Y %H:%M")
    except AttributeError:
        return str(value)


def print_merch_orders_table(
    db: Session,
    *,
    student_id: int | None = None,
    offset: int = 0,
) -> int:
    q = (
        db.query(MerchOrder, Student)
        .join(Student, Student.id == MerchOrder.student_id)
        .order_by(MerchOrder.created_at.desc(), MerchOrder.id.desc())
    )
    if student_id is not None:
        q = q.filter(MerchOrder.student_id == student_id)

    rows = q.all()
    total = len(rows)
    page = rows[offset : offset + PAGE_SIZE]

    if student_id is not None:
        print(f"\nЗаказы студента #{student_id}: {total} шт.")
    else:
        print(f"\nВсе заказы мерча: {total} шт.")
    if not page:
        print("  (пусто)")
        return 0

    print(f"  Показано {offset + 1}–{offset + len(page)} из {total}\n")
    for order, student in page:
        items_count = len(order.items)
        print(
            f"  #{order.id:>4}  {format_order_datetime(order.created_at)}  "
            f"{student.full_name} ({student.study_group})  "
            f"{order.total_points} виш.  позиций: {items_count}"
        )
    return len(page)


def print_merch_order_detail(db: Session, order_id: int) -> None:
    order = db.get(MerchOrder, order_id)
    if not order:
        print("Заказ не найден.")
        return
    student = db.get(Student, order.student_id)
    print_header(f"Заказ мерча #{order.id}")
    if student:
        print(f"  Студент:   {student.full_name} ({student.study_group}), id={student.id}")
    else:
        print(f"  Студент:   id={order.student_id} (удалён)")
    print(f"  Дата:      {format_order_datetime(order.created_at)}")
    print(f"  Итого:     {order.total_points} вишенок")
    print("\n  Состав заказа:")
    if not order.items:
        print("    (нет позиций)")
        return
    for item in order.items:
        print(
            f"    • {item.product_name}  "
            f"{item.quantity} × {item.unit_price} = {item.line_total} виш."
        )


def menu_merch_orders(db: Session) -> None:
    offset = 0
    filter_student_id: int | None = None
    while True:
        print_header("Заказы мерча")
        if filter_student_id is not None:
            st = db.get(Student, filter_student_id)
            label = st.full_name if st else f"id={filter_student_id}"
            print(f"  Фильтр: студент {label}")
        print("  1 — все заказы (список)")
        print("  2 — детали заказа по ID")
        print("  3 — заказы конкретного студента")
        print("  4 — сбросить фильтр по студенту")
        print("  9 — следующая страница списка")
        print("  0 — назад")
        choice = read_int("Выбор: ")

        if choice == 0:
            return
        if choice == 1:
            offset = 0
            shown = print_merch_orders_table(
                db, student_id=filter_student_id, offset=offset
            )
            if shown == PAGE_SIZE:
                print("\n  (есть ещё — пункт 9)")
            pause()
        elif choice == 2:
            oid = read_int("ID заказа: ")
            if oid is None:
                continue
            print_merch_order_detail(db, oid)
            pause()
        elif choice == 3:
            sid = read_int("student_id: ")
            if sid is None:
                continue
            if not db.get(Student, sid):
                print("Студент не найден.")
            else:
                filter_student_id = sid
                offset = 0
            pause()
        elif choice == 4:
            filter_student_id = None
            offset = 0
            print("Фильтр сброшен.")
            pause()
        elif choice == 9:
            offset += PAGE_SIZE
            shown = print_merch_orders_table(
                db, student_id=filter_student_id, offset=offset
            )
            if shown == 0:
                print("Больше записей нет.")
                offset = max(0, offset - PAGE_SIZE)
            pause()
        else:
            print("Неверный пункт.")


def main_menu(db: Session) -> None:
    while True:
        print_header("WISHenki — меню администратора")
        print("  1 — студенты")
        print("  2 — мероприятия (запись / посещения)")
        print("  3 — аккаунты")
        print("  4 — статистика")
        print("  5 — заказы мерча")
        print("  0 — выход")
        choice = read_int("Выбор: ")

        if choice == 0:
            print("Выход.")
            return
        if choice == 1:
            menu_students(db)
        elif choice == 2:
            menu_activities(db)
        elif choice == 3:
            menu_accounts(db)
        elif choice == 4:
            print_stats(db)
            pause()
        elif choice == 5:
            menu_merch_orders(db)
        else:
            print("Неверный пункт.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Консольное меню администратора")
    parser.add_argument("--wait", type=int, default=30, help="Секунд ждать БД")
    args = parser.parse_args()

    if not sys.stdin.isatty():
        print(
            "Запустите в интерактивном режиме: docker compose exec -it api python admin_menu.py",
            file=sys.stderr,
        )
        sys.exit(1)

    wait_for_db(timeout_s=args.wait)
    ensure_schema()

    db = SessionLocal()
    try:
        main_menu(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
