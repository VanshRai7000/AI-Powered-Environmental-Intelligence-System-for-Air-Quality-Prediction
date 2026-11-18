import logging
import httpx

from app.config.settings import settings

logger = logging.getLogger(__name__)


WAQI_BASE_URL = "https://api.waqi.info"

# Pollutants WAQI may return
KNOWN_POLLUTANTS = {"pm25", "pm10", "no2", "o3", "co", "so2"}


async def get_waqi_air_quality(latitude: float, longitude: float) -> dict | None:
    """
    Fetch AQI and pollutant readings from WAQI for a geo coordinate.
    Returns a normalised dict or None if no station is found nearby.
    """
    url = f"{WAQI_BASE_URL}/feed/geo:{latitude};{longitude}/"

    params = {"token": settings.waqi_api_token}

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        body = response.json()

    # WAQI wraps everything under {"status": "ok", "data": {...}}
    if body.get("status") != "ok":
        logger.warning("WAQI returned non-ok status: %s (msg: %s)", body.get("status"), body.get("data"))
        return None

    data = body.get("data")

    if not data or data == "Unknown station":
        logger.warning("WAQI returned no data or Unknown station for (%s, %s)", latitude, longitude)
        return None

    aqi = _parse_aqi(data.get("aqi"))
    pollutants = _extract_pollutants(data.get("iaqi", {}))
    station_name = _extract_station_name(data)
    timestamp = _extract_timestamp(data)

    return {
        "aqi": aqi,
        "pollutants": pollutants,
        "station_name": station_name,
        "timestamp": timestamp,
        "source": "WAQI",
    }


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _parse_aqi(raw) -> float | None:
    """Parse AQI; WAQI sometimes returns '-' for missing data."""
    try:
        value = float(raw)
        return value if value >= 0 else None
    except (TypeError, ValueError):
        return None


def _extract_pollutants(iaqi: dict) -> list[dict]:
    """
    iaqi looks like: { "pm25": {"v": 42.0}, "pm10": {"v": 60}, ... }
    We only extract known pollutants and skip missing / negative values.
    """
    readings = []

    pollutant_meta = {
        "pm25": ("PM2.5", "µg/m³"),
        "pm10": ("PM10",  "µg/m³"),
        "no2":  ("NO2",   "ppb"),
        "o3":   ("O3",    "ppb"),
        "co":   ("CO",    "ppm"),
        "so2":  ("SO2",   "ppb"),
    }

    for key, (label, unit) in pollutant_meta.items():
        if key not in iaqi:
            continue

        raw_value = iaqi[key].get("v")

        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            continue

        if value < 0:
            continue

        readings.append({
            "pollutant": label,
            "value": value,
            "unit": unit,
        })

    return readings


def _extract_station_name(data: dict) -> str | None:
    city = data.get("city", {})
    if isinstance(city, dict):
        return city.get("name") or None
    return None


def _extract_timestamp(data: dict) -> str | None:
    time_block = data.get("time", {})
    if isinstance(time_block, dict):
        return time_block.get("iso") or time_block.get("s") or None
    return None


async def get_waqi_stations_in_bounds(
    latitude: float,
    longitude: float,
    delta: float = 0.6,
) -> list[dict]:
    """
    Fetch nearby monitoring stations within a bounding box from WAQI map/bounds.
    """
    token = settings.waqi_api_token.strip()
    if not token:
        return []

    latlng = f"{latitude - delta},{longitude - delta},{latitude + delta},{longitude + delta}"
    url = f"{WAQI_BASE_URL}/map/bounds/"

    try:
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.get(url, params={"latlng": latlng, "token": token})
            if response.status_code != 200:
                return []
            body = response.json()
    except Exception as exc:
        logger.warning("WAQI map bounds fetch failed: %s", exc)
        return []

    if body.get("status") != "ok":
        return []

    stations = []
    for item in body.get("data", []):
        st_info = item.get("station", {})
        aqi_val = _parse_aqi(item.get("aqi"))
        stations.append({
            "id": str(item.get("uid")),
            "name": st_info.get("name") or "WAQI Station",
            "latitude": item.get("lat"),
            "longitude": item.get("lon"),
            "aqi": aqi_val,
            "last_updated": st_info.get("time"),
            "source": "WAQI",
        })
    return stations

