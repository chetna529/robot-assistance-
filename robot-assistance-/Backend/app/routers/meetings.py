import logging
from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.meeting import Meeting as MeetingModel
from app.schemas.meeting import Meeting as MeetingSchema
from app.schemas.meeting import MeetingCreate, MeetingUpdate
from app.services.google_calendar_service import create_or_update_event, delete_event

router = APIRouter(tags=["Meetings"])
logger = logging.getLogger(__name__)


async def _sync_meeting_to_google(db: Session, db_meeting: MeetingModel) -> None:
    try:
        result = await create_or_update_event(db_meeting)
        if isinstance(result, dict) and result.get("event_id"):
            db_meeting.google_event_id = result["event_id"]
            db.commit()
            db.refresh(db_meeting)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Google Calendar sync failed for meeting %s: %s", db_meeting.id, exc)


@router.get("/meetings", response_model=list[MeetingSchema])
def get_all_meetings(db: Session = Depends(get_db)):
    return db.query(MeetingModel).order_by(MeetingModel.start_time.asc()).all()


@router.get("/meetings/{meeting_id}", response_model=MeetingSchema)
def get_meeting(meeting_id: int, db: Session = Depends(get_db)):
    db_meeting = db.query(MeetingModel).filter(MeetingModel.id == meeting_id).first()
    if not db_meeting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
    return db_meeting


@router.get("/meetings/today", response_model=list[MeetingSchema])
def get_today_meetings(db: Session = Depends(get_db)):
    today_start = datetime.combine(date.today(), time.min)
    tomorrow_start = today_start + timedelta(days=1)

    return (
        db.query(MeetingModel)
        .filter(MeetingModel.start_time >= today_start, MeetingModel.start_time < tomorrow_start)
        .order_by(MeetingModel.start_time.asc())
        .all()
    )


@router.post("/meetings", response_model=MeetingSchema, status_code=status.HTTP_201_CREATED)
async def create_meeting(meeting: MeetingCreate, db: Session = Depends(get_db)):
    if meeting.end_time <= meeting.start_time:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="end_time must be after start_time")

    db_meeting = MeetingModel(**meeting.model_dump())
    db.add(db_meeting)
    db.commit()
    db.refresh(db_meeting)

    await _sync_meeting_to_google(db, db_meeting)
    return db_meeting


@router.put("/meetings/{meeting_id}", response_model=MeetingSchema)
async def update_meeting(meeting_id: int, update: MeetingUpdate, db: Session = Depends(get_db)):
    db_meeting = db.query(MeetingModel).filter(MeetingModel.id == meeting_id).first()
    if not db_meeting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")

    update_data = update.model_dump(exclude_unset=True)
    merged_start = update_data.get("start_time", db_meeting.start_time)
    merged_end = update_data.get("end_time", db_meeting.end_time)
    if merged_end <= merged_start:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="end_time must be after start_time")

    for key, value in update_data.items():
        setattr(db_meeting, key, value)

    db.commit()
    db.refresh(db_meeting)

    await _sync_meeting_to_google(db, db_meeting)
    return db_meeting


@router.delete("/meetings/{meeting_id}")
async def delete_meeting(meeting_id: int, db: Session = Depends(get_db)):
    db_meeting = db.query(MeetingModel).filter(MeetingModel.id == meeting_id).first()
    if not db_meeting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")

    if db_meeting.google_event_id:
        try:
            await delete_event(db_meeting.google_event_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Google event delete failed for meeting %s: %s", db_meeting.id, exc)

    db.delete(db_meeting)
    db.commit()
    return {"status": "deleted", "id": meeting_id}
