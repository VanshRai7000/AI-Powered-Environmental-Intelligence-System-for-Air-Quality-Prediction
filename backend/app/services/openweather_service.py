import asyncio
import logging
import math
from datetime import datetime, timezone
import httpx

from app.config.settings import settings
from app.services.pollutant_service import normalize_pollutant

logger = logging.getLogger(__name__)

OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"
OPENWEATHER_GEO_URL = "https://api.openweathermap.org/geo/1.0"
NOMINATIM_REVERSE_URL = "https://nominatim.openstreetmap.org/reverse"

POLLUTANT_MAP = {
    "pm2_5": ("PM2.5", "µg/m³"),
    "pm10":  ("PM10",  "µg/m³"),
    "no2":   ("NO2",   "µg/m³"),
    "o3":    ("O3",    "µg/m³"),
    "co":    ("CO",    "µg/m³"),
    "so2":   ("SO2",   "µg/m³"),
    "nh3":   ("NH3",   "µg/m³"),
    "no":    ("NO",    "µg/m³"),
}


def calculate_pm25_aqi(pm25: float) -> int:
    """Calculate US EPA AQI from PM2.5 concentration (ug/m3)."""
    if pm25 < 0:
        return 0
    # EPA spec truncates PM2.5 to 1 decimal place so values like 12.05 don't fall into gaps
    c = math.floor(pm25 * 10) / 10.0
    breakpoints = [
        (0.0, 12.0, 0, 50),
        (12.1, 35.4, 51, 100),
        (35.5, 55.4, 101, 150),
        (55.5, 150.4, 151, 200),
        (150.5, 250.4, 201, 300),
        (250.5, 350.4, 301, 400),
        (350.5, 500.4, 401, 500),
    ]
    for c_low, c_high, i_low, i_high in breakpoints:
        if c_low <= c <= c_high:
            return round(((i_high - i_low) / (c_high - c_low)) * (c - c_low) + i_low)
    return 500 if c > 500.4 else 0


def calculate_pm10_aqi(pm10: float) -> int:
    """Calculate US EPA AQI from PM10 concentration (ug/m3)."""
    if pm10 < 0:
        return 0
    # EPA spec truncates PM10 to an integer so values like 54.6 don't fall into gaps
    c = float(math.floor(pm10))
    breakpoints = [
        (0.0, 54.0, 0, 50),
        (55.0, 154.0, 51, 100),
        (155.0, 254.0, 101, 150),
        (255.0, 354.0, 151, 200),
        (355.0, 424.0, 201, 300),
        (425.0, 504.0, 301, 400),
        (505.0, 604.0, 401, 500),
    ]
    for c_low, c_high, i_low, i_high in breakpoints:
        if c_low <= c <= c_high:
            return round(((i_high - i_low) / (c_high - c_low)) * (c - c_low) + i_low)
    return 500 if c > 604.0 else 0


def derive_composite_aqi(
    pm25: float | None,
    pm10: float | None,
    owm_index: int | None = None
) -> float | None:
    """Derive standard 0-500 AQI score from PM readings or OWM qualitative index."""
    aqi_values = []
    if pm25 is not None and pm25 >= 0:
        aqi_values.append(calculate_pm25_aqi(pm25))
    if pm10 is not None and pm10 >= 0:
        aqi_values.append(calculate_pm10_aqi(pm10))

    if aqi_values:
        return float(max(aqi_values))

    owm_fallback = {1: 25, 2: 75, 3: 125, 4: 175, 5: 350}
    if owm_index in owm_fallback:
        return float(owm_fallback[owm_index])

    return None


async def resolve_exact_location_name(
    client: httpx.AsyncClient,
    latitude: float,
    longitude: float,
    api_key: str,
    fallback_name: str | None = None,
) -> str | None:
    """Resolve exact neighborhood/city name using OpenStreetMap Nominatim and OWM Reverse Geo."""
    # 1. Try OpenStreetMap Nominatim for hyper-local suburb/city accuracy
    try:
        nom_res = await client.get(
            NOMINATIM_REVERSE_URL,
            params={"lat": latitude, "lon": longitude, "format": "jsonv2", "zoom": 14},
            headers={"User-Agent": "AirQualityDashboard/1.0", "Accept-Language": "en"},
            timeout=5.0,
        )
        if nom_res.status_code == 200:
            addr = nom_res.json().get("address", {})
            locality = (
                addr.get("suburb")
                or addr.get("neighbourhood")
                or addr.get("town")
                or addr.get("village")
            )
            city = addr.get("city") or addr.get("state_district") or addr.get("county")
            country_code = (addr.get("country_code") or "").upper()

            if locality and city and locality != city:
                return f"{locality}, {city}"
            if city and country_code:
                return f"{city}, {country_code}"
            if locality and country_code:
                return f"{locality}, {country_code}"
    except Exception as exc:
        logger.debug("Nominatim reverse geocode skipped: %s", exc)

    # 2. Fallback to OpenWeather Reverse Geocoding API
    try:
        geo_res = await client.get(
            f"{OPENWEATHER_GEO_URL}/reverse",
            params={"lat": latitude, "lon": longitude, "limit": 1, "appid": api_key},
            timeout=5.0,
        )
        if geo_res.status_code == 200:
            geo_list = geo_res.json()
            if geo_list:
                place = geo_list[0]
                name = place.get("name")
                state = place.get("state")
                country = place.get("country")
                if name and state:
                    return f"{name}, {state}"
                if name and country:
                    return f"{name}, {country}"
    except Exception as exc:
        logger.debug("OWM reverse geocode skipped: %s", exc)

    return fallback_name


