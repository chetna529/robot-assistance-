# models/user.py
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String, default="user")  # admin / user
    created_at = Column(DateTime, default=datetime.utcnow)
    
    meetings = relationship("Meeting", back_populates="created_by_user")
    calendar_events = relationship("CalendarEvent", back_populates="user")

# models/calendar_event.py (NEW - added per your request)
class CalendarEvent(Base):
    __tablename__ = "calendar_events"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    location = Column(String)
    google_event_id = Column(String, unique=True)  # sync with Google
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="calendar_events")