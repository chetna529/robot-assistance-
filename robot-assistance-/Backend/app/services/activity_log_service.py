from datetime import datetime, timezone
from typing import Any


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


async def log_activity(
    db: Any,
    *,
    action: str,
    entity_type: str | None = None,
    entity_id: int | None = None,
    performed_by: str | None = None,
    details: dict | None = None,
) -> None:
    await db["activity_logs"].insert_one(
        {
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "performed_by": performed_by,
            "details": details or {},
            "created_at": _now_utc(),
        }
    )
