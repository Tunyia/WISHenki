from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ActivityBase(BaseModel):
    title: str
    organizer: str
    description: str
    categories: list[str] = Field(default_factory=list)
    base_reward: int = 0
    event_date: str
    images: list[str] = Field(default_factory=list)


class ActivityCreate(ActivityBase):
    pass


class ActivityResponse(ActivityBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

