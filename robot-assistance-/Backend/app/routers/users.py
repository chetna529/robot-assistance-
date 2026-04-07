from datetime import datetime, timezone
import hashlib
import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pymongo import ASCENDING

from app.database import get_db, get_next_sequence
from app.schemas.user import User as UserSchema
from app.schemas.user import UserCreate, UserUpdate

router = APIRouter(tags=["Users"])


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _strip_mongo_id(document: dict | None) -> dict | None:
    if document is None:
        return None
    return {key: value for key, value in document.items() if key != "_id"}


def _hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120000)
    return f"pbkdf2_sha256${salt.hex()}${digest.hex()}"


def _user_defaults(document: dict) -> dict:
    data = _strip_mongo_id(document) or {}
    data.setdefault("role", "employee")
    data.setdefault("department", None)
    data.setdefault("is_active", True)
    data.setdefault("face_id", None)
    data.setdefault("preferred_language", "en")
    data.setdefault("created_at", _now_utc())
    data.setdefault("updated_at", _now_utc())
    data.pop("password", None)
    return data


async def _get_user_or_404(db: Any, user_id: int) -> dict:
    user_doc = await db["users"].find_one({"id": user_id})
    if not user_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return _strip_mongo_id(user_doc) or {}


@router.get("/users", response_model=list[UserSchema])
async def list_users(
    active_only: bool = Query(False),
    db: Any = Depends(get_db),
):
    query = {"is_active": True} if active_only else {}
    docs = await db["users"].find(query).sort("id", ASCENDING).to_list(length=5000)
    return [UserSchema.model_validate(_user_defaults(doc)) for doc in docs]


@router.get("/users/{user_id}", response_model=UserSchema)
async def get_user(user_id: int, db: Any = Depends(get_db)):
    user_doc = await _get_user_or_404(db, user_id)
    return UserSchema.model_validate(_user_defaults(user_doc))


@router.post("/users", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Any = Depends(get_db)):
    existing = await db["users"].find_one({"email": user.email}, {"id": 1})
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

    now = _now_utc()
    user_id = await get_next_sequence(db, "users")

    user_doc = {
        "id": user_id,
        "name": user.name,
        "email": user.email,
        "password": _hash_password(user.password) if user.password else None,
        "role": user.role,
        "department": user.department,
        "is_active": user.is_active,
        "face_id": user.face_id,
        "preferred_language": user.preferred_language,
        "created_at": now,
        "updated_at": now,
    }

    await db["users"].insert_one(user_doc)
    return UserSchema.model_validate(_user_defaults(user_doc))


@router.put("/users/{user_id}", response_model=UserSchema)
async def update_user(user_id: int, payload: UserUpdate, db: Any = Depends(get_db)):
    user_doc = await _get_user_or_404(db, user_id)
    update_data = payload.model_dump(exclude_unset=True)

    if "email" in update_data:
        duplicate = await db["users"].find_one({"email": update_data["email"], "id": {"$ne": user_id}}, {"id": 1})
        if duplicate:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

    if "password" in update_data:
        raw_password = update_data.pop("password")
        user_doc["password"] = _hash_password(raw_password) if raw_password else None

    user_doc.update(update_data)
    user_doc["updated_at"] = _now_utc()

    await db["users"].update_one({"id": user_id}, {"$set": user_doc})
    return UserSchema.model_validate(_user_defaults(user_doc))


@router.delete("/users/{user_id}")
async def deactivate_user(user_id: int, db: Any = Depends(get_db)):
    await _get_user_or_404(db, user_id)
    updated_at = _now_utc()
    await db["users"].update_one({"id": user_id}, {"$set": {"is_active": False, "updated_at": updated_at}})
    return {"status": "deactivated", "id": user_id}
