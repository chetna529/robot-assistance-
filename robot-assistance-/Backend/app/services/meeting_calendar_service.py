from __future__ import annotations

from calendar import monthrange
from datetime import UTC, datetime, timedelta
from typing import Any

ALLOWED_AVAILABILITY = {"busy", "free", "tentative", "out_of_office"}
ALLOWED_RECURRENCE_FREQUENCIES = {"daily", "weekly", "monthly", "yearly"}

_WEEKDAY_INDEX = {
    "MO": 0,
    "TU": 1,
    "WE": 2,
    "TH": 3,
    "FR": 4,
    "SA": 5,
    "SU": 6,
}
_WEEKDAY_ALIASES = {
    "MON": "MO",
    "MONDAY": "MO",
    "TUE": "TU",
    "TUES": "TU",
    "TUESDAY": "TU",
    "WED": "WE",
    "WEDNESDAY": "WE",
    "THU": "TH",
    "THUR": "TH",
    "THURSDAY": "TH",
    "FRI": "FR",
    "FRIDAY": "FR",
    "SAT": "SA",
    "SATURDAY": "SA",
    "SUN": "SU",
    "SUNDAY": "SU",
}


def normalize_availability(value: str | None) -> str:
    normalized = (value or "busy").strip().lower().replace(" ", "_")
    if normalized not in ALLOWED_AVAILABILITY:
        allowed = ", ".join(sorted(ALLOWED_AVAILABILITY))
        raise ValueError(f"availability must be one of: {allowed}")
    return normalized


def normalize_alert_minutes(values: list[int] | None) -> list[int]:
    if values is None:
        return [30]

    normalized: list[int] = []
    for raw in values:
        if isinstance(raw, bool):
            raise ValueError("alert_minutes values must be integers")

        minutes = int(raw)
        if minutes <= 0:
            raise ValueError("alert_minutes values must be greater than zero")
        if minutes > 43200:
            raise ValueError("alert_minutes values cannot exceed 43200 (30 days)")
        normalized.append(minutes)

    return sorted(set(normalized))


