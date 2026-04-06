from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.services.meeting_calendar_service import (
    normalize_alert_minutes,
    normalize_availability,
    normalize_frequency,
    normalize_weekdays,
    validate_meeting_calendar,
)


class MeetingBase(BaseModel):
    title: str
    description: str | None = None
    start_time: datetime
    end_time: datetime
    location: str | None = None
    availability: str = "busy"
    alert_minutes: list[int] = Field(default_factory=lambda: [30])
    is_recurring: bool = False
    recurrence_frequency: str | None = None
    recurrence_interval: int = 1
    recurrence_count: int | None = None
    recurrence_until: datetime | None = None
    recurrence_by_weekday: list[str] = Field(default_factory=list)
    attendees: list[Any] = Field(default_factory=list)
    user_id: int

    @field_validator("availability")
    @classmethod
    def _normalize_availability(cls, value: str) -> str:
        return normalize_availability(value)

    @field_validator("alert_minutes")
    @classmethod
    def _normalize_alert_minutes(cls, value: list[int]) -> list[int]:
        return normalize_alert_minutes(value)

    @field_validator("recurrence_frequency")
    @classmethod
    def _normalize_recurrence_frequency(cls, value: str | None) -> str | None:
        return normalize_frequency(value)

    @field_validator("recurrence_by_weekday")
    @classmethod
    def _normalize_recurrence_by_weekday(cls, value: list[str]) -> list[str]:
        return normalize_weekdays(value)

    @model_validator(mode="after")
    def _validate_calendar_rules(self):
        validate_meeting_calendar(
            start_time=self.start_time,
            end_time=self.end_time,
            availability=self.availability,
            alert_minutes=self.alert_minutes,
            is_recurring=self.is_recurring,
            recurrence_frequency=self.recurrence_frequency,
            recurrence_interval=self.recurrence_interval,
            recurrence_count=self.recurrence_count,
            recurrence_until=self.recurrence_until,
            recurrence_by_weekday=self.recurrence_by_weekday,
        )
        return self


class MeetingCreate(MeetingBase):
    pass


class MeetingUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    location: str | None = None
    availability: str | None = None
    alert_minutes: list[int] | None = None
    is_recurring: bool | None = None
    recurrence_frequency: str | None = None
    recurrence_interval: int | None = None
    recurrence_count: int | None = None
    recurrence_until: datetime | None = None
    recurrence_by_weekday: list[str] | None = None
    attendees: list[Any] | None = None
    user_id: int | None = None

    @field_validator("availability")
    @classmethod
    def _normalize_availability(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return normalize_availability(value)

    @field_validator("alert_minutes")
    @classmethod
    def _normalize_alert_minutes(cls, value: list[int] | None) -> list[int] | None:
        if value is None:
            return None
        return normalize_alert_minutes(value)

    @field_validator("recurrence_frequency")
    @classmethod
    def _normalize_recurrence_frequency(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return normalize_frequency(value)

    @field_validator("recurrence_by_weekday")
    @classmethod
    def _normalize_recurrence_by_weekday(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        return normalize_weekdays(value)


class MeetingAvailabilityUpdate(BaseModel):
    availability: str

    @field_validator("availability")
    @classmethod
    def _normalize_availability(cls, value: str) -> str:
        return normalize_availability(value)


class MeetingAlertsUpdate(BaseModel):
    alert_minutes: list[int]

    @field_validator("alert_minutes")
    @classmethod
    def _normalize_alert_minutes(cls, value: list[int]) -> list[int]:
        return normalize_alert_minutes(value)


class MeetingOccurrence(BaseModel):
    meeting_id: int
    occurrence_index: int
    title: str
    start_time: datetime
    end_time: datetime
    availability: str


class Meeting(MeetingBase):
    id: int
    google_event_id: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
