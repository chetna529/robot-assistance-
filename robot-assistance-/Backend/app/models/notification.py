from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base

JSON_TYPE = JSON().with_variant(JSONB(), "postgresql")


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        CheckConstraint(
            "notification_type IN ('info', 'alert', 'greeting', 'system')",
            name="ck_notifications_type",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    # PostgreSQL schema fields
    title = Column(String(255), nullable=False, default="Notification")
    message = Column(Text, nullable=False, default="")
    notification_type = Column(String(50), nullable=False, default="info")
    target = Column(String(50))
    target_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    is_read = Column(Boolean, nullable=False, default=False)
    scheduled_for = Column(DateTime(timezone=True))
    delivered = Column(Boolean, nullable=False, default=False)
    metadata_info = Column(JSON_TYPE, nullable=False, default=dict)

    # Existing API compatibility fields
    meeting_id = Column(Integer, ForeignKey("meetings.id", ondelete="CASCADE"))
    channel = Column(String(50), nullable=False, default="email")
    recipient = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    meeting = relationship("Meeting", back_populates="notifications")
    target_user = relationship("User", back_populates="notifications")
