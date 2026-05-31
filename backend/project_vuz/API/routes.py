from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from API.deps import get_current_student
from core.attendance import cherries_for_attendance
from core.database import get_db
from core.points import sync_student_points
from models.activity import Activity, ActivityAttendance, ActivityEnrollment
from models.rating import Item, Student, Transaction
from Shemas.activity import (
    ActivityCreate,
    ActivityAttendeeResponse,
    ActivityParticipantResponse,
    ActivityResponse,
)
from Shemas.rating import (
    ItemCreate,
    ItemResponse,
    StudentCreate,
    StudentResponse,
    TransactionCreate,
    TransactionResponse,
)

router = APIRouter()


def _student_response(db: Session, student: Student) -> StudentResponse:
    sync_student_points(db, student)
    db.commit()
    db.refresh(student)
    return student


@router.get("/students", response_model=list[StudentResponse])
def list_students(
    db: Annotated[Session, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    students = db.query(Student).offset(skip).limit(limit).all()
    for st in students:
        sync_student_points(db, st)
    db.commit()
    for st in students:
        db.refresh(st)
    return students


@router.post("/students", response_model=StudentResponse, status_code=201)
def create_student(
    payload: StudentCreate,
    db: Annotated[Session, Depends(get_db)],
):
    student = Student(
        full_name=payload.full_name,
        study_group=payload.study_group,
        total_points=0,
        available_points=0,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@router.get("/students/{student_id}", response_model=StudentResponse)
def get_student(
    student_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Студент не найден")
    return _student_response(db, student)


@router.get("/items", response_model=list[ItemResponse])
def list_items(
    db: Annotated[Session, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    return db.query(Item).offset(skip).limit(limit).all()


@router.post("/items", response_model=ItemResponse, status_code=201)
def create_item(
    payload: ItemCreate,
    db: Annotated[Session, Depends(get_db)],
):
    item = Item(name=payload.name, type=payload.type)
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Предмет с таким именем уже есть")
    db.refresh(item)
    return item


@router.get("/transactions", response_model=list[TransactionResponse])
def list_transactions(
    db: Annotated[Session, Depends(get_db)],
    student_id: int | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    q = db.query(Transaction)
    if student_id is not None:
        q = q.filter(Transaction.student_id == student_id)
    return q.order_by(Transaction.id.desc()).offset(skip).limit(limit).all()


@router.post("/transactions", response_model=TransactionResponse, status_code=201)
def create_transaction(
    payload: TransactionCreate,
    db: Annotated[Session, Depends(get_db)],
):
    student = db.get(Student, payload.student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Студент не найден")
    item = db.get(Item, payload.item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Предмет не найден")

    sync_student_points(db, student)
    if payload.points_change < 0 and student.available_points < -payload.points_change:
        raise HTTPException(
            status_code=400,
            detail="Недостаточно доступных баллов для этой операции",
        )

    tx = Transaction(
        student_id=payload.student_id,
        item_id=payload.item_id,
        points_change=payload.points_change,
    )
    db.add(tx)
    db.commit()
    sync_student_points(db, student)
    db.commit()
    db.refresh(tx)
    db.refresh(student)
    return tx


@router.get("/activities", response_model=list[ActivityResponse])
def list_activities(
    db: Annotated[Session, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    time: str | None = Query(
        None,
        description="upcoming — предстоящие, past — прошедшие",
    ),
):
    q = db.query(Activity)
    if time == "upcoming":
        q = q.filter(Activity.is_completed.is_(False))
    elif time == "past":
        q = q.filter(Activity.is_completed.is_(True))
    return q.order_by(Activity.id.desc()).offset(skip).limit(limit).all()


@router.post("/activities", response_model=ActivityResponse, status_code=201)
def create_activity(
    payload: ActivityCreate,
    db: Annotated[Session, Depends(get_db)],
):
    activity = Activity(
        title=payload.title,
        organizer=payload.organizer,
        description=payload.description,
        categories=payload.categories,
        base_reward=payload.base_reward,
        event_date=payload.event_date,
        images=payload.images,
        is_completed=payload.is_completed,
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


@router.get("/activities/{activity_id}", response_model=ActivityResponse)
def get_activity(
    activity_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    activity = db.get(Activity, activity_id)
    if activity is None:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    return activity


@router.get(
    "/activities/{activity_id}/participants",
    response_model=list[ActivityParticipantResponse],
)
def list_activity_participants(
    activity_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    """Записавшиеся на предстоящее мероприятие."""
    activity = db.get(Activity, activity_id)
    if activity is None:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    if activity.is_completed:
        raise HTTPException(
            status_code=400,
            detail="Для прошедшего мероприятия используйте /attendees",
        )
    students = (
        db.query(Student)
        .join(ActivityEnrollment, ActivityEnrollment.student_id == Student.id)
        .filter(ActivityEnrollment.activity_id == activity_id)
        .order_by(ActivityEnrollment.id.asc())
        .all()
    )
    return [
        ActivityParticipantResponse(
            student_id=s.id,
            full_name=s.full_name,
            study_group=s.study_group,
        )
        for s in students
    ]


@router.get(
    "/activities/{activity_id}/attendees",
    response_model=list[ActivityAttendeeResponse],
)
def list_activity_attendees(
    activity_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    """Посетившие прошедшее мероприятие (по ним начисляются вишенки)."""
    activity = db.get(Activity, activity_id)
    if activity is None:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    if not activity.is_completed:
        raise HTTPException(
            status_code=400,
            detail="Мероприятие ещё не завершено — список записавшихся: /participants",
        )
    rows = (
        db.query(ActivityAttendance, Student)
        .join(Student, ActivityAttendance.student_id == Student.id)
        .join(Activity, Activity.id == ActivityAttendance.activity_id)
        .filter(ActivityAttendance.activity_id == activity_id)
        .order_by(
            (Activity.base_reward + ActivityAttendance.bonus_points).desc(),
            ActivityAttendance.id.asc(),
        )
        .all()
    )
    return [
        ActivityAttendeeResponse(
            student_id=student.id,
            full_name=student.full_name,
            study_group=student.study_group,
            bonus_points=att.bonus_points,
            cherries_earned=cherries_for_attendance(activity, att),
        )
        for att, student in rows
    ]


@router.post("/activities/{activity_id}/enroll", status_code=201)
def enroll_in_activity(
    activity_id: int,
    db: Annotated[Session, Depends(get_db)],
    student: Annotated[Student, Depends(get_current_student)],
):
    activity = db.get(Activity, activity_id)
    if activity is None:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    if activity.is_completed:
        raise HTTPException(
            status_code=400,
            detail="На прошедшее мероприятие записаться нельзя",
        )
    exists = (
        db.query(ActivityEnrollment)
        .filter(
            ActivityEnrollment.activity_id == activity_id,
            ActivityEnrollment.student_id == student.id,
        )
        .first()
    )
    if exists is not None:
        raise HTTPException(
            status_code=409,
            detail="Вы уже записаны на это мероприятие",
        )
    db.add(ActivityEnrollment(activity_id=activity_id, student_id=student.id))
    db.commit()
    return {"ok": True}
