import json
import os
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.services.meeting_calendar_service import build_google_rrule, normalize_alert_minutes, normalize_availability

SCOPES = ["https://www.googleapis.com/auth/calendar"]
BACKEND_DIR = Path(__file__).resolve().parents[2]
DEFAULT_SERVICE_ACCOUNT_FILE = BACKEND_DIR / "credentials" / "service-account.json"
DEFAULT_OAUTH_CLIENT_FILE = BACKEND_DIR / "credentials" / "google-oauth-client.json"
DEFAULT_OAUTH_TOKEN_FILE = BACKEND_DIR / "credentials" / "google-token.json"
DEFAULT_REDIRECT_URI = "http://localhost:8000/api/auth/google/callback"


def _resolve_path(raw_value: str | None, default_path: Path) -> Path:
    if raw_value and raw_value.strip():
        candidate = Path(raw_value.strip()).expanduser()
        if not candidate.is_absolute():
            candidate = (BACKEND_DIR / candidate).resolve()
        return candidate
    return default_path


def _service_account_file() -> Path:
    return _resolve_path(os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE"), DEFAULT_SERVICE_ACCOUNT_FILE)


def _oauth_client_file() -> Path:
    return _resolve_path(os.getenv("GOOGLE_OAUTH_CLIENT_FILE"), DEFAULT_OAUTH_CLIENT_FILE)


def _oauth_token_file() -> Path:
    return _resolve_path(os.getenv("GOOGLE_OAUTH_TOKEN_FILE"), DEFAULT_OAUTH_TOKEN_FILE)


def _load_oauth_client_config() -> dict[str, Any] | None:
    client_file = _oauth_client_file()
    if not client_file.is_file():
        return None
    with client_file.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _oauth_redirect_uri(client_config: dict[str, Any]) -> str:
    configured = os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "").strip()
    if configured:
        return configured

    web_config = client_config.get("web", {})
    redirect_uris = web_config.get("redirect_uris", [])
    if redirect_uris:
        return str(redirect_uris[0])

    return DEFAULT_REDIRECT_URI


def _save_oauth_credentials(credentials: Credentials) -> None:
    token_path = _oauth_token_file()
    token_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes,
    }

    with token_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh)


def _oauth_credentials() -> Credentials:
    token_file = _oauth_token_file()
    if not token_file.is_file():
        raise RuntimeError(
            "Google OAuth token not found. Open /api/auth/google/url and complete the callback first."
        )

    credentials = Credentials.from_authorized_user_file(str(token_file), SCOPES)

    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        _save_oauth_credentials(credentials)

    if not credentials.valid:
        raise RuntimeError(
            "Google OAuth credentials are invalid. Re-authorize using /api/auth/google/url."
        )

    return credentials


def is_google_calendar_enabled() -> bool:
    return _service_account_file().is_file() or _oauth_client_file().is_file()


def is_google_calendar_authorized() -> bool:
    return _service_account_file().is_file() or _oauth_token_file().is_file()


def get_google_auth_url() -> str:
    client_config = _load_oauth_client_config()
    if not client_config:
        raise RuntimeError(
            "Google OAuth client config not found. Add credentials/google-oauth-client.json first."
        )

    flow = Flow.from_client_config(client_config, SCOPES)
    flow.redirect_uri = _oauth_redirect_uri(client_config)

    auth_url, _state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return auth_url


async def exchange_google_auth_code(code: str) -> dict[str, Any]:
    client_config = _load_oauth_client_config()
    if not client_config:
        raise RuntimeError(
            "Google OAuth client config not found. Add credentials/google-oauth-client.json first."
        )

    flow = Flow.from_client_config(client_config, SCOPES)
    flow.redirect_uri = _oauth_redirect_uri(client_config)
    flow.fetch_token(code=code)

    credentials = flow.credentials
    _save_oauth_credentials(credentials)

    return {
        "authorized": True,
        "expiry": credentials.expiry.isoformat() if credentials.expiry else None,
        "scopes": credentials.scopes,
    }


def _calendar_client():
    service_account_file = _service_account_file()

    if service_account_file.is_file():
        credentials = service_account.Credentials.from_service_account_file(
            str(service_account_file),
            scopes=SCOPES,
        )
    else:
        if not _oauth_client_file().is_file():
            raise RuntimeError(
                "Google Calendar is not configured yet. "
                "Provide service account file or OAuth client file in Backend/credentials/."
            )
        credentials = _oauth_credentials()

    service = build("calendar", "v3", credentials=credentials)
    calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "").strip() or "primary"
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
    availability = normalize_availability(getattr(meeting, "availability", "busy"))
    alert_minutes = normalize_alert_minutes(getattr(meeting, "alert_minutes", [30]))

    payload = {
        "summary": meeting.title,
        "location": getattr(meeting, "location", "") or "",
        "description": getattr(meeting, "description", f"Meeting ID: {meeting.id}") or f"Meeting ID: {meeting.id}",
        "start": {"dateTime": meeting.start_time.isoformat(), "timeZone": timezone},
        "end": {"dateTime": meeting.end_time.isoformat(), "timeZone": timezone},
        "attendees": _normalized_attendees(getattr(meeting, "attendees", [])),
        "transparency": "transparent" if availability == "free" else "opaque",
    }

    if alert_minutes:
        payload["reminders"] = {
            "useDefault": False,
            "overrides": [{"method": "popup", "minutes": minutes} for minutes in alert_minutes],
        }
    else:
        payload["reminders"] = {"useDefault": True}

    rrule = build_google_rrule(meeting)
    if rrule:
        payload["recurrence"] = [f"RRULE:{rrule}"]

    return payload


async def create_or_update_event(meeting):
    if not is_google_calendar_enabled() or not is_google_calendar_authorized():
        return None

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
    if not is_google_calendar_enabled() or not is_google_calendar_authorized():
        return False

    service, calendar_id = _calendar_client()
    try:
        service.events().delete(calendarId=calendar_id, eventId=google_event_id).execute()
        return True
    except HttpError:
        return False
