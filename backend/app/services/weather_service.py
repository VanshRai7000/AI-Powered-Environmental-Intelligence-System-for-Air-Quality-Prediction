import logging
from app.services.openweather_service import get_openweather_weather

logger = logging.getLogger(__name__)


async def get_current_weather(
    latitude: float,
    longitude: float
) -> dict | None:
    """
    Fetch current weather metrics (temperature, humidity, wind, etc.) for coordinates.
    """
    try:
        weather_data = await get_openweather_weather(latitude, longitude)
        return weather_data
    except Exception as exc:
        logger.warning("Weather fetch failed: %s", exc)
        return None

