"""
Database Data Verification Script for Milestone 1.
Verifies InfluxDB connectivity, writes a test environmental reading,
queries it back from the time-series bucket, and validates data consistency.
"""
from datetime import datetime, timezone
from app.database.influxdb import (
    check_influxdb_connection,
    write_environmental_data,
    query_historical_environmental_data,
)


def run_verification() -> bool:
    print("=" * 60)
    print("InfluxDB Database Verification")
    print("=" * 60)

    connected = check_influxdb_connection()
    print(f"1. InfluxDB Connection Status : {'CONNECTED' if connected else 'DISCONNECTED'}")
    if not connected:
        print("   -> Make sure Docker container 'environmental-influxdb' is running.")
        return False

    sample_location = "Paonta Sahib, Himachal Pradesh, IN"
    sample_lat, sample_lon = 30.43844, 77.62118
    now_iso = datetime.now(timezone.utc).isoformat()

    sample_payload = {
        "location": {
            "name": sample_location,
            "latitude": sample_lat,
            "longitude": sample_lon,
        },
        "air_quality": {
            "aqi": 142.0,
            "station_name": sample_location,
            "pollutants": [
                {"pollutant": "PM2.5", "value": 52.1, "unit": "µg/m³"},
                {"pollutant": "PM10", "value": 88.4, "unit": "µg/m³"},
                {"pollutant": "NO2", "value": 24.5, "unit": "µg/m³"},
                {"pollutant": "O3", "value": 48.0, "unit": "µg/m³"},
                {"pollutant": "CO", "value": 310.0, "unit": "µg/m³"},
            ],
            "source": "OpenWeatherMap",
        },
        "weather": {
            "temperature": 21.5,
            "feels_like": 21.0,
            "humidity": 68,
            "wind_speed_kmh": 7.2,
        },
        "traffic": {
            "current_speed_kmph": 38,
            "free_flow_speed_kmph": 45,
            "congestion_percent": 15.56,
            "congestion_level": "Low",
        },
        "collected_at": now_iso,
    }

    write_ok = write_environmental_data(sample_payload)
    print(f"2. Write Test Record          : {'PASS' if write_ok else 'FAIL'}")
    if not write_ok:
        return False

    records = query_historical_environmental_data(location=sample_location, range_str="1h")
    print(f"3. Historical Query Count     : {len(records)} record(s) found for '{sample_location}'")
    if not records:
        print("   -> FAIL: No records retrieved after write.")
        return False

    latest = records[-1]
    print("4. Latest Stored Record Check :")
    print(f"   - Location  : {latest.get('location_name')}")
    print(f"   - Timestamp : {latest.get('timestamp')}")
    print(f"   - AQI       : {latest.get('aqi')}")
    print(f"   - PM2.5     : {latest.get('pm2_5')} µg/m³")
    print(f"   - PM10      : {latest.get('pm10')} µg/m³")
    print(f"   - Temp      : {latest.get('temperature')} °C")
    print(f"   - Humidity  : {latest.get('humidity')} %")
    print(f"   - Traffic   : {latest.get('congestion_percent')} %")

    assert latest.get("location_name") == sample_location
    assert latest.get("aqi") is not None
    assert latest.get("timestamp") is not None
    print("=" * 60)
    print("RESULT: Database verification PASSED")
    print("=" * 60)
    return True


if __name__ == "__main__":
    ok = run_verification()
    raise SystemExit(0 if ok else 1)

