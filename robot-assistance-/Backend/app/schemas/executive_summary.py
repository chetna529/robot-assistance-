from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ExecutiveSummary(BaseModel):
    meetings: list[dict[str, Any]]
    reminders: list[dict[str, Any]]
    weather: dict[str, Any]
    notifications: list[dict[str, Any]]

    model_config = ConfigDict(from_attributes=True)


class ActivityLogEntry(BaseModel):
    action: str
    entity_type: str | None = None
    entity_id: int | None = None
    performed_by: str | None = None
    details: dict[str, Any] = {}
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