def normalize_frequency(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = value.strip().lower()
    if normalized not in ALLOWED_RECURRENCE_FREQUENCIES:
        allowed = ", ".join(sorted(ALLOWED_RECURRENCE_FREQUENCIES))
        raise ValueError(f"recurrence_frequency must be one of: {allowed}")
    return normalized


def normalize_weekdays(values: list[str] | None) -> list[str]:
    if not values:
        return []

    normalized: list[str] = []
    for item in values:
        token = str(item).strip().upper()
        token = _WEEKDAY_ALIASES.get(token, token)
        if token not in _WEEKDAY_INDEX:
            raise ValueError("recurrence_by_weekday must use MO,TU,WE,TH,FR,SA,SU")
        normalized.append(token)

    ordered_unique = sorted(set(normalized), key=lambda day: _WEEKDAY_INDEX[day])
    return ordered_unique


def validate_meeting_calendar(
    *,
    start_time: datetime,
    end_time: datetime,
    availability: str,
    alert_minutes: list[int],
    is_recurring: bool,
    recurrence_frequency: str | None,
    recurrence_interval: int,
    recurrence_count: int | None,
    recurrence_until: datetime | None,
    recurrence_by_weekday: list[str],
) -> None:
    if end_time <= start_time:
        raise ValueError("end_time must be after start_time")

    normalize_availability(availability)
    normalize_alert_minutes(alert_minutes)

    if recurrence_interval < 1:
        raise ValueError("recurrence_interval must be at least 1")

    if recurrence_count is not None and recurrence_count < 1:
        raise ValueError("recurrence_count must be at least 1")

    frequency = normalize_frequency(recurrence_frequency)

    if not is_recurring:
        has_recurrence_data = any(
            [frequency, recurrence_count, recurrence_until, recurrence_by_weekday]
        )
        if has_recurrence_data:
            raise ValueError("Set is_recurring=true before sending recurrence fields")
        return

    if not frequency:
        raise ValueError("recurrence_frequency is required when is_recurring is true")

    if recurrence_until and recurrence_until <= start_time:
        raise ValueError("recurrence_until must be after start_time")

    if recurrence_by_weekday and frequency != "weekly":
        raise ValueError("recurrence_by_weekday is only valid for weekly recurrence")


def sanitize_meeting_payload(payload: dict[str, Any], is_create: bool) -> dict[str, Any]:
    cleaned = dict(payload)

    if "availability" in cleaned or is_create:
        cleaned["availability"] = normalize_availability(cleaned.get("availability"))

    if "alert_minutes" in cleaned:
        cleaned["alert_minutes"] = normalize_alert_minutes(cleaned["alert_minutes"])
    elif is_create:
        cleaned["alert_minutes"] = [30]

    if "recurrence_frequency" in cleaned:
        cleaned["recurrence_frequency"] = normalize_frequency(cleaned["recurrence_frequency"])

    if "recurrence_by_weekday" in cleaned:
        cleaned["recurrence_by_weekday"] = normalize_weekdays(cleaned["recurrence_by_weekday"])

    return cleaned


def build_google_rrule(meeting) -> str | None:
    if not getattr(meeting, "is_recurring", False):
        return None

    frequency = normalize_frequency(getattr(meeting, "recurrence_frequency", None))
    if not frequency:
        return None

    interval = int(getattr(meeting, "recurrence_interval", 1) or 1)
    parts = [f"FREQ={frequency.upper()}", f"INTERVAL={interval}"]

    weekdays = normalize_weekdays(getattr(meeting, "recurrence_by_weekday", []) or [])
    if frequency == "weekly" and weekdays:
        parts.append(f"BYDAY={','.join(weekdays)}")

    recurrence_count = getattr(meeting, "recurrence_count", None)
    recurrence_until = getattr(meeting, "recurrence_until", None)
    if recurrence_count:
        parts.append(f"COUNT={int(recurrence_count)}")
    elif recurrence_until:
        until_dt = recurrence_until
        if until_dt.tzinfo is None:
            until_dt = until_dt.replace(tzinfo=UTC)
        else:
            until_dt = until_dt.astimezone(UTC)
        parts.append(f"UNTIL={until_dt.strftime('%Y%m%dT%H%M%SZ')}")

    return ";".join(parts)


def _add_months(base: datetime, months: int) -> datetime:
    month = base.month - 1 + months
    year = base.year + month // 12
    month = month % 12 + 1
    day = min(base.day, monthrange(year, month)[1])
    return base.replace(year=year, month=month, day=day)


def _add_years(base: datetime, years: int) -> datetime:
    year = base.year + years
    day = base.day
    if base.month == 2 and base.day == 29 and not monthrange(year, 2)[1] == 29:
        day = 28
    return base.replace(year=year, day=day)


def _iter_weekly_with_weekdays(
    *,
    base_start: datetime,
    interval: int,
    weekdays: list[str],
    recurrence_count: int | None,
    recurrence_until: datetime | None,
):
    week_anchor = base_start - timedelta(days=base_start.weekday())
    emitted = 0
    week_index = 0

    while True:
        current_week_start = week_anchor + timedelta(weeks=week_index * interval)
        for weekday_code in weekdays:
            occurrence_date = current_week_start + timedelta(days=_WEEKDAY_INDEX[weekday_code])
            occurrence_start = occurrence_date.replace(
                hour=base_start.hour,
                minute=base_start.minute,
                second=base_start.second,
                microsecond=base_start.microsecond,
            )

            if occurrence_start < base_start:
                continue

            if recurrence_until and occurrence_start > recurrence_until:
                return

            emitted += 1
            yield emitted, occurrence_start

            if recurrence_count and emitted >= recurrence_count:
                return

        week_index += 1


def iter_recurrence_starts(meeting, hard_limit: int = 1000):
    base_start = meeting.start_time

    if not getattr(meeting, "is_recurring", False):
        yield 1, base_start
        return

    frequency = normalize_frequency(getattr(meeting, "recurrence_frequency", None))
    if not frequency:
        yield 1, base_start
        return

    interval = int(getattr(meeting, "recurrence_interval", 1) or 1)
    recurrence_count = getattr(meeting, "recurrence_count", None)
    recurrence_until = getattr(meeting, "recurrence_until", None)

    weekdays = normalize_weekdays(getattr(meeting, "recurrence_by_weekday", []) or [])
    if frequency == "weekly" and weekdays:
        for emitted, occurrence_start in _iter_weekly_with_weekdays(
            base_start=base_start,
            interval=interval,
            weekdays=weekdays,
            recurrence_count=recurrence_count,
            recurrence_until=recurrence_until,
        ):
            if emitted > hard_limit:
                return
            yield emitted, occurrence_start
        return

    emitted = 0
    current_start = base_start

    while emitted < hard_limit:
        if recurrence_until and current_start > recurrence_until:
            return

        emitted += 1
        yield emitted, current_start

        if recurrence_count and emitted >= recurrence_count:
            return

        if frequency == "daily":
            current_start = current_start + timedelta(days=interval)
        elif frequency == "weekly":
            current_start = current_start + timedelta(weeks=interval)
        elif frequency == "monthly":
            current_start = _add_months(current_start, interval)
        elif frequency == "yearly":
            current_start = _add_years(current_start, interval)


def list_meeting_occurrences(
    meeting,
    *,
    range_start: datetime,
    range_end: datetime,
    limit: int = 200,
) -> list[dict[str, Any]]:
    if range_end <= range_start:
        raise ValueError("range_end must be after range_start")

    duration = meeting.end_time - meeting.start_time
    if duration.total_seconds() <= 0:
        return []

    results: list[dict[str, Any]] = []

    for occurrence_index, start_at in iter_recurrence_starts(meeting, hard_limit=5000):
        end_at = start_at + duration

        overlaps = end_at > range_start and start_at < range_end
        if overlaps:
            results.append(
                {
                    "meeting_id": meeting.id,
                    "occurrence_index": occurrence_index,
                    "title": meeting.title,
                    "start_time": start_at,
                    "end_time": end_at,
                    "availability": getattr(meeting, "availability", "busy"),
                }
            )
            if len(results) >= limit:
                break

        if start_at >= range_end and getattr(meeting, "is_recurring", False):
            break

    return results
