from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "role IN ('employee', 'admin', 'visitor', 'executive')",
            name="ck_users_role",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255))
    role = Column(String(50), nullable=False, default="employee")
    department = Column(String(100))
    is_active = Column(Boolean, nullable=False, default=True)
    face_id = Column(String(100), index=True)
    preferred_language = Column(String(10), nullable=False, default="en")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    meetings = relationship("Meeting", back_populates="owner")
    reminders = relationship("Reminder", back_populates="user")
    notifications = relationship("Notification", back_populates="target_user")
