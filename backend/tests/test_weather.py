import pytest
import respx
import httpx

from app.services.openweather_service import (
    get_openweather_weather,
    OPENWEATHER_BASE_URL,
)


@pytest.mark.asyncio
@respx.mock
async def test_weather_api_success():
    url = f"{OPENWEATHER_BASE_URL}/weather"
    respx.get(url).respond(
        200,
        json={
            "name": "Delhi",
            "sys": {"country": "IN"},
            "main": {
                "temp": 28.5,
                "feels_like": 30.1,
                "humidity": 65,
                "pressure": 1012,
            },
            "wind": {"speed": 4.5},
            "weather": [
                {"description": "clear sky", "icon": "01d"}
            ],
        },
    )

    result = await get_openweather_weather(28.6139, 77.2090)
    assert result is not None
    assert result["temperature"] == 28.5
    assert result["feels_like"] == 30.1
    assert result["humidity"] == 65
    assert result["wind_speed_kmh"] == round(4.5 * 3.6, 1)
    assert result["description"] == "clear sky"
    assert result["icon"] == "01d"


@pytest.mark.asyncio
@respx.mock
async def test_weather_api_invalid_credentials_401():
    url = f"{OPENWEATHER_BASE_URL}/weather"
    respx.get(url).respond(401, json={"cod": 401, "message": "Invalid API key"})

    result = await get_openweather_weather(28.6139, 77.2090)
    # Service gracefully logs and returns None rather than crashing
    assert result is None


@pytest.mark.asyncio
@respx.mock
async def test_weather_api_rate_limit_429():
    url = f"{OPENWEATHER_BASE_URL}/weather"
    respx.get(url).respond(429, json={"cod": 429, "message": "Rate limit exceeded"})

    result = await get_openweather_weather(28.6139, 77.2090)
    assert result is None


@pytest.mark.asyncio
@respx.mock
async def test_weather_api_timeout():
    url = f"{OPENWEATHER_BASE_URL}/weather"
    respx.get(url).mock(side_effect=httpx.TimeoutException("Read timed out"))

    result = await get_openweather_weather(28.6139, 77.2090)
    assert result is None

