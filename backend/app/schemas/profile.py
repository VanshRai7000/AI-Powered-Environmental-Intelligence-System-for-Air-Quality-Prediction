from pydantic import BaseModel, Field


class HealthSensitivity(BaseModel):
    asthma: bool = False
    elderly: bool = False
    children: bool = False


class AlertPreferences(BaseModel):
    enabled: bool = True
    custom_threshold: int | None = Field(
        default=None,
        ge=0,
        le=500
    )


class HealthProfile(BaseModel):
    sensitivity: HealthSensitivity
    alert_preferences: AlertPreferences