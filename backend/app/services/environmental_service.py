import logging
from datetime import datetime, timezone

from app.services.geo_service import resolve_location
from app.services.air_quality_service import (
    get_current_air_quality
)
from app.services.weather_service import (
    get_current_weather
)
from app.services.traffic_service import (
    get_traffic_data,
    normalize_traffic
)
from app.services.data_cleaning_service import (
    validate_coordinates
)

logger = logging.getLogger(__name__)


async def collect_environmental_data(
    location: str | float | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
):
    """
    Collect comprehensive environmental data (Air Quality, Weather, Traffic).
    Accepts either a human-readable location name (e.g. 'Delhi', 'Indirapuram')
    OR direct coordinates. Resolves and tags data with the location name.
    """
    if isinstance(location, (int, float)):
        longitude = latitude
        latitude = float(location)
        location = None
    lat, lon, resolved_name = await resolve_location(
        location=location,
        latitude=latitude,
        longitude=longitude,
    )

    # Validate coordinate boundaries (-90..90, -180..180)
    validate_coordinates(lat, lon)

    air_quality = None
    weather = None
    traffic = None

    # -------------------------
    # Air Quality
    # -------------------------
    try:
        air_quality = await get_current_air_quality(lat, lon)
        if air_quality:
            air_quality["latitude"] = lat
            air_quality["longitude"] = lon
            if resolved_name:
                air_quality["station_name"] = resolved_name
    except Exception as error:
        logger.warning("Air quality service unavailable: %s", error)

    # -------------------------
    # Weather
    # -------------------------
    try:
        weather = await get_current_weather(lat, lon)
        if weather:
            weather["latitude"] = lat
            weather["longitude"] = lon
            weather.setdefault("source", "OpenWeatherMap")
            if resolved_name:
                weather["station_name"] = resolved_name
                weather["location_name"] = resolved_name
    except Exception as error:
        logger.warning("Weather service unavailable: %s", error)

    # -------------------------
    # Traffic
    # -------------------------
    try:
        raw_traffic = await get_traffic_data(lat, lon)
        if raw_traffic:
            traffic = normalize_traffic(raw_traffic)
    except Exception as error:
        logger.warning("Traffic service unavailable: %s", error)

    return {
        "location": {
            "name": resolved_name,
            "latitude": lat,
            "longitude": lon,
        },
        "air_quality": air_quality,
        "weather": weather,
        "traffic": traffic,
        "collected_at": datetime.now(timezone.utc).isoformat(),
    }
