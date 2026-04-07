from datetime import datetime, timedelta, timezone
from typing import Any


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


async def get_pending_reminders(db: Any, limit: int = 10) -> list[dict]:
    now = _now_utc()
    cursor = db["reminders"].find(
        {"$or": [{"is_sent": False}, {"status": {"$in": [None, "pending"]}}], "remind_at": {"$lte": now}}
    ).sort("remind_at", 1).limit(limit)
    return await cursor.to_list(length=limit)


async def get_upcoming_reminders(db: Any, limit: int = 10, within_minutes: int = 60) -> list[dict]:
    now = _now_utc()
    upper_bound = now + timedelta(minutes=within_minutes)
    # Keep the query simple and robust for POC: return reminders that are pending or due soon.
    cursor = db["reminders"].find(
        {
            "$or": [{"is_sent": False}, {"status": {"$in": [None, "pending"]}}],
            "remind_at": {"$gte": now, "$lte": upper_bound},
        }
    ).sort("remind_at", 1).limit(limit)
    items = await cursor.to_list(length=limit)
    return items
