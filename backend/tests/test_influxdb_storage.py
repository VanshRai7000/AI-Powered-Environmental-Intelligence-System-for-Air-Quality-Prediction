from unittest.mock import patch, MagicMock

from app.database.influxdb import (
    write_environmental_data,
    query_historical_environmental_data,
    check_influxdb_connection,
)


def test_write_environmental_data_success():
    mock_data = {
        "location": {"latitude": 28.6139, "longitude": 77.2090},
        "air_quality": {
            "aqi": 150.0,
            "station_name": "Test Station",
            "pollutants": [
                {"pollutant": "PM2.5", "value": 55.4},
                {"pollutant": "NO2", "value": 20.1},
            ],
        },
        "weather": {
            "temperature": 27.0,
            "humidity": 60,
            "wind_speed_kmh": 10.0,
        },
        "traffic": {
            "congestion_percent": 15.5,
            "current_speed_kmph": 45,
            "free_flow_speed_kmph": 50,
        },
        "collected_at": "2026-11-11T12:00:00Z",
    }

    mock_write_api = MagicMock()
    with patch("app.database.influxdb.influx_client.write_api", return_value=mock_write_api):
        result = write_environmental_data(mock_data)
        assert result is True
        mock_write_api.write.assert_called_once()


def test_write_environmental_data_missing_location():
    # If location is missing, it should gracefully return False without crashing
    bad_data = {"air_quality": {"aqi": 100}}
    result = write_environmental_data(bad_data)
    assert result is False


def test_write_environmental_data_offline_resilience():
    # When InfluxDB raises an error (e.g. connection refused), write returns False safely
    mock_data = {"location": {"latitude": 28.6139, "longitude": 77.2090}}
    with patch("app.database.influxdb.influx_client.write_api", side_effect=Exception("Connection Refused")):
        result = write_environmental_data(mock_data)
        assert result is False


def test_query_historical_data_parsing():
    mock_record_1 = MagicMock()
    mock_record_1.values = {
        "_time": "2026-11-11T10:00:00Z",
        "aqi": 110.0,
        "temperature": 23.5,
        "humidity": 65,
        "wind_speed_kmh": 8.0,
        "congestion_percent": 12.0,
        "pollutant_pm2_5": 38.0,
        "pollutant_pm10": 60.0,
        "pollutant_no2": 15.0,
        "pollutant_o3": 25.0,
        "pollutant_co": 1.1,
        "pollutant_so2": 5.0,
    }

    mock_table = MagicMock()
    mock_table.records = [mock_record_1]

    mock_query_api = MagicMock()
    mock_query_api.query.return_value = [mock_table]

    with patch("app.database.influxdb.influx_client.query_api", return_value=mock_query_api):
        records = query_historical_environmental_data(28.6139, 77.2090, "24h")
        assert len(records) == 1
        assert records[0]["aqi"] == 110.0
        assert records[0]["temperature"] == 23.5
        assert records[0]["pm2_5"] == 38.0
        assert records[0]["congestion_percent"] == 12.0


def test_check_influxdb_connection_mocked():
    mock_health = MagicMock()
    mock_health.status = "pass"
    with patch("app.database.influxdb.influx_client.health", return_value=mock_health):
        assert check_influxdb_connection() is True

    mock_health.status = "fail"
    with patch("app.database.influxdb.influx_client.health", return_value=mock_health):
        assert check_influxdb_connection() is False

