import os
from typing import Any

import httpx


def is_weather_enabled() -> bool:
    return bool(os.getenv("WEATHER_API_KEY", "").strip())


def _weather_provider() -> str:
    provider = os.getenv("WEATHER_PROVIDER", "openweather").strip().lower()
    return provider or "openweather"


def _extract_number(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, dict):
        for key in ("value", "degrees", "magnitude"):
            item = value.get(key)
            if isinstance(item, (int, float)):
                return float(item)
    return None


async def _get_openweather_weather(city: str, units: str, api_key: str) -> dict:
    base_url = os.getenv("WEATHER_BASE_URL", "https://api.openweathermap.org/data/2.5").rstrip("/")
    url = f"{base_url}/weather"
    params: dict[str, Any] = {"q": city, "appid": api_key, "units": units}

    geocode_provider = os.getenv("GEOCODING_PROVIDER", "").strip().lower()
    geocoding_key = os.getenv("GEOCODING_API_KEY", "").strip()
    if geocode_provider == "opencage" and geocoding_key:
        geocode_url = os.getenv("OPENCAGE_GEOCODE_URL", "https://api.opencagedata.com/geocode/v1/json")
        async with httpx.AsyncClient(timeout=15.0) as client:
            geocode_response = await client.get(
                geocode_url,
                params={
                    "q": city,
                    "key": geocoding_key,
                    "limit": 1,
                    "no_annotations": 1,
                },
            )

        if geocode_response.status_code != 200:
            raise RuntimeError("OpenCage geocoding request failed")

        geocode_payload = geocode_response.json()
        results = geocode_payload.get("results", [])
        if not results:
            message = geocode_payload.get("status", {}).get("message", "No geocoding result found")
            raise RuntimeError(f"OpenCage geocoding error: {message}")

        geometry = results[0].get("geometry", {})
        latitude = geometry.get("lat")
        longitude = geometry.get("lng")
        if latitude is None or longitude is None:
            raise RuntimeError("OpenCage geocoding did not return coordinates")

        params = {"lat": latitude, "lon": longitude, "appid": api_key, "units": units}

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(url, params=params)

    if response.status_code != 200:
        message = response.json().get("message", "Weather API request failed") if response.text else "Weather API request failed"
        raise RuntimeError(message)

    payload = response.json()
    main = payload.get("main", {})
    weather_items = payload.get("weather", [])
    weather = weather_items[0] if weather_items else {}
    wind = payload.get("wind", {})

    return {
        "provider": "openweather",
        "enabled": True,
        "city": payload.get("name", city),
        "country": payload.get("sys", {}).get("country"),
        "temperature": main.get("temp"),
        "feels_like": main.get("feels_like"),
        "humidity": main.get("humidity"),
        "condition": weather.get("main"),
        "description": weather.get("description"),
        "wind_speed": wind.get("speed"),
        "raw": payload,
    }


async def _get_google_weather(city: str, units: str, api_key: str) -> dict:
    geocode_url = os.getenv("GOOGLE_GEOCODE_URL", "https://maps.googleapis.com/maps/api/geocode/json")
    weather_url = os.getenv("GOOGLE_WEATHER_URL", "https://weather.googleapis.com/v1/currentConditions:lookup")
    units_system = "IMPERIAL" if units.lower() == "imperial" else "METRIC"

    async with httpx.AsyncClient(timeout=20.0) as client:
        geocode_response = await client.get(
            geocode_url,
            params={"address": city, "key": api_key},
        )

        if geocode_response.status_code != 200:
            raise RuntimeError("Google geocoding request failed")

        geocode_payload = geocode_response.json()
        geocode_status = geocode_payload.get("status")
        if geocode_status != "OK":
            message = geocode_payload.get("error_message") or geocode_status or "Geocoding failed"
            raise RuntimeError(f"Google geocoding error: {message}")

        first_result = geocode_payload.get("results", [])[0]
        location = first_result.get("geometry", {}).get("location", {})
        latitude = location.get("lat")
        longitude = location.get("lng")
        if latitude is None or longitude is None:
            raise RuntimeError("Google geocoding did not return coordinates")

        weather_response = await client.get(
            weather_url,
            params={
                "key": api_key,
                "location.latitude": latitude,
                "location.longitude": longitude,
                "unitsSystem": units_system,
            },
        )

    if weather_response.status_code != 200:
        message = "Google Weather API request failed"
        if weather_response.text:
            try:
                error_payload = weather_response.json()
                message = error_payload.get("error", {}).get("message", message)
            except Exception:  # noqa: BLE001
                message = weather_response.text
        raise RuntimeError(message)

    payload = weather_response.json()
    current = payload.get("currentConditions", payload)
    condition = current.get("weatherCondition", {})
    condition_text = condition.get("description", {}).get("text") or condition.get("type")

    temperature = _extract_number(current.get("temperature")) or _extract_number(payload.get("temperature"))
    feels_like = _extract_number(current.get("feelsLikeTemperature")) or _extract_number(payload.get("feelsLikeTemperature"))
    humidity = _extract_number(current.get("relativeHumidity")) or _extract_number(payload.get("relativeHumidity"))
    wind_speed = _extract_number((current.get("wind") or {}).get("speed")) or _extract_number(
        ((payload.get("wind") or {}).get("speed"))
    )
    timestamp = current.get("currentTime") or payload.get("currentTime")

    return {
        "provider": "google",
        "enabled": True,
        "city": city,
        "country": None,
        "temperature": temperature,
        "feels_like": feels_like,
        "humidity": humidity,
        "condition": condition.get("type"),
        "description": condition_text,
        "wind_speed": wind_speed,
        "timestamp": timestamp,
        "raw": payload,
    }


async def get_current_weather(city: str, units: str = "metric") -> dict:
    api_key = os.getenv("WEATHER_API_KEY", "").strip()
    if not api_key:
        return {
            "enabled": False,
            "message": "Weather API key is not configured yet.",
            "city": city,
            "data": None,
        }

    provider = _weather_provider()
    if provider == "google":
        return await _get_google_weather(city=city, units=units, api_key=api_key)

    return await _get_openweather_weather(city=city, units=units, api_key=api_key)
