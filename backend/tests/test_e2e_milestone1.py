from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_e2e_health_and_root():
    root_res = client.get("/")
    assert root_res.status_code == 200
    assert "running" in root_res.json()["message"].lower()

    with patch("app.routes.health.check_influxdb_connection", return_value=True):
        health_res = client.get("/health")
        assert health_res.status_code == 200
        assert health_res.json() == {"status": "healthy", "database": "connected"}


def test_e2e_location_validation_and_search():
    # Valid POST location
    post_res = client.post("/api/location", json={"latitude": 30.43844, "longitude": 77.62118})
    assert post_res.status_code == 200
    assert post_res.json()["latitude"] == 30.43844

    # Invalid coordinate boundaries -> 422 Validation Error
    bad_res = client.post("/api/location", json={"latitude": 120.0, "longitude": 77.6})
    assert bad_res.status_code == 422


def test_e2e_complete_environmental_workflow():
    """
    End-to-end Milestone 1 flow:
    Location resolution -> External API collection -> InfluxDB write -> Map stations -> Historical query.
    """
    in_memory_store = []

    def fake_write(data):
        in_memory_store.append(data)
        return True

    def fake_query(location=None, latitude=None, longitude=None, range_str="24h"):
        return [
            {
                "timestamp": item["collected_at"],
                "location_name": item["location"]["name"],
                "aqi": item["air_quality"]["aqi"],
                "temperature": item["weather"]["temperature"],
                "humidity": item["weather"]["humidity"],
                "congestion_percent": item["traffic"]["congestion_percent"],
                "pm2_5": 52.1,
                "pm10": 88.4,
            }
            for item in in_memory_store
            if not location or item["location"]["name"] == location
        ]

    with patch(
        "app.services.environmental_service.resolve_location",
        new=AsyncMock(return_value=(30.43844, 77.62118, "Paonta Sahib, Himachal Pradesh, IN")),
    ), patch(
        "app.services.environmental_service.get_current_air_quality",
        new=AsyncMock(
            return_value={
                "aqi": 142.0,
                "pollutants": [{"pollutant": "PM2.5", "value": 52.1, "unit": "µg/m³"}],
                "timestamp": "2026-11-12T04:00:00Z",
                "source": "OpenWeatherMap",
            }
        ),
    ), patch(
        "app.services.environmental_service.get_current_weather",
        new=AsyncMock(
            return_value={
                "temperature": 21.5,
                "feels_like": 21.0,
                "humidity": 68,
                "wind_speed_kmh": 7.2,
                "description": "clear sky",
                "icon": "01d",
            }
        ),
    ), patch(
        "app.services.environmental_service.get_traffic_data",
        new=AsyncMock(return_value={"currentSpeed": 38, "freeFlowSpeed": 45}),
    ), patch(
        "app.routes.environmental.write_environmental_data",
        side_effect=fake_write,
    ), patch(
        "app.routes.environmental.query_historical_environmental_data",
        side_effect=fake_query,
    ), patch(
        "app.routes.environmental.resolve_location",
        new=AsyncMock(return_value=(30.43844, 77.62118, "Paonta Sahib, Himachal Pradesh, IN")),
    ):
        # 1. Fetch combined environmental data by location name
        env_res = client.get("/api/environmental/current?location=Paonta Sahib")
        assert env_res.status_code == 200
        body = env_res.json()
        assert body["location"]["name"] == "Paonta Sahib, Himachal Pradesh, IN"
        assert body["air_quality"]["aqi"] == 142.0
        assert body["weather"]["temperature"] == 21.5
        assert body["traffic"]["congestion_level"] == "Low"

        # 2. Verify data was recorded and can be queried historically
        hist_res = client.get("/api/environmental/historical?location=Paonta Sahib&range=24h")
        assert hist_res.status_code == 200
        hist_body = hist_res.json()
        assert hist_body["count"] == 1
        assert hist_body["data"][0]["aqi"] == 142.0


def test_e2e_stations_endpoint_and_error_handling():
    # Missing both location and coordinates -> 400
    bad_req = client.get("/api/air-quality/stations")
    assert bad_req.status_code == 400

    bad_env = client.get("/api/environmental/current")
    assert bad_env.status_code == 400

    # Valid stations request with mocked providers
    with patch(
        "app.routes.air_quality.resolve_location",
        new=AsyncMock(return_value=(30.43844, 77.62118, "Paonta Sahib, Himachal Pradesh, IN")),
    ), patch(
        "app.routes.air_quality.get_waqi_stations_in_bounds",
        new=AsyncMock(
            return_value=[
                {
                    "id": "14698",
                    "name": "Doon University, Dehradun, India",
                    "latitude": 30.2694,
                    "longitude": 78.0441,
                    "aqi": 78.0,
                    "last_updated": "2026-11-12T05:00:00Z",
                    "source": "WAQI",
                }
            ]
        ),
    ), patch(
        "app.routes.air_quality.get_nearby_locations",
        new=AsyncMock(return_value={"results": []}),
    ):
        res = client.get("/api/air-quality/stations?location=Paonta Sahib")
        assert res.status_code == 200
        data = res.json()
        assert data["count"] == 1
        assert data["center"]["name"] == "Paonta Sahib, Himachal Pradesh, IN"
        assert data["stations"][0]["aqi"] == 78.0

