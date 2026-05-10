from __future__ import annotations

from sqlalchemy import Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(String, index=True)
    organizer: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str] = mapped_column(Text)

    # Храним как массив строк (PostgreSQL JSONB)
    categories: Mapped[list[str]] = mapped_column(JSONB, default=list)

    base_reward: Mapped[int] = mapped_column(Integer, default=0)

    # В учебном проекте пока оставим как человекочитаемую строку, как в текущем фронте
    event_date: Mapped[str] = mapped_column(String)

    # Путь/URL картинок (как у вас сейчас в mock: "photos/kot.png", ...)
    images: Mapped[list[str]] = mapped_column(JSONB, default=list)

