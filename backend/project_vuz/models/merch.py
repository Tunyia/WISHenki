from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class MerchOrder(Base):
    __tablename__ = "merch_orders"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"),
        index=True,
    )
    total_points: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    items = relationship(
        "MerchOrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
    )
    student = relationship("Student", back_populates="merch_orders")


class MerchOrderItem(Base):
    __tablename__ = "merch_order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("merch_orders.id", ondelete="CASCADE"),
        index=True,
    )
    product_id: Mapped[str] = mapped_column(String(64))
    product_name: Mapped[str] = mapped_column(String(255))
    unit_price: Mapped[int] = mapped_column(Integer)
    quantity: Mapped[int] = mapped_column(Integer)
    line_total: Mapped[int] = mapped_column(Integer)

    order = relationship("MerchOrder", back_populates="items")
