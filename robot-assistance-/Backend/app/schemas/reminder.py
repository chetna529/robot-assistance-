from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReminderBase(BaseModel):
    meeting_id: int
    message: str
    remind_at: datetime
    is_sent: bool = False


class ReminderCreate(ReminderBase):
    pass


class ReminderUpdate(BaseModel):
    message: str | None = None
    remind_at: datetime | None = None
    is_sent: bool | None = None


class Reminder(ReminderBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
