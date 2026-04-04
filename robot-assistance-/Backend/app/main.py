from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401
from app.database import Base, engine
from app.routers import info, meetings, notifications, reminders

app = FastAPI(title="Humoind Robot Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


app.include_router(meetings.router, prefix="/api")
app.include_router(reminders.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")
app.include_router(info.router, prefix="/api")


@app.get("/")
def root():
    return {"message": "Humoind Robot API is running"}
