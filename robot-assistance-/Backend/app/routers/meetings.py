import logging
from datetime import date, datetime, time, timedelta, timezone
from types import SimpleNamespace

from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING

from app.database import get_db, get_next_sequence
from app.schemas.meeting import Meeting as MeetingSchema
from app.schemas.meeting import (
    MeetingAlertsUpdate,
    MeetingAvailabilityUpdate,
    MeetingCreate,
    MeetingOccurrence,
    MeetingUpdate,
)
from app.services.google_calendar_service import create_or_update_event, delete_event, is_google_calendar_enabled
from app.services.meeting_calendar_service import (
    list_meeting_occurrences,
    sanitize_meeting_payload,
    validate_meeting_calendar,
)

router = APIRouter(tags=["Meetings"])
logger = logging.getLogger(__name__)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _strip_mongo_id(document: dict | None) -> dict | None:
    if document is None:
        return None
    return {key: value for key, value in document.items() if key != "_id"}


def _meeting_defaults(document: dict) -> dict:
    data = _strip_mongo_id(document) or {}
    data.setdefault("description", None)
    data.setdefault("location", None)
    data.setdefault("attendees", [])
    data.setdefault("availability", "busy")
    data.setdefault("alert_minutes", [30])
    data.setdefault("is_recurring", False)
    data.setdefault("recurrence_frequency", None)
    data.setdefault("recurrence_interval", 1)
    data.setdefault("recurrence_count", None)
    data.setdefault("recurrence_until", None)
    data.setdefault("recurrence_by_weekday", [])
    data.setdefault("google_event_id", None)
    data.setdefault("created_at", _now_utc())
    data.setdefault("updated_at", _now_utc())
    return data


def _meeting_namespace(document: dict) -> SimpleNamespace:
    return SimpleNamespace(**_meeting_defaults(document))


async def _sync_meeting_to_google(db: AsyncIOMotorDatabase, meeting_doc: dict) -> dict:
    if not is_google_calendar_enabled():
        return meeting_doc

    try:
        result = await create_or_update_event(_meeting_namespace(meeting_doc))
        if isinstance(result, dict) and result.get("event_id"):
            meeting_doc["google_event_id"] = result["event_id"]
            meeting_doc["updated_at"] = _now_utc()
            await db["meetings"].update_one(
                {"id": meeting_doc["id"]},
                {"$set": {"google_event_id": result["event_id"], "updated_at": meeting_doc["updated_at"]}},
            )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Google Calendar sync failed for meeting %s: %s", meeting_doc.get("id"), exc)

    return meeting_doc


def _merged_calendar_payload(meeting_doc: dict, update_data: dict) -> dict:
    source = _meeting_defaults(meeting_doc)
    return {
        "start_time": update_data.get("start_time", source["start_time"]),
        "end_time": update_data.get("end_time", source["end_time"]),
        "availability": update_data.get("availability", source["availability"]),
        "alert_minutes": update_data.get("alert_minutes", source["alert_minutes"]),
        "is_recurring": update_data.get("is_recurring", source["is_recurring"]),
        "recurrence_frequency": update_data.get("recurrence_frequency", source["recurrence_frequency"]),
        "recurrence_interval": update_data.get("recurrence_interval", source["recurrence_interval"]),
        "recurrence_count": update_data.get("recurrence_count", source["recurrence_count"]),
        "recurrence_until": update_data.get("recurrence_until", source["recurrence_until"]),
        "recurrence_by_weekday": update_data.get("recurrence_by_weekday", source["recurrence_by_weekday"]),
    }


async def _sync_relative_reminders(db: AsyncIOMotorDatabase, meeting_doc: dict) -> None:
    if "start_time" not in meeting_doc:
        return

    reminder_cursor = db["reminders"].find(
        {"meeting_id": meeting_doc["id"], "minutes_before": {"$ne": None}}
    )
    reminders = await reminder_cursor.to_list(length=2000)

    for reminder in reminders:
        minutes_before = reminder.get("minutes_before")
        if minutes_before is None:
            continue

        remind_at = meeting_doc["start_time"] - timedelta(minutes=int(minutes_before))
        await db["reminders"].update_one(
            {"id": reminder["id"]},
            {"$set": {"remind_at": remind_at, "reminder_time": remind_at}},
        )


async def _get_meeting_or_404(db: AsyncIOMotorDatabase, meeting_id: int) -> dict:
    meeting = await db["meetings"].find_one({"id": meeting_id})
    if not meeting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
    return _meeting_defaults(meeting)


@router.get("/meetings", response_model=list[MeetingSchema])
async def get_all_meetings(db: AsyncIOMotorDatabase = Depends(get_db)):
    docs = await db["meetings"].find().sort("start_time", ASCENDING).to_list(length=5000)
    return [MeetingSchema.model_validate(_meeting_defaults(doc)) for doc in docs]


@router.get("/meetings/today", response_model=list[MeetingSchema])
async def get_today_meetings(db: AsyncIOMotorDatabase = Depends(get_db)):
    today_start = datetime.combine(date.today(), time.min)
    tomorrow_start = today_start + timedelta(days=1)

    docs = await db["meetings"].find(
        {"start_time": {"$gte": today_start, "$lt": tomorrow_start}}
    ).sort("start_time", ASCENDING).to_list(length=5000)

    return [MeetingSchema.model_validate(_meeting_defaults(doc)) for doc in docs]


