from pydantic import BaseModel, Field


class LocationRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class LocationResponse(BaseModel):
    latitude: float
    longitude: float
    message: str


class LocationSearchResult(BaseModel):
    name: str
    state: str | None = None
    country: str | None = None
    latitude: float
    longitude: float
    display_name: str

    message: str


class LocationSearchResult(BaseModel):
    name: str
    state: str | None = None
    country: str | None = None
    latitude: float
    longitude: float
    display_name: str