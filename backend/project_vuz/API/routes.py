from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.database import get_db
from models.activity import Activity
from models.rating import Item, Student, Transaction
from Shemas.activity import ActivityCreate, ActivityResponse
from Shemas.rating import (
    ItemCreate,
    ItemResponse,
    StudentCreate,
    StudentResponse,
    TransactionCreate,
    TransactionResponse,
)

router = APIRouter()


@router.get("/students", response_model=list[StudentResponse])
def list_students(
    db: Annotated[Session, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    return db.query(Student).offset(skip).limit(limit).all()


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
    return student


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

    new_available = student.available_points + payload.points_change
    if new_available < 0:
        raise HTTPException(
            status_code=400,
            detail="Недостаточно доступных баллов для этой операции",
        )

    if payload.points_change > 0:
        student.total_points += payload.points_change
    student.available_points = new_available

    tx = Transaction(
        student_id=payload.student_id,
        item_id=payload.item_id,
        points_change=payload.points_change,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


@router.get("/activities", response_model=list[ActivityResponse])
def list_activities(
    db: Annotated[Session, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    return db.query(Activity).order_by(Activity.id.desc()).offset(skip).limit(limit).all()


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
