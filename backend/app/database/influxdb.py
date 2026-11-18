import logging
from datetime import datetime, timezone
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

from app.config.settings import settings

logger = logging.getLogger(__name__)

# Initialize InfluxDB client with a 3-second timeout so queries don't hang if DB is offline
influx_client = InfluxDBClient(
    url=settings.influxdb_url,
    token=settings.influxdb_token,
    org=settings.influxdb_org,
    timeout=3000,
)


def get_influx_client():
    return influx_client


def check_influxdb_connection() -> bool:
    try:
        health = influx_client.health()
        return health.status == "pass"
    except Exception:
        return False


def write_environmental_data(data: dict) -> bool:
    """
    Store collected environmental measurements (air quality, weather, traffic)
    into the InfluxDB time-series database tagged by location name and coordinates.
    """
    try:
        loc = data.get("location", {})
        lat = loc.get("latitude")
        lon = loc.get("longitude")
        location_name = loc.get("name") or "Unknown"

        if lat is None or lon is None:
            logger.warning("Cannot write to InfluxDB: missing latitude/longitude")
            return False

        # Extract timestamp
        collected_at = data.get("collected_at")
        if collected_at:
            try:
                ts = datetime.fromisoformat(collected_at.replace("Z", "+00:00"))
            except Exception:
                ts = datetime.now(timezone.utc)
        else:
            ts = datetime.now(timezone.utc)

        loc_tag = f"{round(lat, 3)},{round(lon, 3)}"
        aq = data.get("air_quality") or {}
        wx = data.get("weather") or {}
        tf = data.get("traffic") or {}

        # City / area tag
        city_tag = (
            location_name
            or aq.get("station_name")
            or wx.get("station_name")
            or "Unknown"
        )

        point = (
            Point("environmental_measurement")
            .tag("location_name", str(city_tag))
            .tag("city", str(city_tag))
            .tag("location", loc_tag)
            .field("latitude", float(lat))
            .field("longitude", float(lon))
            .time(ts, WritePrecision.NS)
        )

        # 1. Air Quality fields
        if aq:
            if aq.get("aqi") is not None:
                point.field("aqi", float(aq["aqi"]))
            for p in aq.get("pollutants", []):
                p_name = p.get("pollutant", "").lower().replace(".", "_")
                val = p.get("value")
                if p_name and val is not None:
                    point.field(f"pollutant_{p_name}", float(val))

        # 2. Weather fields
        if wx:
            if wx.get("temperature") is not None:
                point.field("temperature", float(wx["temperature"]))
            if wx.get("feels_like") is not None:
                point.field("feels_like", float(wx["feels_like"]))
            if wx.get("humidity") is not None:
                point.field("humidity", float(wx["humidity"]))
            if wx.get("wind_speed_kmh") is not None:
                point.field("wind_speed_kmh", float(wx["wind_speed_kmh"]))

        # 3. Traffic fields
        if tf:
            if tf.get("congestion_percent") is not None:
                point.field("congestion_percent", float(tf["congestion_percent"]))
            if tf.get("current_speed_kmph") is not None:
                point.field("current_speed_kmph", float(tf["current_speed_kmph"]))
            if tf.get("free_flow_speed_kmph") is not None:
                point.field("free_flow_speed_kmph", float(tf["free_flow_speed_kmph"]))

        write_api = influx_client.write_api(write_options=SYNCHRONOUS)
        write_api.write(
            bucket=settings.influxdb_bucket,
            org=settings.influxdb_org,
            record=point,
        )
        logger.info("Successfully wrote environmental measurement to InfluxDB for '%s'", city_tag)
        return True

    except Exception as exc:
        logger.warning("Failed writing to InfluxDB: %s", exc)
        return False


def query_historical_environmental_data(
    location: str | float | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    range_str: str = "24h",
) -> list[dict]:
    """
    Retrieve historical measurements from InfluxDB by location name or coordinates
    within the requested time range (e.g. '1h', '24h', '7d', '30d').
    """
    # Support positional arguments: (lat, lon, range_str)
    if isinstance(location, (int, float)):
        if isinstance(longitude, str):
            range_str = longitude
        longitude = latitude
        latitude = float(location)
        location = None

    allowed_ranges = {"1h", "6h", "12h", "24h", "48h", "7d", "30d"}
    safe_range = range_str if range_str in allowed_ranges else "24h"

    # Build filtering clause
    if isinstance(location, str) and location.strip():
        safe_loc = location.strip().replace('"', '\\"')
        filter_clause = f'r["location_name"] == "{safe_loc}" or r["city"] == "{safe_loc}"'
    elif latitude is not None and longitude is not None:
        loc_tag = f"{round(latitude, 3)},{round(longitude, 3)}"
        filter_clause = f'r["location"] == "{loc_tag}"'
    else:
        filter_clause = 'true'

    flux_query = f'''
    from(bucket: "{settings.influxdb_bucket}")
      |> range(start: -{safe_range})
      |> filter(fn: (r) => r["_measurement"] == "environmental_measurement")
      |> filter(fn: (r) => {filter_clause})
      |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
      |> sort(columns: ["_time"], desc: false)
    '''

    try:
        query_api = influx_client.query_api()
        tables = query_api.query(query=flux_query, org=settings.influxdb_org)
        records = []

        for table in tables:
            for record in table.records:
                values = record.values
                t = values.get("_time")
                timestamp_str = t.isoformat() if hasattr(t, "isoformat") else str(t)

                records.append({
                    "timestamp": timestamp_str,
                    "location_name": values.get("location_name") or values.get("city"),
                    "aqi": values.get("aqi"),
                    "temperature": values.get("temperature"),
                    "humidity": values.get("humidity"),
                    "wind_speed_kmh": values.get("wind_speed_kmh"),
                    "congestion_percent": values.get("congestion_percent"),
                    "pm2_5": values.get("pollutant_pm2_5"),
                    "pm10": values.get("pollutant_pm10"),
                    "no2": values.get("pollutant_no2"),
                    "o3": values.get("pollutant_o3"),
                    "co": values.get("pollutant_co"),
                    "so2": values.get("pollutant_so2"),
                })

        return records

    except Exception as exc:
        logger.warning("Historical InfluxDB query failed: %s", exc)
        return []
