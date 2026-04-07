from datetime import datetime, timezone
from typing import Any


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


async def get_recent_notifications(db: Any, limit: int = 10) -> list[dict]:
    cursor = db["notifications"].find().sort("created_at", -1).limit(limit)
    return await cursor.to_list(length=limit)
