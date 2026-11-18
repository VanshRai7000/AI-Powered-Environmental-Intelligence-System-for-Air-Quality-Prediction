import logging
import httpx

from app.config.settings import settings

logger = logging.getLogger(__name__)

OPENWEATHER_GEO_URL = "https://api.openweathermap.org/geo/1.0"
NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org"


async def geocode_location(location_name: str) -> tuple[float, float, str]:
    """
    Convert a user-entered location string (city, town, neighborhood, landmark)
    into (latitude, longitude, display_name).
    """
    clean_query = location_name.strip()
    if not clean_query:
        raise ValueError("Location name cannot be empty.")

    api_key = settings.openweather_api_key.strip()

    async with httpx.AsyncClient(timeout=8.0) as client:
        # 1. Try OpenWeather Geocoding API if key is present
        if api_key:
            try:
                res = await client.get(
                    f"{OPENWEATHER_GEO_URL}/direct",
                    params={"q": clean_query, "limit": 1, "appid": api_key},
                )
                if res.status_code == 200:
                    data = res.json()
                    if data:
                        first = data[0]
                        lat = round(float(first["lat"]), 5)
                        lon = round(float(first["lon"]), 5)
                        parts = [
                            first.get("name"),
                            first.get("state"),
                            first.get("country"),
                        ]
                        display_name = ", ".join([p for p in parts if p])
                        return lat, lon, display_name
            except Exception as exc:
                logger.warning("OpenWeather geocoding error: %s", exc)

        # 2. Fallback to OpenStreetMap Nominatim
        try:
            nom_res = await client.get(
                f"{NOMINATIM_BASE_URL}/search",
                params={"q": clean_query, "format": "json", "limit": 1, "addressdetails": 1},
                headers={"User-Agent": "EnvironmentalIntelligenceSystem/1.0"},
            )
            if nom_res.status_code == 200:
                data = nom_res.json()
                if data:
                    first = data[0]
                    lat = round(float(first["lat"]), 5)
                    lon = round(float(first["lon"]), 5)
                    display_name = first.get("display_name", clean_query)
                    parts = [p.strip() for p in display_name.split(",") if p.strip()]
                    short_name = ", ".join(parts[:3]) if len(parts) >= 3 else display_name
                    return lat, lon, short_name
        except Exception as exc:
            logger.warning("Nominatim geocoding error: %s", exc)

    raise ValueError(f"Could not find coordinates for location: '{clean_query}'. Please check the spelling.")


async def reverse_geocode(latitude: float, longitude: float) -> str:
    """
    Convert (latitude, longitude) into a human-friendly city/neighborhood name.
    """
    api_key = settings.openweather_api_key.strip()
    fallback = f"{round(latitude, 3)}, {round(longitude, 3)}"

    async with httpx.AsyncClient(timeout=8.0) as client:
        # 1. Try Nominatim for local neighborhood accuracy
        try:
            res = await client.get(
                f"{NOMINATIM_BASE_URL}/reverse",
                params={"lat": latitude, "lon": longitude, "format": "jsonv2", "zoom": 14},
                headers={"User-Agent": "EnvironmentalIntelligenceSystem/1.0"},
            )
            if res.status_code == 200:
                addr = res.json().get("address", {})
                local = (
                    addr.get("suburb")
                    or addr.get("neighbourhood")
                    or addr.get("town")
                    or addr.get("village")
                )
                city = addr.get("city") or addr.get("state_district")
                country = (addr.get("country_code") or "").upper()
                if local and city:
                    return f"{local}, {city}"
                if city and country:
                    return f"{city}, {country}"
                if local:
                    return local
        except Exception as exc:
            logger.debug("Reverse geocode Nominatim error: %s", exc)

        # 2. Try OpenWeather Reverse Geo
        if api_key:
            try:
                res = await client.get(
                    f"{OPENWEATHER_GEO_URL}/reverse",
                    params={"lat": latitude, "lon": longitude, "limit": 1, "appid": api_key},
                )
                if res.status_code == 200:
                    data = res.json()
                    if data:
                        item = data[0]
                        name = item.get("name")
                        state = item.get("state")
                        if name and state:
                            return f"{name}, {state}"
                        if name:
                            return name
            except Exception as exc:
                logger.debug("Reverse geocode OWM error: %s", exc)

    return fallback


async def resolve_location(
    location: str | float | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> tuple[float, float, str]:
    """
    Unified resolver:
    - If `location` (name) is provided, resolves to (lat, lon, display_name).
    - If `latitude` and `longitude` are provided, reverse-geocodes to display_name.
    - Also supports legacy positional calls where first arg is numeric latitude.
    - Returns (lat, lon, location_name).
    """
    # Handle legacy positional calls: resolve_location(28.6139, 77.2090)
    if isinstance(location, (int, float)):
        longitude = latitude
        latitude = float(location)
        location = None

    if isinstance(location, str) and location.strip():
        return await geocode_location(location.strip())

    if latitude is not None and longitude is not None:
        display_name = await reverse_geocode(latitude, longitude)
        return latitude, longitude, display_name

    raise ValueError("Either a location name (e.g. 'Delhi') or latitude/longitude coordinates must be provided.")
