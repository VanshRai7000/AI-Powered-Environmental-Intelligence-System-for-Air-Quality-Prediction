from pydantic import BaseModel


class PollutantReading(BaseModel):
    pollutant: str
    value: float | None
    unit: str | None


class AirQualityResponse(BaseModel):
    latitude: float
    longitude: float

    aqi: float | None

    pollutants: list[PollutantReading]

    station_name: str | None
    timestamp: str | None

    source: str
