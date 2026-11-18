from pydantic import BaseModel


class WeatherResponse(BaseModel):
    latitude: float
    longitude: float
    location_name: str | None
    temperature: float | None
    feels_like: float | None
    humidity: int | None
    wind_speed_kmh: float | None
    description: str | None = None
    icon: str | None = None
    precipitation: float | None = None
    weather_code: int | None = None
    timestamp: str | None = None
    source: str = "OpenWeatherMap"

