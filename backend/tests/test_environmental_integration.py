import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from main import app
from app.services.environmental_service import collect_environmental_data

client = TestClient(app)


@pytest.mark.asyncio
async def test_collect_environmental_data_success():
    mock_aq = {
        "aqi": 110.0,
        "pollutants": [{"pollutant": "PM2.5", "value": 40.0, "unit": "µg/m³"}],
        "station_name": "Test Station",
        "source": "MockAQ",
    }
    mock_wx = {
        "temperature": 26.5,
        "humidity": 70,
        "wind_speed_kmh": 12.0,
        "description": "cloudy",
    }
    mock_tf = {
        "current_speed_kmph": 40,
        "free_flow_speed_kmph": 50,
        "congestion_percent": 20.0,
        "congestion_level": "Moderate",
    }

    with patch("app.services.environmental_service.get_current_air_quality", new=AsyncMock(return_value=mock_aq)), \
         patch("app.services.environmental_service.get_current_weather", new=AsyncMock(return_value=mock_wx)), \
         patch("app.services.environmental_service.get_traffic_data", new=AsyncMock(return_value={"mock": True})), \
         patch("app.services.environmental_service.normalize_traffic", return_value=mock_tf):

        data = await collect_environmental_data(28.6139, 77.2090)

        assert data["location"]["latitude"] == 28.6139
        assert data["location"]["longitude"] == 77.2090
        assert data["air_quality"]["aqi"] == 110.0
        assert data["weather"]["temperature"] == 26.5
        assert data["traffic"]["congestion_level"] == "Moderate"
        assert "collected_at" in data


@pytest.mark.asyncio
async def test_collect_environmental_data_partial_failure():
    """Verify that when one provider (e.g. traffic or weather) fails, the remaining data is still returned."""
    mock_aq = {"aqi": 80.0, "pollutants": []}

    with patch("app.services.environmental_service.get_current_air_quality", new=AsyncMock(return_value=mock_aq)), \
         patch("app.services.environmental_service.get_current_weather", new=AsyncMock(side_effect=Exception("Weather API timeout"))), \
         patch("app.services.environmental_service.get_traffic_data", new=AsyncMock(side_effect=Exception("TomTom 429 Rate Limit"))):

        data = await collect_environmental_data(28.6139, 77.2090)

        assert data["air_quality"] is not None
        assert data["air_quality"]["aqi"] == 80.0
        assert data["weather"] is None
        assert data["traffic"] is None
        assert data["location"] is not None


@pytest.mark.asyncio
async def test_invalid_coordinates():
    with pytest.raises(ValueError, match="Invalid latitude"):
        await collect_environmental_data(95.0, 77.2090)

    with pytest.raises(ValueError, match="Invalid longitude"):
        await collect_environmental_data(28.6139, 195.0)


def test_api_environmental_current_endpoint():
    mock_payload = {
        "location": {"latitude": 28.6139, "longitude": 77.2090},
        "air_quality": {"aqi": 95.0},
        "weather": {"temperature": 25.0},
        "traffic": {"congestion_level": "Low"},
        "collected_at": "2026-11-11T12:00:00Z",
    }

    with patch("app.routes.environmental.collect_environmental_data", new=AsyncMock(return_value=mock_payload)), \
         patch("app.routes.environmental.write_environmental_data", return_value=True):

        response = client.get("/api/environmental/current?latitude=28.6139&longitude=77.2090")
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["air_quality"]["aqi"] == 95.0
        assert json_data["weather"]["temperature"] == 25.0


def test_api_environmental_historical_endpoint():
    mock_records = [
        {"timestamp": "2026-11-11T10:00:00Z", "aqi": 120.0, "temperature": 22.0},
        {"timestamp": "2026-11-11T11:00:00Z", "aqi": 115.0, "temperature": 24.0},
    ]

    with patch("app.routes.environmental.query_historical_environmental_data", return_value=mock_records):
        response = client.get("/api/environmental/historical?latitude=28.6139&longitude=77.2090&range=24h")
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["count"] == 2
        assert len(json_data["data"]) == 2
        assert json_data["data"][0]["aqi"] == 120.0

