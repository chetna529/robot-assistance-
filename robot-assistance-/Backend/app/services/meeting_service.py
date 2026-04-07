from datetime import datetime, timedelta, timezone
from typing import Any


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


async def get_upcoming_meetings(db: Any, limit: int = 10, within_hours: int = 24) -> list[dict]:
    now = _now_utc()
    upper_bound = now + timedelta(hours=within_hours)
    cursor = db["meetings"].find({"start_time": {"$gte": now, "$lte": upper_bound}}).sort("start_time", 1).limit(limit)
    return await cursor.to_list(length=limit)


async def get_today_meetings(db: Any, limit: int = 10) -> list[dict]:
    today_start = datetime.combine(_now_utc().date(), datetime.min.time(), tzinfo=timezone.utc)
    tomorrow_start = today_start + timedelta(days=1)
    cursor = db["meetings"].find({"start_time": {"$gte": today_start, "$lt": tomorrow_start}}).sort("start_time", 1).limit(limit)
    return await cursor.to_list(length=limit)
