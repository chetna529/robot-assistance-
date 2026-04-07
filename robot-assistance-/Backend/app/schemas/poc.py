from datetime import datetime

from pydantic import BaseModel, ConfigDict


class POCMeeting(BaseModel):
    id: int
    title: str
    start_time: datetime
    end_time: datetime
    room: str | None = None
    created_by: int | None = None

    model_config = ConfigDict(from_attributes=True)


class POCReminder(BaseModel):
    id: int
    title: str
    trigger_time: datetime
    status: str
    priority: str

    model_config = ConfigDict(from_attributes=True)


class POCNotification(BaseModel):
    id: int
    message: str
    type: str
    status: str

    model_config = ConfigDict(from_attributes=True)
