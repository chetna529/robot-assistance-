import logging
import os
from typing import AsyncGenerator

from dotenv import load_dotenv
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING, ReturnDocument

load_dotenv()
logger = logging.getLogger(__name__)

MONGODB_URI = os.getenv("MONGODB_URI", "").strip()
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "").strip() or "humoid"
MONGODB_TIMEOUT_MS = int(os.getenv("MONGODB_TIMEOUT_MS", "5000"))

_client: AsyncIOMotorClient | None = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if not is_mongodb_configured():
        raise RuntimeError("MongoDB Atlas is not configured. Set MONGODB_URI in Backend/.env.")

    if _client is None:
        _client = AsyncIOMotorClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=MONGODB_TIMEOUT_MS,
            connectTimeoutMS=MONGODB_TIMEOUT_MS,
        )
    return _client


def get_database() -> AsyncIOMotorDatabase:
    return get_client()[MONGODB_DB_NAME]


async def get_db() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    if not is_mongodb_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB Atlas is not configured yet. Set MONGODB_URI in Backend/.env.",
        )
    yield get_database()


def is_mongodb_configured() -> bool:
    return bool(os.getenv("MONGODB_URI", "").strip())


async def ping_database() -> bool:
    if not is_mongodb_configured():
        return False

    try:
        await get_client().admin.command("ping")
        return True
    except Exception:  # noqa: BLE001
        return False


async def initialize_database() -> None:
    if not is_mongodb_configured():
        logger.info("Skipping MongoDB init because MONGODB_URI is not set.")
        return

    db = get_database()
    try:
        await db["users"].create_index([("id", ASCENDING)], unique=True)
        await db["users"].create_index([("email", ASCENDING)], unique=True, sparse=True)

        await db["meetings"].create_index([("id", ASCENDING)], unique=True)
        await db["meetings"].create_index([("start_time", ASCENDING)])
        await db["meetings"].create_index([("user_id", ASCENDING)])

        await db["reminders"].create_index([("id", ASCENDING)], unique=True)
        await db["reminders"].create_index([("meeting_id", ASCENDING)])
        await db["reminders"].create_index([("remind_at", ASCENDING)])

        await db["notifications"].create_index([("id", ASCENDING)], unique=True)
        await db["notifications"].create_index([("meeting_id", ASCENDING)])
        await db["notifications"].create_index([("created_at", DESCENDING)])

        await db["activity_logs"].create_index([("created_at", DESCENDING)])
        await db["info_service_logs"].create_index([("created_at", DESCENDING)])
    except Exception as exc:  # noqa: BLE001
        logger.warning("MongoDB index initialization skipped: %s", exc)


async def get_next_sequence(db: AsyncIOMotorDatabase, sequence_name: str) -> int:
    doc = await db["counters"].find_one_and_update(
        {"_id": sequence_name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return int(doc["seq"])
