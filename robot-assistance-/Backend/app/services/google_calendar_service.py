import os
from pathlib import Path
from typing import Any

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/calendar"]
DEFAULT_CREDENTIALS_FILE = Path(__file__).resolve().parents[2] / "credentials" / "service-account.json"


def _calendar_client():
    credentials_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", str(DEFAULT_CREDENTIALS_FILE))
    if not Path(credentials_file).exists():
        raise FileNotFoundError(
            f"Google service account file not found at {credentials_file}. "
            "Set GOOGLE_SERVICE_ACCOUNT_FILE or place credentials at Backend/credentials/service-account.json."
        )

    credentials = service_account.Credentials.from_service_account_file(
        credentials_file,
        scopes=SCOPES,
    )
    service = build("calendar", "v3", credentials=credentials)
    calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "primary")
    return service, calendar_id


def _normalized_attendees(raw_attendees: Any) -> list[dict[str, str]]:
    attendees: list[dict[str, str]] = []
    if not raw_attendees:
        return attendees

    for attendee in raw_attendees:
        if isinstance(attendee, str):
            attendees.append({"email": attendee})
            continue

        if isinstance(attendee, dict) and attendee.get("email"):
            normalized = {"email": attendee["email"]}
            if attendee.get("displayName"):
                normalized["displayName"] = str(attendee["displayName"])
            attendees.append(normalized)

    return attendees


def _build_event_payload(meeting) -> dict[str, Any]:
    timezone = os.getenv("GOOGLE_CALENDAR_TIMEZONE", "Asia/Kolkata")
    payload = {
        "summary": meeting.title,
        "location": getattr(meeting, "location", "") or "",
        "description": getattr(meeting, "description", f"Meeting ID: {meeting.id}") or f"Meeting ID: {meeting.id}",
        "start": {"dateTime": meeting.start_time.isoformat(), "timeZone": timezone},
        "end": {"dateTime": meeting.end_time.isoformat(), "timeZone": timezone},
        "attendees": _normalized_attendees(getattr(meeting, "attendees", [])),
        "reminders": {"useDefault": True},
    }
    return payload


async def create_or_update_event(meeting):
    service, calendar_id = _calendar_client()
    event_body = _build_event_payload(meeting)

    try:
        if getattr(meeting, "google_event_id", None):
            updated = (
                service.events()
                .update(
                    calendarId=calendar_id,
                    eventId=meeting.google_event_id,
                    body=event_body,
                )
                .execute()
            )
            return {"htmlLink": updated.get("htmlLink"), "event_id": updated.get("id")}

        created = (
            service.events()
            .insert(
                calendarId=calendar_id,
                body=event_body,
                sendUpdates="all",
            )
            .execute()
        )
        return {"htmlLink": created.get("htmlLink"), "event_id": created.get("id")}
    except HttpError as exc:
        raise RuntimeError(f"Google Calendar API error: {exc}") from exc


async def delete_event(google_event_id: str) -> bool:
    service, calendar_id = _calendar_client()
    try:
        service.events().delete(calendarId=calendar_id, eventId=google_event_id).execute()
        return True
    except HttpError:
        return False
