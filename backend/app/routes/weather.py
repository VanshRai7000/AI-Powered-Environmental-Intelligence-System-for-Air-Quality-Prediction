from datetime import datetime, timezone
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from app.schemas.weather import WeatherResponse
from app.services.geo_service import resolve_location
from app.services.openweather_service import get_openweather_weather
from app.database.influxdb import write_environmental_data

router = APIRouter(
    prefix="/api/weather",
    tags=["Weather"],
)


@router.get("/current", response_model=WeatherResponse)
async def current_weather(
    location: str | None = Query(None, description="City or area name (e.g. 'Paonta Sahib', 'Delhi')"),
    latitude: float | None = Query(None, ge=-90, le=90, description="Latitude (optional if location is provided)"),
    longitude: float | None = Query(None, ge=-180, le=180, description="Longitude (optional if location is provided)"),
    background_tasks: BackgroundTasks = None,
):
    """Retrieve real-time temperature, humidity, and wind conditions and store to InfluxDB."""
    if not location and (latitude is None or longitude is None):
        raise HTTPException(
            status_code=400,
            detail="Please provide a location name (e.g. ?location=Paonta Sahib) or latitude & longitude.",
        )

    try:
        lat, lon, resolved_name = await resolve_location(
            location=location,
            latitude=latitude,
            longitude=longitude,
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

    weather = await get_openweather_weather(lat, lon)
    if not weather:
        raise HTTPException(
            status_code=503,
            detail="Weather data unavailable. Please verify OPENWEATHER_API_KEY.",
        )

    loc_name = resolved_name or weather.get("station_name") or f"{lat},{lon}"

    record = {
        "location": {
            "name": loc_name,
            "latitude": lat,
            "longitude": lon,
        },
        "weather": weather,
        "collected_at": datetime.now(timezone.utc).isoformat(),
    }
    if background_tasks:
        background_tasks.add_task(write_environmental_data, record)
    else:
        write_environmental_data(record)

    return WeatherResponse(
        latitude=lat,
        longitude=lon,
        location_name=loc_name,
        temperature=weather.get("temperature"),
        feels_like=weather.get("feels_like"),
        humidity=weather.get("humidity"),
        wind_speed_kmh=weather.get("wind_speed_kmh"),
        description=weather.get("description"),
        icon=weather.get("icon"),
        precipitation=weather.get("precipitation"),
        weather_code=weather.get("weather_code"),
        timestamp=weather.get("timestamp"),
    )
