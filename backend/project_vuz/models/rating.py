from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String, index=True)
    study_group: Mapped[str] = mapped_column(String)
    total_points: Mapped[int] = mapped_column(Integer, default=0)
    available_points: Mapped[int] = mapped_column(Integer, default=0)

    transactions = relationship("Transaction", back_populates="student")
    user = relationship("User", back_populates="student", uselist=False)
    merch_orders = relationship("MerchOrder", back_populates="student")


class User(Base):
    """Учётная запись студента: почта + пароль, привязка к одной записи Student."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"),
        unique=True,
    )

    student = relationship("Student", back_populates="user")


class Item(Base):
    __tablename__ = "items"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    type: Mapped[str] = mapped_column(String)


class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"))
    points_change: Mapped[int] = mapped_column(Integer)

    student = relationship("Student", back_populates="transactions")
    item = relationship("Item")
