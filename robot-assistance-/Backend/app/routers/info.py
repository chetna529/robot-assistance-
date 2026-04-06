from datetime import datetime, timezone

from fastapi import APIRouter

from app.database import is_mongodb_configured, ping_database
from app.services.google_calendar_service import is_google_calendar_authorized, is_google_calendar_enabled
from app.services.weather_service import is_weather_enabled

router = APIRouter(tags=["Info"])


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
