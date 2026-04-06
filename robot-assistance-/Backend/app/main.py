from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import initialize_database
from app.routers import auth, info, meetings, notifications, reminders, weather

app = FastAPI(title="Humoind Robot Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup() -> None:
    await initialize_database()


app.include_router(meetings.router, prefix="/api")
app.include_router(reminders.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")
app.include_router(weather.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(info.router, prefix="/api")


@app.get("/")
def root():
    return {"message": "Humoind Robot API is running"}
