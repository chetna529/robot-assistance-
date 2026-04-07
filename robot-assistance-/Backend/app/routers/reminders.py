from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pymongo import ASCENDING

from app.database import get_db, get_next_sequence
from app.services.activity_log_service import log_activity
from app.schemas.poc import POCReminder
from app.schemas.reminder import Reminder as ReminderSchema
from app.schemas.reminder import ReminderCreate, ReminderUpdate

router = APIRouter(tags=["Reminders"])


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _strip_mongo_id(document: dict | None) -> dict | None:
    if document is None:
        return None
    return {key: value for key, value in document.items() if key != "_id"}


def _remind_at_from_minutes_before(meeting_start: datetime, minutes_before: int):
    return meeting_start - timedelta(minutes=minutes_before)


def _reminder_defaults(document: dict) -> dict:
    data = _strip_mongo_id(document) or {}
    data.setdefault("minutes_before", None)
    data.setdefault("is_sent", False)
    data.setdefault("created_at", _now_utc())
    return data


def _reminder_poc_payload(document: dict) -> dict:
    data = _reminder_defaults(document)
    status = data.get("status") or ("sent" if data.get("is_sent") else "pending")
    priority = data.get("priority") or "medium"
    return {
        "id": data["id"],
        "title": data.get("title") or data.get("message") or "Reminder",
        "trigger_time": data.get("remind_at") or data.get("reminder_time"),
        "status": status,
        "priority": priority,
    }


async def _get_reminder_or_404(db: Any, reminder_id: int) -> dict:
    reminder = await db["reminders"].find_one({"id": reminder_id})
    if not reminder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found")
    return _reminder_defaults(reminder)


@router.get("/reminders", response_model=list[POCReminder])
async def get_all_reminders(db: Any = Depends(get_db)):
    docs = await db["reminders"].find().sort("remind_at", ASCENDING).to_list(length=5000)
    return [POCReminder.model_validate(_reminder_poc_payload(doc)) for doc in docs]


@router.get("/meetings/{meeting_id}/reminders", response_model=list[POCReminder])
async def get_meeting_reminders(meeting_id: int, db: Any = Depends(get_db)):
    docs = await db["reminders"].find({"meeting_id": meeting_id}).sort("remind_at", ASCENDING).to_list(length=2000)
    return [POCReminder.model_validate(_reminder_poc_payload(doc)) for doc in docs]


@router.post("/reminders", response_model=POCReminder, status_code=status.HTTP_201_CREATED)
async def create_reminder(reminder: ReminderCreate, db: Any = Depends(get_db)):
    meeting_doc = await db["meetings"].find_one({"id": reminder.meeting_id})
    if not meeting_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")

    remind_at = reminder.remind_at
    if reminder.minutes_before is not None:
        remind_at = _remind_at_from_minutes_before(meeting_doc["start_time"], reminder.minutes_before)

    if remind_at is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provide remind_at or minutes_before")

    reminder_id = await get_next_sequence(db, "reminders")
    now = _now_utc()
    reminder_doc = {
        "id": reminder_id,
        "meeting_id": reminder.meeting_id,
        "message": reminder.message,
        "minutes_before": reminder.minutes_before,
        "remind_at": remind_at,
        "is_sent": reminder.is_sent,
        "created_at": now,
        "title": reminder.message,
        "description": None,
        "reminder_time": remind_at,
        "priority": "medium",
        "is_recurring": False,
        "recurrence_pattern": None,
        "user_id": meeting_doc.get("user_id"),
    }

    await db["reminders"].insert_one(reminder_doc)
    try:
        await log_activity(
            db,
            action="reminder_created",
            entity_type="reminder",
            entity_id=reminder_id,
            performed_by=str(reminder_doc.get("user_id") or "robot"),
            details={"meeting_id": reminder.meeting_id, "message": reminder.message},
        )
    except Exception:  # noqa: BLE001
        pass
    return POCReminder.model_validate(_reminder_poc_payload(reminder_doc))


@router.put("/reminders/{reminder_id}", response_model=POCReminder)
async def update_reminder(reminder_id: int, update: ReminderUpdate, db: Any = Depends(get_db)):
    reminder_doc = await _get_reminder_or_404(db, reminder_id)
    update_data = update.model_dump(exclude_unset=True)

    if "minutes_before" in update_data:
        minutes_before = update_data["minutes_before"]
        if minutes_before is None:
            reminder_doc["minutes_before"] = None
        else:
            meeting_doc = await db["meetings"].find_one({"id": reminder_doc["meeting_id"]})
            if not meeting_doc:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
            reminder_doc["minutes_before"] = minutes_before
            remind_at = _remind_at_from_minutes_before(meeting_doc["start_time"], minutes_before)
            reminder_doc["remind_at"] = remind_at
            reminder_doc["reminder_time"] = remind_at

    if "remind_at" in update_data and update_data["remind_at"] is not None:
        reminder_doc["remind_at"] = update_data["remind_at"]
        reminder_doc["reminder_time"] = update_data["remind_at"]
        if "minutes_before" not in update_data:
            reminder_doc["minutes_before"] = None

    if "message" in update_data and update_data["message"] is not None:
        reminder_doc["message"] = update_data["message"]
        reminder_doc["title"] = update_data["message"]

    if "is_sent" in update_data:
        reminder_doc["is_sent"] = update_data["is_sent"]

    await db["reminders"].update_one({"id": reminder_id}, {"$set": reminder_doc})
    try:
        await log_activity(
            db,
            action="reminder_updated",
            entity_type="reminder",
            entity_id=reminder_id,
            performed_by=str(reminder_doc.get("user_id") or "robot"),
            details={"meeting_id": reminder_doc.get("meeting_id"), "message": reminder_doc.get("message")},
        )
    except Exception:  # noqa: BLE001
        pass
    return POCReminder.model_validate(_reminder_poc_payload(reminder_doc))


@router.delete("/reminders/{reminder_id}")
async def delete_reminder(reminder_id: int, db: Any = Depends(get_db)):
    await _get_reminder_or_404(db, reminder_id)
    await db["reminders"].delete_one({"id": reminder_id})
    try:
        await log_activity(
            db,
            action="reminder_deleted",
            entity_type="reminder",
            entity_id=reminder_id,
            performed_by="robot",
            details={"reminder_id": reminder_id},
        )
    except Exception:  # noqa: BLE001
        pass
    return {"status": "deleted", "id": reminder_id}
