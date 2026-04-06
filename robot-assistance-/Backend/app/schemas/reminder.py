from datetime import datetime

from pydantic import BaseModel, ConfigDict, model_validator


class ReminderCreate(BaseModel):
    meeting_id: int
    message: str
    remind_at: datetime | None = None
    minutes_before: int | None = None
    is_sent: bool = False

    @model_validator(mode="after")
    def _validate_time_source(self):
        if self.remind_at is None and self.minutes_before is None:
            raise ValueError("Provide either remind_at or minutes_before")
        if self.minutes_before is not None and self.minutes_before <= 0:
            raise ValueError("minutes_before must be greater than zero")
        return self


class ReminderUpdate(BaseModel):
    message: str | None = None
    remind_at: datetime | None = None
    minutes_before: int | None = None
    is_sent: bool | None = None

    @model_validator(mode="after")
    def _validate_minutes(self):
        if self.minutes_before is not None and self.minutes_before <= 0:
            raise ValueError("minutes_before must be greater than zero")
        return self


class Reminder(BaseModel):
    id: int
    meeting_id: int
    message: str
    remind_at: datetime
    minutes_before: int | None = None
    is_sent: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
