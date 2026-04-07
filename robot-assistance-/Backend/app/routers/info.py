from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, status

from app.database import is_mongodb_configured, ping_database
from app.services.google_calendar_service import is_google_calendar_authorized, is_google_calendar_enabled
from app.services.activity_log_service import log_activity
from app.database import get_database
from app.services.meeting_service import get_upcoming_meetings
from app.services.notification_service import get_recent_notifications
from app.services.reminder_service import get_pending_reminders
from app.services.weather_service import is_weather_enabled
from app.services.weather_service import get_current_weather
from app.schemas.poc import POCMeeting, POCNotification, POCReminder

router = APIRouter(tags=["Info"])


def _strip_mongo_id(document: dict | None) -> dict | None:
    if document is None:
        return None
    return {key: value for key, value in document.items() if key != "_id"}


def _meeting_poc_payload(document: dict) -> dict:
    return {
        "id": document["id"],
        "title": document["title"],
        "start_time": document["start_time"],
        "end_time": document["end_time"],
        "room": document.get("location"),
        "created_by": document.get("user_id"),
    }


def _reminder_poc_payload(document: dict) -> dict:
    return {
        "id": document["id"],
        "title": document.get("title") or document.get("message") or "Reminder",
        "trigger_time": document.get("remind_at") or document.get("reminder_time"),
        "status": document.get("status") or ("sent" if document.get("is_sent") else "pending"),
        "priority": document.get("priority") or "medium",
    }


def _notification_poc_payload(document: dict) -> dict:
    return {
        "id": document["id"],
        "message": document.get("message") or document.get("content") or "Notification",
        "type": document.get("notification_type") or document.get("channel") or "info",
        "status": document.get("status") or ("sent" if document.get("delivered") else "pending"),
    }



@router.get("/health")
async def health():
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": {
            "type": "mongodb",
            "connected": await ping_database(),
        },
    }


@router.get("/info")
def info():
    return {
        "service": "Humoind Robot Backend",
        "version": "1.0.0",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "database": {
            "type": "mongodb",
            "atlas_uri_configured": is_mongodb_configured(),
        },
        "calendar_capabilities": [
            "meeting_crud",
            "busy_free_status",
            "custom_alert_minutes",
            "recurring_meetings",
            "occurrence_expansion",
        ],
        "integrations": {
            "google_calendar_enabled": is_google_calendar_enabled(),
            "google_calendar_authorized": is_google_calendar_authorized(),
            "weather_enabled": is_weather_enabled(),
        },
    }


@router.get("/info/weather")
async def info_weather(city: str = Query("Kolkata", min_length=2), units: str = Query("metric")):
    try:
        return await get_current_weather(city=city, units=units)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.get("/executive-summary")
async def executive_summary(city: str = Query("Kolkata", min_length=2), units: str = Query("metric")):
    weather = await get_current_weather(city=city, units=units)
    db = get_database()
    meetings = [POCMeeting.model_validate(_meeting_poc_payload(item)).model_dump() for item in await get_upcoming_meetings(db)]
    reminders = [POCReminder.model_validate(_reminder_poc_payload(item)).model_dump() for item in await get_pending_reminders(db)]
    notifications = [
        POCNotification.model_validate(_notification_poc_payload(item)).model_dump()
        for item in await get_recent_notifications(db)
    ]

    await log_activity(
        db,
        action="executive_summary_viewed",
        entity_type="summary",
        entity_id=None,
        performed_by="robot",
        details={"city": city, "units": units},
    )

    return {
        "meetings": meetings,
        "reminders": reminders,
        "weather": weather,
        "notifications": notifications,
    }
