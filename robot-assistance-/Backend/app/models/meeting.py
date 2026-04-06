from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base

JSON_TYPE = JSON().with_variant(JSONB(), "postgresql")


class Meeting(Base):
    __tablename__ = "meetings"
    __table_args__ = (
        CheckConstraint(
            "status IN ('scheduled', 'ongoing', 'completed', 'cancelled')",
            name="ck_meetings_status",
        ),
        CheckConstraint(
            "availability IN ('busy', 'free', 'tentative', 'out_of_office')",
            name="ck_meetings_availability",
        ),
        Index("idx_meetings_start_time", "start_time"),
        Index("idx_meetings_owner_id", "owner_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    location = Column(String(200))
    description = Column(Text)
    attendees = Column(JSON_TYPE, default=list, nullable=False)
    status = Column(String(50), nullable=False, default="scheduled")
    google_event_id = Column(String(100), unique=True)

    # DB column uses owner_id, API keeps using user_id for backward compatibility
    user_id = Column("owner_id", Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    availability = Column(String(20), nullable=False, default="busy")
    alert_minutes = Column(JSON_TYPE, default=lambda: [30], nullable=False)
    is_recurring = Column(Boolean, nullable=False, default=False)
    recurrence_frequency = Column(String(20))
    recurrence_interval = Column(Integer, nullable=False, default=1)
    recurrence_count = Column(Integer)
    recurrence_until = Column(DateTime(timezone=True))
    recurrence_by_weekday = Column(JSON_TYPE, default=list, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    owner = relationship("User", back_populates="meetings", foreign_keys=[user_id])
    reminders = relationship("Reminder", back_populates="meeting", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="meeting", cascade="all, delete-orphan")
