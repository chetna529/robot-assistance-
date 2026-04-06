from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class Reminder(Base):
    __tablename__ = "reminders"
    __table_args__ = (
        CheckConstraint(
            "priority IN ('low', 'medium', 'high')",
            name="ck_reminders_priority",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    # PostgreSQL schema fields
    title = Column(String(255), nullable=False, default="Reminder")
    description = Column(Text)
    reminder_time = Column(DateTime(timezone=True), nullable=False)
    priority = Column(String(20), nullable=False, default="medium")
    is_recurring = Column(Boolean, nullable=False, default=False)
    recurrence_pattern = Column(String(50))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    meeting_id = Column(Integer, ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False)

    # Existing API compatibility fields
    message = Column(String(500), nullable=False)
    minutes_before = Column(Integer)
    remind_at = Column(DateTime(timezone=True), nullable=False)
    is_sent = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    meeting = relationship("Meeting", back_populates="reminders")
    user = relationship("User", back_populates="reminders")
