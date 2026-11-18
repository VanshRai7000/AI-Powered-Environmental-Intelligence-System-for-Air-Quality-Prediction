import logging
from app.services.openweather_service import (
    get_openweather_air_pollution,
    get_openweather_weather,
)
from app.services.waqi_service import get_waqi_air_quality
from app.services.openaq_service import get_openaq_air_quality

logger = logging.getLogger(__name__)


async def get_current_air_quality(
    latitude: float,
    longitude: float
) -> dict | None:
    """
    Fetch current air quality for given coordinates.
    Tries OpenWeatherMap first, falls back to WAQI, then OpenAQ.
    """
    # 1. OpenWeatherMap
    try:
        owm_data = await get_openweather_air_pollution(latitude, longitude)
        if owm_data:
            weather_meta = await get_openweather_weather(latitude, longitude)
            station_name = weather_meta.get("station_name") if weather_meta else None
            return {
                "aqi": owm_data.get("aqi"),
                "pollutants": owm_data.get("pollutants", []),
                "station_name": station_name,
                "timestamp": owm_data.get("timestamp"),
                "source": "OpenWeatherMap",
            }
    except Exception as exc:
        logger.warning("OpenWeather air quality fetch failed: %s", exc)

    # 2. WAQI Fallback
    try:
        waqi_data = await get_waqi_air_quality(latitude, longitude)
        if waqi_data:
            return waqi_data
    except Exception as exc:
        logger.warning("WAQI air quality fetch failed: %s", exc)

    # 3. OpenAQ Fallback
    try:
        openaq_data = await get_openaq_air_quality(latitude, longitude)
        if openaq_data:
            return openaq_data
    except Exception as exc:
        logger.warning("OpenAQ air quality fetch failed: %s", exc)

    return None

