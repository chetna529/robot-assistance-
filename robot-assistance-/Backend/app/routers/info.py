from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter(tags=["Info"])


@router.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get("/info")
def info():
    return {
        "service": "Humoind Robot Backend",
        "version": "1.0.0",
        "docs": "/docs",
        "openapi": "/openapi.json",
    }
