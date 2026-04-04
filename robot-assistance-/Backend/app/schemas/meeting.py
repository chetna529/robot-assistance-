from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MeetingBase(BaseModel):
    title: str
    description: str | None = None
    start_time: datetime
    end_time: datetime
    location: str | None = None
    attendees: list[Any] = Field(default_factory=list)
    user_id: int


class MeetingCreate(MeetingBase):
    pass


class MeetingUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    location: str | None = None
    attendees: list[Any] | None = None
    user_id: int | None = None


class Meeting(MeetingBase):
    id: int
    google_event_id: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
