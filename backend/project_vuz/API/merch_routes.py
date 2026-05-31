from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from API.deps import get_current_student
from core.database import get_db
from core.merch_catalog import MERCH_BY_ID, MERCH_PRODUCTS
from core.points import compute_available_points, sync_student_points
from models.merch import MerchOrder, MerchOrderItem
from models.rating import Student
from Shemas.merch import (
    MerchOrderCreateRequest,
    MerchOrderLineResponse,
    MerchOrderResponse,
    MerchProductResponse,
)

router = APIRouter()


@router.get("/merch/products", response_model=list[MerchProductResponse])
def list_merch_products():
    return [MerchProductResponse(**p) for p in MERCH_PRODUCTS]


@router.post("/merch/orders", response_model=MerchOrderResponse, status_code=201)
def create_merch_order(
    payload: MerchOrderCreateRequest,
    student: Annotated[Student, Depends(get_current_student)],
    db: Annotated[Session, Depends(get_db)],
):
    if not payload.items:
        raise HTTPException(status_code=400, detail="Корзина пуста")

    aggregated: dict[str, int] = {}
    for line in payload.items:
        if line.quantity < 1:
            raise HTTPException(status_code=400, detail="Количество должно быть не меньше 1")
        if line.product_id not in MERCH_BY_ID:
            raise HTTPException(
                status_code=400,
                detail=f"Неизвестный товар: {line.product_id}",
            )
        aggregated[line.product_id] = aggregated.get(line.product_id, 0) + line.quantity

    total = sum(
        MERCH_BY_ID[pid]["price"] * qty for pid, qty in aggregated.items()
    )
    available = compute_available_points(db, student.id)
    if total > available:
        raise HTTPException(
            status_code=400,
            detail=f"Недостаточно вишенок: нужно {total}, доступно {available}",
        )

    order = MerchOrder(student_id=student.id, total_points=total)
    for product_id, quantity in aggregated.items():
        product = MERCH_BY_ID[product_id]
        line_total = product["price"] * quantity
        order.items.append(
            MerchOrderItem(
                product_id=product_id,
                product_name=product["name"],
                unit_price=product["price"],
                quantity=quantity,
                line_total=line_total,
            )
        )

    db.add(order)
    db.flush()
    sync_student_points(db, student)
    db.commit()
    db.refresh(order)
    db.refresh(student)

    return MerchOrderResponse(
        id=order.id,
        total_points=order.total_points,
        available_points=student.available_points,
        items=[
            MerchOrderLineResponse(
                product_id=item.product_id,
                product_name=item.product_name,
                unit_price=item.unit_price,
                quantity=item.quantity,
                line_total=item.line_total,
            )
            for item in order.items
        ],
    )
