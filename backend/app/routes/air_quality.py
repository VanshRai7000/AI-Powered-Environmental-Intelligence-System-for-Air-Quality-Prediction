import logging
from datetime import datetime, timezone
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from app.schemas.air_quality import AirQualityResponse, PollutantReading
from app.services.geo_service import resolve_location
from app.services.openweather_service import (
    get_openweather_air_pollution,
    get_openweather_weather,
)
from app.services.waqi_service import (
    get_waqi_air_quality,
    get_waqi_stations_in_bounds,
)
from app.services.openaq_service import get_nearby_locations
from app.database.influxdb import write_environmental_data

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/air-quality",
    tags=["Air Quality"],
)


def _save_aq_to_influx(
    background_tasks: BackgroundTasks | None,
    location_name: str,
    lat: float,
    lon: float,
    aq_payload: dict,
):
    record = {
        "location": {
            "name": location_name,
            "latitude": lat,
            "longitude": lon,
        },
        "air_quality": aq_payload,
        "collected_at": datetime.now(timezone.utc).isoformat(),
    }
    if background_tasks:
        background_tasks.add_task(write_environmental_data, record)
    else:
        write_environmental_data(record)


@router.get("/current", response_model=AirQualityResponse)
async def current_air_quality(
    location: str | None = Query(None, description="City, neighborhood, or area name (e.g. 'Paonta Sahib', 'Delhi')"),
    latitude: float | None = Query(None, ge=-90, le=90, description="Latitude (optional if location name is given)"),
    longitude: float | None = Query(None, ge=-180, le=180, description="Longitude (optional if location name is given)"),
    background_tasks: BackgroundTasks = None,
):
    """
    Retrieve air quality by location name or coordinates, and store into InfluxDB.
    Primary: OpenWeatherMap (exact GPS coordinates worldwide, all 8 pollutants + city name).
    Fallback: WAQI (if OpenWeatherMap key is missing or fails).
    """
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

    # 1. Try OpenWeatherMap
    try:
        owm_pollution = await get_openweather_air_pollution(lat, lon)
        if owm_pollution:
            weather_meta = await get_openweather_weather(lat, lon)
            station_name = resolved_name or (weather_meta.get("station_name") if weather_meta else None)

            _save_aq_to_influx(
                background_tasks,
                station_name or f"{lat},{lon}",
                lat,
                lon,
                owm_pollution,
            )

            return AirQualityResponse(
                latitude=lat,
                longitude=lon,
                aqi=owm_pollution.get("aqi"),
                pollutants=[PollutantReading(**p) for p in owm_pollution.get("pollutants", [])],
                station_name=station_name,
                timestamp=owm_pollution.get("timestamp"),
                source="OpenWeatherMap",
            )
    except Exception as exc:
        logger.warning("OpenWeatherMap fetch failed for (%s, %s): %s", lat, lon, exc)

    # 2. Fallback to WAQI if OpenWeatherMap is not configured or failed
    try:
        waqi_data = await get_waqi_air_quality(lat, lon)
        if waqi_data:
            station_name = resolved_name or waqi_data.get("station_name")
            _save_aq_to_influx(
                background_tasks,
                station_name or f"{lat},{lon}",
                lat,
                lon,
                waqi_data,
            )

            return AirQualityResponse(
                latitude=lat,
                longitude=lon,
                aqi=waqi_data.get("aqi"),
                pollutants=[PollutantReading(**p) for p in waqi_data.get("pollutants", [])],
                station_name=station_name,
                timestamp=waqi_data.get("timestamp"),
                source="WAQI (Fallback)",
            )
    except Exception as exc:
        logger.warning("WAQI fallback failed for (%s, %s): %s", lat, lon, exc)

    raise HTTPException(
        status_code=503,
        detail="No air quality data available. Please verify your OPENWEATHER_API_KEY in backend/.env.",
    )


@router.get("/stations")
async def nearby_monitoring_stations(
    location: str | None = Query(None, description="City or locality name"),
    latitude: float | None = Query(None, ge=-90, le=90),
    longitude: float | None = Query(None, ge=-180, le=180),
):
    """
    Return nearby air quality monitoring stations for the interactive pollution map.
    Combines WAQI regional stations and OpenAQ locations.
    """
    if not location and (latitude is None or longitude is None):
        raise HTTPException(
            status_code=400,
            detail="Please provide a location name or latitude & longitude.",
        )

    try:
        lat, lon, resolved_name = await resolve_location(
            location=location,
            latitude=latitude,
            longitude=longitude,
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

    stations: list[dict] = []

    # 1. WAQI regional map stations (includes live AQI)
    waqi_stations = await get_waqi_stations_in_bounds(lat, lon, delta=0.6)
    stations.extend(waqi_stations)

    # 2. OpenAQ ground stations within 25 km
    try:
        openaq_raw = await get_nearby_locations(lat, lon, radius=25000)
        for item in openaq_raw.get("results", []):
            coords = item.get("coordinates") or {}
            if coords.get("latitude") is None or coords.get("longitude") is None:
                continue
            dt_last = item.get("datetimeLast") or {}
            last_ts = dt_last.get("local") or dt_last.get("utc") if isinstance(dt_last, dict) else None
            sensors = [
                s.get("parameter", {}).get("displayName") or s.get("parameter", {}).get("name")
                for s in item.get("sensors", [])
                if s.get("parameter")
            ]
            stations.append({
                "id": f"openaq-{item.get('id')}",
                "name": item.get("name") or item.get("locality") or "OpenAQ Station",
                "latitude": coords.get("latitude"),
                "longitude": coords.get("longitude"),
                "aqi": None,
                "parameters": [p for p in sensors if p],
                "last_updated": last_ts,
                "source": "OpenAQ",
            })
    except Exception as exc:
        logger.debug("OpenAQ nearby stations skipped: %s", exc)

    return {
        "center": {
            "name": resolved_name,
            "latitude": lat,
            "longitude": lon,
        },
        "count": len(stations),
        "stations": stations,
    }
