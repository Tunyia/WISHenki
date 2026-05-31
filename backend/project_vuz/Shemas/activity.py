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
    is_completed: bool = False


class ActivityCreate(ActivityBase):
    pass


class ActivityResponse(ActivityBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class ActivityParticipantResponse(BaseModel):
    student_id: int
    full_name: str
    study_group: str

    model_config = ConfigDict(from_attributes=True)


class ActivityAttendeeResponse(ActivityParticipantResponse):
    """Посетивший прошедшее мероприятие с разбивкой начисления."""

    bonus_points: int = 0
    cherries_earned: int = 0

