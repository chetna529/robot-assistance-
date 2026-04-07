from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import DESCENDING

from app.database import get_db, get_next_sequence
from app.services.activity_log_service import log_activity
from app.schemas.poc import POCNotification
from app.schemas.notification import Notification as NotificationSchema
from app.schemas.notification import NotificationCreate, NotificationUpdate

router = APIRouter(tags=["Notifications"])


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _strip_mongo_id(document: dict | None) -> dict | None:
    if document is None:
        return None
    return {key: value for key, value in document.items() if key != "_id"}


def _notification_defaults(document: dict) -> dict:
    data = _strip_mongo_id(document) or {}
    data.setdefault("channel", "email")
    data.setdefault("delivered", False)
    data.setdefault("created_at", _now_utc())
    return data


def _notification_poc_payload(document: dict) -> dict:
    data = _notification_defaults(document)
    status = data.get("status") or ("sent" if data.get("delivered") else "pending")
    notification_type = data.get("notification_type") or data.get("channel") or "info"
    return {
        "id": data["id"],
        "message": data.get("message") or data.get("content") or "Notification",
        "type": notification_type,
        "status": status,
    }


async def _get_notification_or_404(db: AsyncIOMotorDatabase, notification_id: int) -> dict:
    notification = await db["notifications"].find_one({"id": notification_id})
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return _notification_defaults(notification)


@router.get("/notifications", response_model=list[POCNotification])
async def get_all_notifications(db: AsyncIOMotorDatabase = Depends(get_db)):
    docs = await db["notifications"].find().sort("created_at", DESCENDING).to_list(length=5000)
    return [POCNotification.model_validate(_notification_poc_payload(doc)) for doc in docs]


@router.get("/meetings/{meeting_id}/notifications", response_model=list[POCNotification])
async def get_meeting_notifications(meeting_id: int, db: AsyncIOMotorDatabase = Depends(get_db)):
    docs = await db["notifications"].find({"meeting_id": meeting_id}).sort("created_at", DESCENDING).to_list(length=2000)
    return [POCNotification.model_validate(_notification_poc_payload(doc)) for doc in docs]


@router.post("/notifications", response_model=POCNotification, status_code=status.HTTP_201_CREATED)
async def create_notification(notification: NotificationCreate, db: AsyncIOMotorDatabase = Depends(get_db)):
    meeting_exists = await db["meetings"].find_one({"id": notification.meeting_id}, {"id": 1})
    if not meeting_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")

    notification_id = await get_next_sequence(db, "notifications")
    now = _now_utc()
    payload = notification.model_dump()
    notification_doc = {
        "id": notification_id,
        **payload,
        "created_at": now,
        "title": (payload.get("content") or "Notification")[:255] or "Notification",
        "message": payload.get("content", ""),
        "notification_type": "info",
        "metadata_info": {},
    }

    await db["notifications"].insert_one(notification_doc)
    try:
        await log_activity(
            db,
            action="notification_created",
            entity_type="notification",
            entity_id=notification_id,
            performed_by="robot",
            details={"meeting_id": notification.meeting_id, "recipient": notification.recipient},
        )
    except Exception:  # noqa: BLE001
        pass
    return POCNotification.model_validate(_notification_poc_payload(notification_doc))


@router.put("/notifications/{notification_id}", response_model=POCNotification)
async def update_notification(
    notification_id: int,
    update: NotificationUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    notification_doc = await _get_notification_or_404(db, notification_id)
    update_data = update.model_dump(exclude_unset=True)

    if "content" in update_data:
        update_data["message"] = update_data["content"]
        update_data["title"] = (update_data["content"] or "Notification")[:255]

    notification_doc.update(update_data)
    await db["notifications"].update_one({"id": notification_id}, {"$set": update_data})
    try:
        await log_activity(
            db,
            action="notification_updated",
            entity_type="notification",
            entity_id=notification_id,
            performed_by="robot",
            details={"meeting_id": notification_doc.get("meeting_id"), "recipient": notification_doc.get("recipient")},
        )
    except Exception:  # noqa: BLE001
        pass
    return POCNotification.model_validate(_notification_poc_payload(notification_doc))


@router.delete("/notifications/{notification_id}")
async def delete_notification(notification_id: int, db: AsyncIOMotorDatabase = Depends(get_db)):
    await _get_notification_or_404(db, notification_id)
    await db["notifications"].delete_one({"id": notification_id})
    try:
        await log_activity(
            db,
            action="notification_deleted",
            entity_type="notification",
            entity_id=notification_id,
            performed_by="robot",
            details={"notification_id": notification_id},
        )
    except Exception:  # noqa: BLE001
        pass
    return {"status": "deleted", "id": notification_id}
