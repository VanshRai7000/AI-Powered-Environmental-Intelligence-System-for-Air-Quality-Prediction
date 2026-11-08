import os
from influxdb_client import InfluxDBClient

INFLUXDB_URL = os.getenv(
    "INFLUXDB_URL",
    "http://localhost:8086"
)

INFLUXDB_TOKEN = os.getenv(
    "INFLUXDB_TOKEN"
)

INFLUXDB_ORG = os.getenv(
    "INFLUXDB_ORG",
    "environmental-intelligence"
)

INFLUXDB_BUCKET = os.getenv(
    "INFLUXDB_BUCKET",
    "environmental_data"
)

client = InfluxDBClient(
    url=INFLUXDB_URL,
    token=INFLUXDB_TOKEN,
    org=INFLUXDB_ORG
)