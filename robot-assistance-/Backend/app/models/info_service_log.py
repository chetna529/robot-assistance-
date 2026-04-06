from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.models.base import Base

JSON_TYPE = JSON().with_variant(JSONB(), "postgresql")


class InfoServiceLog(Base):
    __tablename__ = "info_service_logs"

    id = Column(Integer, primary_key=True, index=True)
    service_type = Column(String(50), nullable=False)
    query = Column(Text)
    response = Column(Text)
    response_data = Column(JSON_TYPE)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
