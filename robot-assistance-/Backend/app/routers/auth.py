from fastapi import APIRouter, HTTPException, Query, status

from app.services.google_calendar_service import (
    exchange_google_auth_code,
    get_google_auth_url,
    is_google_calendar_authorized,
    is_google_calendar_enabled,
)

router = APIRouter(tags=["Google Auth"])


@router.get("/auth/google/status")
def google_auth_status():
    return {
        "enabled": is_google_calendar_enabled(),
        "authorized": is_google_calendar_authorized(),
    }


@router.get("/auth/google/url")
def google_auth_url():
    try:
        return {"auth_url": get_google_auth_url()}
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/auth/google/callback")
async def google_auth_callback(code: str = Query(...), state: str | None = Query(None)):
    _ = state
    try:
        result = await exchange_google_auth_code(code)
        return {"status": "authorized", **result}
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