async def get_openweather_air_pollution(latitude: float, longitude: float) -> dict | None:
    """Fetch air pollution measurements from OpenWeatherMap for any lat/lon."""
    api_key = settings.openweather_api_key.strip()
    if not api_key:
        logger.warning("OPENWEATHER_API_KEY is not configured")
        return None

    url = f"{OPENWEATHER_BASE_URL}/air_pollution"
    params = {"lat": latitude, "lon": longitude, "appid": api_key}

    try:
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.get(url, params=params)
            if response.status_code != 200:
                logger.warning("OpenWeather air_pollution returned %s: %s", response.status_code, response.text)
                return None
            body = response.json()
    except httpx.HTTPError as exc:
        logger.error("HTTP error fetching OpenWeather air_pollution: %s", exc)
        return None

    results = body.get("list", [])
    if not results:
        return None

    first = results[0]
    components = first.get("components", {})
    owm_aqi_index = first.get("main", {}).get("aqi")
    dt = first.get("dt")

    pm25 = components.get("pm2_5")
    pm10 = components.get("pm10")
    aqi = derive_composite_aqi(pm25, pm10, owm_aqi_index)

    pollutants = []
    for key, (label, default_unit) in POLLUTANT_MAP.items():
        if key in components:
            clean = normalize_pollutant(label, components[key], default_unit)
            if clean:
                pollutants.append(clean)

    iso_timestamp = None
    if dt:
        iso_timestamp = datetime.fromtimestamp(dt, tz=timezone.utc).isoformat()

    return {
        "aqi": aqi,
        "pollutants": pollutants,
        "timestamp": iso_timestamp,
        "source": "OpenWeatherMap",
    }


async def get_openweather_weather(latitude: float, longitude: float) -> dict | None:
    """Fetch current weather conditions, temperature, humidity, wind, and exact city name."""
    api_key = settings.openweather_api_key.strip()
    if not api_key:
        return None

    url = f"{OPENWEATHER_BASE_URL}/weather"
    params = {
        "lat": latitude,
        "lon": longitude,
        "appid": api_key,
        "units": "metric",
    }

    try:
        async with httpx.AsyncClient(timeout=12) as client:
            weather_res = await client.get(url, params=params)
            if weather_res.status_code != 200:
                logger.warning("OpenWeather weather returned %s: %s", weather_res.status_code, weather_res.text)
                return None
            data = weather_res.json()

            raw_city = data.get("name")
            country = data.get("sys", {}).get("country")
            owm_fallback = f"{raw_city}, {country}" if raw_city and country else raw_city

            # Resolve exact neighborhood/city instead of relying solely on OWM station name
            station_name = await resolve_exact_location_name(
                client, latitude, longitude, api_key, fallback_name=owm_fallback
            )
    except httpx.HTTPError as exc:
        logger.error("HTTP error fetching OpenWeather weather: %s", exc)
        return None

    main = data.get("main", {})
    wind = data.get("wind", {})
    rain = data.get("rain", {})
    weather_list = data.get("weather", [])
    weather_desc = weather_list[0].get("description") if weather_list else None
    weather_icon = weather_list[0].get("icon") if weather_list else None
    weather_code = weather_list[0].get("id") if weather_list else None

    speed_ms = wind.get("speed")
    wind_kmh = round(speed_ms * 3.6, 1) if speed_ms is not None else None
    precipitation = rain.get("1h") or rain.get("3h") or 0.0
    dt = data.get("dt")
    iso_timestamp = datetime.fromtimestamp(dt, tz=timezone.utc).isoformat() if dt else None

    return {
        "station_name": station_name,
        "owm_station_name": owm_fallback,
        "coordinates": {"lat": latitude, "lon": longitude},
        "temperature": round(main.get("temp", 0), 1) if "temp" in main else None,
        "feels_like": round(main.get("feels_like", 0), 1) if "feels_like" in main else None,
        "humidity": main.get("humidity"),
        "wind_speed_kmh": wind_kmh,
        "description": weather_desc,
        "icon": weather_icon,
        "precipitation": precipitation,
        "weather_code": weather_code,
        "timestamp": iso_timestamp,
    }