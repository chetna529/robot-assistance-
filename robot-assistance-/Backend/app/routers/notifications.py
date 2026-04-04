from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.meeting import Meeting as MeetingModel
from app.models.notification import Notification as NotificationModel
from app.schemas.notification import Notification as NotificationSchema
from app.schemas.notification import NotificationCreate, NotificationUpdate

router = APIRouter(tags=["Notifications"])


@router.get("/notifications", response_model=list[NotificationSchema])
def get_all_notifications(db: Session = Depends(get_db)):
    return db.query(NotificationModel).order_by(NotificationModel.created_at.desc()).all()


@router.get("/meetings/{meeting_id}/notifications", response_model=list[NotificationSchema])
def get_meeting_notifications(meeting_id: int, db: Session = Depends(get_db)):
    return db.query(NotificationModel).filter(NotificationModel.meeting_id == meeting_id).all()


@router.post("/notifications", response_model=NotificationSchema, status_code=status.HTTP_201_CREATED)
def create_notification(notification: NotificationCreate, db: Session = Depends(get_db)):
    meeting_exists = db.query(MeetingModel.id).filter(MeetingModel.id == notification.meeting_id).first()
    if not meeting_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")

    db_notification = NotificationModel(**notification.model_dump())
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification


@router.put("/notifications/{notification_id}", response_model=NotificationSchema)
def update_notification(notification_id: int, update: NotificationUpdate, db: Session = Depends(get_db)):
    db_notification = db.query(NotificationModel).filter(NotificationModel.id == notification_id).first()
    if not db_notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    for key, value in update.model_dump(exclude_unset=True).items():
        setattr(db_notification, key, value)

    db.commit()
    db.refresh(db_notification)
    return db_notification


@router.delete("/notifications/{notification_id}")
def delete_notification(notification_id: int, db: Session = Depends(get_db)):
    db_notification = db.query(NotificationModel).filter(NotificationModel.id == notification_id).first()
    if not db_notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    db.delete(db_notification)
    db.commit()
    return {"status": "deleted", "id": notification_id}
