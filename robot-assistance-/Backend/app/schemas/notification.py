from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationBase(BaseModel):
    meeting_id: int
    channel: str = "email"
    recipient: str
    content: str
    delivered: bool = False


class NotificationCreate(NotificationBase):
    pass


class NotificationUpdate(BaseModel):
    channel: str | None = None
    recipient: str | None = None
    content: str | None = None
    delivered: bool | None = None


class Notification(NotificationBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