@router.get("/meetings/{meeting_id}", response_model=MeetingSchema)
async def get_meeting(meeting_id: int, db: AsyncIOMotorDatabase = Depends(get_db)):
    meeting = await _get_meeting_or_404(db, meeting_id)
    return MeetingSchema.model_validate(meeting)


@router.get("/meetings/{meeting_id}/occurrences", response_model=list[MeetingOccurrence])
async def get_meeting_occurrences(
    meeting_id: int,
    range_start: datetime = Query(...),
    range_end: datetime = Query(...),
    limit: int = Query(200, ge=1, le=1000),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    meeting = await _get_meeting_or_404(db, meeting_id)

    try:
        occurrences = list_meeting_occurrences(
            _meeting_namespace(meeting),
            range_start=range_start,
            range_end=range_end,
            limit=limit,
        )
        return [MeetingOccurrence.model_validate(item) for item in occurrences]
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/meetings", response_model=MeetingSchema, status_code=status.HTTP_201_CREATED)
async def create_meeting(meeting: MeetingCreate, db: AsyncIOMotorDatabase = Depends(get_db)):
    payload = sanitize_meeting_payload(meeting.model_dump(), is_create=True)

    try:
        validate_meeting_calendar(**{
            key: payload[key]
            for key in [
                "start_time",
                "end_time",
                "availability",
                "alert_minutes",
                "is_recurring",
                "recurrence_frequency",
                "recurrence_interval",
                "recurrence_count",
                "recurrence_until",
                "recurrence_by_weekday",
            ]
        })
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if payload.get("is_recurring") is False:
        payload["recurrence_frequency"] = None
        payload["recurrence_interval"] = 1
        payload["recurrence_count"] = None
        payload["recurrence_until"] = None
        payload["recurrence_by_weekday"] = []

    now = _now_utc()
    meeting_id = await get_next_sequence(db, "meetings")
    meeting_doc = {
        "id": meeting_id,
        **payload,
        "google_event_id": None,
        "created_at": now,
        "updated_at": now,
    }

    await db["meetings"].insert_one(meeting_doc)
    meeting_doc = await _sync_meeting_to_google(db, meeting_doc)
    return MeetingSchema.model_validate(_meeting_defaults(meeting_doc))


@router.put("/meetings/{meeting_id}", response_model=MeetingSchema)
async def update_meeting(meeting_id: int, update: MeetingUpdate, db: AsyncIOMotorDatabase = Depends(get_db)):
    current_doc = await _get_meeting_or_404(db, meeting_id)

    update_data = sanitize_meeting_payload(update.model_dump(exclude_unset=True), is_create=False)
    merged = _merged_calendar_payload(current_doc, update_data)

    try:
        validate_meeting_calendar(**merged)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if merged["is_recurring"] is False:
        update_data["recurrence_frequency"] = None
        update_data["recurrence_interval"] = 1
        update_data["recurrence_count"] = None
        update_data["recurrence_until"] = None
        update_data["recurrence_by_weekday"] = []

    update_data["updated_at"] = _now_utc()
    updated_doc = {**current_doc, **update_data}

    await db["meetings"].update_one({"id": meeting_id}, {"$set": update_data})

    if "start_time" in update_data:
        await _sync_relative_reminders(db, updated_doc)

    updated_doc = await _sync_meeting_to_google(db, updated_doc)
    return MeetingSchema.model_validate(_meeting_defaults(updated_doc))


@router.patch("/meetings/{meeting_id}/availability", response_model=MeetingSchema)
async def update_meeting_availability(
    meeting_id: int,
    payload: MeetingAvailabilityUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    meeting_doc = await _get_meeting_or_404(db, meeting_id)
    meeting_doc["availability"] = payload.availability
    meeting_doc["updated_at"] = _now_utc()

    await db["meetings"].update_one(
        {"id": meeting_id},
        {"$set": {"availability": payload.availability, "updated_at": meeting_doc["updated_at"]}},
    )

    meeting_doc = await _sync_meeting_to_google(db, meeting_doc)
    return MeetingSchema.model_validate(_meeting_defaults(meeting_doc))


@router.patch("/meetings/{meeting_id}/alerts", response_model=MeetingSchema)
async def update_meeting_alerts(
    meeting_id: int,
    payload: MeetingAlertsUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    meeting_doc = await _get_meeting_or_404(db, meeting_id)
    meeting_doc["alert_minutes"] = payload.alert_minutes
    meeting_doc["updated_at"] = _now_utc()

    await db["meetings"].update_one(
        {"id": meeting_id},
        {"$set": {"alert_minutes": payload.alert_minutes, "updated_at": meeting_doc["updated_at"]}},
    )

    meeting_doc = await _sync_meeting_to_google(db, meeting_doc)
    return MeetingSchema.model_validate(_meeting_defaults(meeting_doc))


@router.delete("/meetings/{meeting_id}")
async def delete_meeting(meeting_id: int, db: AsyncIOMotorDatabase = Depends(get_db)):
    meeting_doc = await _get_meeting_or_404(db, meeting_id)

    if meeting_doc.get("google_event_id"):
        try:
            await delete_event(meeting_doc["google_event_id"])
        except Exception as exc:  # noqa: BLE001
            logger.warning("Google event delete failed for meeting %s: %s", meeting_id, exc)

    await db["meetings"].delete_one({"id": meeting_id})
    await db["reminders"].delete_many({"meeting_id": meeting_id})
    await db["notifications"].delete_many({"meeting_id": meeting_id})

    return {"status": "deleted", "id": meeting_id}
