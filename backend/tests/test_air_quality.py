import pytest
import respx
import httpx

from app.services.openweather_service import (
    get_openweather_air_pollution,
    calculate_pm25_aqi,
    calculate_pm10_aqi,
    derive_composite_aqi,
    OPENWEATHER_BASE_URL,
)
from app.services.air_quality_service import get_current_air_quality


def test_epa_aqi_calculations():
    # PM2.5 standard categories
    assert calculate_pm25_aqi(8.0) == 33        # Good (0-50)
    assert calculate_pm25_aqi(25.0) == 78       # Moderate (51-100)
    assert calculate_pm25_aqi(45.0) == 124      # Sensitive (101-150)
    assert calculate_pm25_aqi(100.0) == 174     # Unhealthy (151-200)
    assert calculate_pm25_aqi(200.0) == 250     # Very Unhealthy (201-300)
    assert calculate_pm25_aqi(400.0) == 434     # Hazardous (301-500)

    # PM10 standard categories
    assert calculate_pm10_aqi(30.0) == 28       # Good
    assert calculate_pm10_aqi(100.0) == 73      # Moderate

    # Composite maximum
    assert derive_composite_aqi(pm25=25.0, pm10=30.0) == 78.0


@pytest.mark.asyncio
@respx.mock
async def test_air_quality_openweather_success():
    url = f"{OPENWEATHER_BASE_URL}/air_pollution"
    respx.get(url).respond(
        200,
        json={
            "list": [
                {
                    "main": {"aqi": 3},
                    "components": {
                        "co": 250.0,
                        "no": 0.5,
                        "no2": 25.0,
                        "o3": 50.0,
                        "so2": 10.0,
                        "pm2_5": 35.0,
                        "pm10": 60.0,
                        "nh3": 8.0,
                    },
                    "dt": 1700000000,
                }
            ]
        },
    )

    data = await get_openweather_air_pollution(28.6139, 77.2090)
    assert data is not None
    assert data["source"] == "OpenWeatherMap"
    assert data["aqi"] is not None
    assert len(data["pollutants"]) > 0


@pytest.mark.asyncio
@respx.mock
async def test_air_quality_openweather_rate_limit_and_fallback():
    # 1. OpenWeather returns 429
    respx.get(f"{OPENWEATHER_BASE_URL}/air_pollution").respond(429)

    # 2. WAQI fallback succeeds
    respx.get("https://api.waqi.info/feed/geo:28.6139;77.209/").respond(
        200,
        json={
            "status": "ok",
            "data": {
                "aqi": 145,
                "city": {"name": "Delhi Fallback Station"},
                "iaqi": {
                    "pm25": {"v": 145.0},
                    "pm10": {"v": 70.0},
                },
                "time": {"iso": "2026-11-11T12:00:00Z"},
            },
        },
    )

    result = await get_current_air_quality(28.6139, 77.2090)
    assert result is not None
    assert result["source"] == "WAQI"
    assert result["aqi"] == 145.0


@pytest.mark.asyncio
@respx.mock
async def test_air_quality_all_providers_fail():
    # OpenWeather fails
    respx.get(f"{OPENWEATHER_BASE_URL}/air_pollution").respond(503)
    # WAQI fails
    respx.get("https://api.waqi.info/feed/geo:28.6139;77.209/").respond(503)
    # OpenAQ fails
    respx.get("https://api.openaq.org/v3/locations").respond(503)

    result = await get_current_air_quality(28.6139, 77.2090)
    assert result is None
