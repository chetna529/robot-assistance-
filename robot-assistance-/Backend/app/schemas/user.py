from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

UserRole = Literal["employee", "admin", "visitor", "executive"]


class UserBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: str = Field(min_length=3, max_length=255)
    role: UserRole = "employee"
    department: str | None = Field(default=None, max_length=100)
    is_active: bool = True
    face_id: str | None = Field(default=None, max_length=100)
    preferred_language: str = Field(default="en", min_length=2, max_length=10)

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, value: str) -> str:
        email = value.strip().lower()
        if "@" not in email or email.startswith("@") or email.endswith("@"):
            raise ValueError("email must be valid")
        return email


class UserCreate(UserBase):
    password: str | None = Field(default=None, min_length=8, max_length=255)


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    email: str | None = Field(default=None, min_length=3, max_length=255)
    role: UserRole | None = None
    department: str | None = Field(default=None, max_length=100)
    is_active: bool | None = None
    face_id: str | None = Field(default=None, max_length=100)
    preferred_language: str | None = Field(default=None, min_length=2, max_length=10)
    password: str | None = Field(default=None, min_length=8, max_length=255)

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, value: str | None) -> str | None:
        if value is None:
            return None
        email = value.strip().lower()
        if "@" not in email or email.startswith("@") or email.endswith("@"):
            raise ValueError("email must be valid")
        return email


class User(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
