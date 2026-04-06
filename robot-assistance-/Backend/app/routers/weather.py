import os

from fastapi import APIRouter, HTTPException, Query, status

from app.services.weather_service import get_current_weather, is_weather_enabled

router = APIRouter(tags=["Weather"])


@router.get("/weather/status")
def weather_status():
    provider = os.getenv("WEATHER_PROVIDER", "openweather").strip().lower() or "openweather"
    geocoding_provider = os.getenv("GEOCODING_PROVIDER", "").strip().lower() or None
    return {
        "enabled": is_weather_enabled(),
        "provider": provider,
        "geocoding_provider": geocoding_provider,
        "message": "Weather API key is configured" if is_weather_enabled() else "Weather API key is not configured yet",
    }


@router.get("/weather/current")
async def weather_current(city: str = Query(..., min_length=2), units: str = Query("metric")):
    try:
        result = await get_current_weather(city=city, units=units)
        return result
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
