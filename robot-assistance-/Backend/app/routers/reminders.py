from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.meeting import Meeting as MeetingModel
from app.models.reminder import Reminder as ReminderModel
from app.schemas.reminder import Reminder as ReminderSchema
from app.schemas.reminder import ReminderCreate, ReminderUpdate

router = APIRouter(tags=["Reminders"])


@router.get("/reminders", response_model=list[ReminderSchema])
def get_all_reminders(db: Session = Depends(get_db)):
    return db.query(ReminderModel).order_by(ReminderModel.remind_at.asc()).all()


@router.get("/meetings/{meeting_id}/reminders", response_model=list[ReminderSchema])
def get_meeting_reminders(meeting_id: int, db: Session = Depends(get_db)):
    return db.query(ReminderModel).filter(ReminderModel.meeting_id == meeting_id).all()


@router.post("/reminders", response_model=ReminderSchema, status_code=status.HTTP_201_CREATED)
def create_reminder(reminder: ReminderCreate, db: Session = Depends(get_db)):
    meeting_exists = db.query(MeetingModel.id).filter(MeetingModel.id == reminder.meeting_id).first()
    if not meeting_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")

    db_reminder = ReminderModel(**reminder.model_dump())
    db.add(db_reminder)
    db.commit()
    db.refresh(db_reminder)
    return db_reminder


@router.put("/reminders/{reminder_id}", response_model=ReminderSchema)
def update_reminder(reminder_id: int, update: ReminderUpdate, db: Session = Depends(get_db)):
    db_reminder = db.query(ReminderModel).filter(ReminderModel.id == reminder_id).first()
    if not db_reminder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found")

    for key, value in update.model_dump(exclude_unset=True).items():
        setattr(db_reminder, key, value)

    db.commit()
    db.refresh(db_reminder)
    return db_reminder


@router.delete("/reminders/{reminder_id}")
def delete_reminder(reminder_id: int, db: Session = Depends(get_db)):
    db_reminder = db.query(ReminderModel).filter(ReminderModel.id == reminder_id).first()
    if not db_reminder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found")

    db.delete(db_reminder)
    db.commit()
    return {"status": "deleted", "id": reminder_id}
