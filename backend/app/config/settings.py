from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Environmental Intelligence System"
    app_env: str = "development"

    influxdb_url: str
    influxdb_token: str
    influxdb_org: str
    influxdb_bucket: str

    #External APIs
    openweather_api_key: str = ""
    openaq_api_key: str = ""
    openweather_base_url: str = (
        "https://api.openweathermap.org/data/2.5/weather"
    )
    tomtom_api_key: str = ""
    waqi_api_token: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False
    )


settings = Settings()