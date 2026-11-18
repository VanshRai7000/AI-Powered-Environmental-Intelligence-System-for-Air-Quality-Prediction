import httpx

from app.config.settings import settings
from app.services.pollutant_service import normalize_pollutants, validate_timestamp


OPENAQ_BASE_URL = "https://api.openaq.org/v3"

# Map OpenAQ parameter names → human-readable labels
PARAMETER_LABEL: dict[str, str] = {
    "pm25": "PM2.5",
    "pm10": "PM10",
    "no2":  "NO2",
    "o3":   "O3",
    "co":   "CO",
    "so2":  "SO2",
}


async def get_nearby_locations(
    latitude: float,
    longitude: float,
    radius: int = 10000,
):
    """Return raw list of monitoring stations near the given coordinates."""
    headers = {"X-API-Key": settings.openaq_api_key}

    params = {
        "coordinates": f"{latitude},{longitude}",
        "radius": radius,
        "limit": 10,
    }

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(
            f"{OPENAQ_BASE_URL}/locations",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        return response.json()


async def get_openaq_air_quality(
    latitude: float,
    longitude: float,
    radius: int = 25000,
) -> dict | None:
    """
    Find the nearest OpenAQ station and retrieve its latest sensor readings.
    Returns a normalised dict or None when no station/data is available.
    """
    headers = {"X-API-Key": settings.openaq_api_key}

    # Step 1: find nearest location
    location_id, station_name = await _find_nearest_location(
        latitude, longitude, radius, headers
    )

    if location_id is None:
        return None

    # Step 2: fetch sensors for that location
    pollutants, timestamp = await _fetch_sensor_readings(location_id, headers)

    return {
        "aqi": None,          # OpenAQ does not expose a computed AQI index
        "pollutants": pollutants,
        "station_name": station_name,
        "timestamp": timestamp,
        "source": "OpenAQ",
    }


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

async def _find_nearest_location(
    latitude: float,
    longitude: float,
    radius: int,
    headers: dict,
) -> tuple[int | None, str | None]:
    """Return (location_id, station_name) for the closest station, or (None, None)."""
    params = {
        "coordinates": f"{latitude},{longitude}",
        "radius": radius,
        "limit": 5,
    }

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(
            f"{OPENAQ_BASE_URL}/locations",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        body = response.json()

    results = body.get("results", [])
    if not results:
        return None, None

    location = results[0]
    location_id = location.get("id")
    station_name = location.get("name") or location.get("locality") or None

    return location_id, station_name


async def _fetch_sensor_readings(
    location_id: int,
    headers: dict,
) -> tuple[list[dict], str | None]:
    """
    Fetch latest sensor measurements for a location.
    Returns (normalised_pollutants, iso_timestamp).
    """
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(
            f"{OPENAQ_BASE_URL}/locations/{location_id}/sensors",
            headers=headers,
        )
        response.raise_for_status()
        body = response.json()

    sensors = body.get("results", [])
    raw_readings: list[dict] = []
    latest_ts: str | None = None

    for sensor in sensors:
        parameter = sensor.get("parameter", {})
        param_name = parameter.get("name", "").lower()

        label = PARAMETER_LABEL.get(param_name)
        if label is None:
            continue   # skip non-target pollutants

        unit = parameter.get("units") or parameter.get("unit")
        latest = sensor.get("latest") or {}
        value = latest.get("value")
        ts = latest.get("datetime")
        if isinstance(ts, dict):
            ts = ts.get("local") or ts.get("utc")

        raw_readings.append({
            "pollutant": label,
            "value": value,
            "unit": unit,
        })

        # Track the most recent timestamp seen across all sensors
        if ts and latest_ts is None:
            latest_ts = ts

    normalised = normalize_pollutants(raw_readings)
    validated_ts = validate_timestamp(latest_ts)

    return normalised, validated_ts
