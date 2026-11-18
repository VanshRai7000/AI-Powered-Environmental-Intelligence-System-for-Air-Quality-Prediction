import logging
from fastapi import APIRouter, HTTPException, Query
import httpx

from app.config.settings import settings
from app.schemas.location import (
    LocationRequest,
    LocationResponse,
    LocationSearchResult,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/location",
    tags=["Location"],
)


@router.post("", response_model=LocationResponse)
def receive_location(location: LocationRequest):
    return {
        "latitude": location.latitude,
        "longitude": location.longitude,
        "message": "Location received successfully",
    }


@router.get("/search", response_model=list[LocationSearchResult])
async def search_locations(
    query: str = Query(..., min_length=2, description="City, town, or neighborhood to search for"),
):
    """
    Search for locations worldwide by city, locality, or landmark name.
    Uses OpenWeatherMap Geocoding API with OpenStreetMap Nominatim as fallback.
    """
    cleaned_query = query.strip()
    results: list[LocationSearchResult] = []
    seen_coords = set()

    api_key = settings.openweather_api_key.strip()

    async with httpx.AsyncClient(timeout=8.0) as client:
        # 1. Try OpenWeather Direct Geocoding if API key is configured
        if api_key:
            try:
                owm_res = await client.get(
                    "https://api.openweathermap.org/geo/1.0/direct",
                    params={"q": cleaned_query, "limit": 5, "appid": api_key},
                )
                if owm_res.status_code == 200:
                    for item in owm_res.json():
                        name = item.get("name", "")
                        state = item.get("state")
                        country = item.get("country", "")
                        lat = round(float(item.get("lat")), 5)
                        lon = round(float(item.get("lon")), 5)
                        coord_key = (round(lat, 3), round(lon, 3))

                        if coord_key not in seen_coords:
                            seen_coords.add(coord_key)
                            parts = [p for p in [name, state, country] if p]
                            display_name = ", ".join(parts)
                            results.append(
                                LocationSearchResult(
                                    name=name,
                                    state=state,
                                    country=country,
                                    latitude=lat,
                                    longitude=lon,
                                    display_name=display_name,
                                )
                            )
            except Exception as exc:
                logger.warning("OWM geocode search error: %s", exc)

        # 2. If OWM returned fewer than 3 results or is unconfigured, supplement with Nominatim
        if len(results) < 3:
            try:
                nom_res = await client.get(
                    "https://nominatim.openstreetmap.org/search",
                    params={
                        "q": cleaned_query,
                        "format": "json",
                        "limit": 5,
                        "addressdetails": 1,
                    },
                    headers={"User-Agent": "EnvironmentalIntelligenceApp/1.0"},
                )
                if nom_res.status_code == 200:
                    for item in nom_res.json():
                        lat = round(float(item.get("lat")), 5)
                        lon = round(float(item.get("lon")), 5)
                        coord_key = (round(lat, 3), round(lon, 3))
                        if coord_key not in seen_coords:
                            seen_coords.add(coord_key)
                            addr = item.get("address", {})
                            name = (
                                addr.get("suburb")
                                or addr.get("neighbourhood")
                                or addr.get("city")
                                or addr.get("town")
                                or addr.get("village")
                                or item.get("name")
                                or cleaned_query
                            )
                            state = addr.get("state")
                            country = (addr.get("country_code") or "").upper()
                            display_name = item.get("display_name", "")
                            parts = [p.strip() for p in display_name.split(",") if p.strip()]
                            short_display = ", ".join(parts[:3]) if len(parts) >= 3 else display_name

                            results.append(
                                LocationSearchResult(
                                    name=name,
                                    state=state,
                                    country=country,
                                    latitude=lat,
                                    longitude=lon,
                                    display_name=short_display,
                                )
                            )
            except Exception as exc:
                logger.warning("Nominatim search error: %s", exc)

    return results[:5]



@router.get("/search", response_model=list[LocationSearchResult])
async def search_locations(
    query: str = Query(..., min_length=2, description="City, town, or neighborhood to search for"),
):
    """
    Search for locations worldwide by city, locality, or landmark name.
    Uses OpenWeatherMap Geocoding API with OpenStreetMap Nominatim as fallback.
    """
    cleaned_query = query.strip()
    results: list[LocationSearchResult] = []
    seen_coords = set()

    api_key = settings.openweather_api_key.strip()

    async with httpx.AsyncClient(timeout=8.0) as client:
        # 1. Try OpenWeather Direct Geocoding if API key is configured
        if api_key:
            try:
                owm_res = await client.get(
                    "https://api.openweathermap.org/geo/1.0/direct",
                    params={"q": cleaned_query, "limit": 5, "appid": api_key},
                )
                if owm_res.status_code == 200:
                    for item in owm_res.json():
                        name = item.get("name", "")
                        state = item.get("state")
                        country = item.get("country", "")
                        lat = round(float(item.get("lat")), 5)
                        lon = round(float(item.get("lon")), 5)
                        coord_key = (round(lat, 3), round(lon, 3))

                        if coord_key not in seen_coords:
                            seen_coords.add(coord_key)
                            parts = [p for p in [name, state, country] if p]
                            display_name = ", ".join(parts)
                            results.append(
                                LocationSearchResult(
                                    name=name,
                                    state=state,
                                    country=country,
                                    latitude=lat,
                                    longitude=lon,
                                    display_name=display_name,
                                )
                            )
            except Exception as exc:
                logger.warning("OWM geocode search error: %s", exc)

        # 2. If OWM returned fewer than 3 results or is unconfigured, supplement with Nominatim
        if len(results) < 3:
            try:
                nom_res = await client.get(
                    "https://nominatim.openstreetmap.org/search",
                    params={
                        "q": cleaned_query,
                        "format": "json",
                        "limit": 5,
                        "addressdetails": 1,
                    },
                    headers={"User-Agent": "EnvironmentalIntelligenceApp/1.0"},
                )
                if nom_res.status_code == 200:
                    for item in nom_res.json():
                        lat = round(float(item.get("lat")), 5)
                        lon = round(float(item.get("lon")), 5)
                        coord_key = (round(lat, 3), round(lon, 3))
                        if coord_key not in seen_coords:
                            seen_coords.add(coord_key)
                            addr = item.get("address", {})
                            name = (
                                addr.get("suburb")
                                or addr.get("neighbourhood")
                                or addr.get("city")
                                or addr.get("town")
                                or addr.get("village")
                                or item.get("name")
                                or cleaned_query
                            )
                            state = addr.get("state")
                            country = (addr.get("country_code") or "").upper()
                            display_name = item.get("display_name", "")
                            parts = [p.strip() for p in display_name.split(",") if p.strip()]
                            short_display = ", ".join(parts[:3]) if len(parts) >= 3 else display_name

                            results.append(
                                LocationSearchResult(
                                    name=name,
                                    state=state,
                                    country=country,
                                    latitude=lat,
                                    longitude=lon,
                                    display_name=short_display,
                                )
                            )
            except Exception as exc:
                logger.warning("Nominatim search error: %s", exc)

    return results[:5]