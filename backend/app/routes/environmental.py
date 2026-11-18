import logging
from fastapi import (
    APIRouter,
    BackgroundTasks,
    HTTPException,
    Query,
)

from app.services.environmental_service import (
    collect_environmental_data,
)
from app.services.geo_service import resolve_location
from app.database.influxdb import (
    write_environmental_data,
    query_historical_environmental_data,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/environmental",
    tags=["Environmental Data"],
)


@router.get("/current")
async def current_environmental_data(
    location: str | None = Query(None, description="City, neighborhood or address (e.g. 'Delhi', 'Indirapuram')"),
    latitude: float | None = Query(None, ge=-90, le=90, description="Latitude (optional if location is provided)"),
    longitude: float | None = Query(None, ge=-180, le=180, description="Longitude (optional if location is provided)"),
    background_tasks: BackgroundTasks = None,
):
    """
    Retrieve real-time environmental data (Air Quality, Weather, Traffic) by location name or coordinates.
    Stores reading in InfluxDB tagged by location name for historical analysis.
    """
    if not location and (latitude is None or longitude is None):
        raise HTTPException(
            status_code=400,
            detail="Please provide a location name (e.g. ?location=Delhi) or latitude & longitude coordinates.",
        )

    try:
        data = await collect_environmental_data(
            location=location,
            latitude=latitude,
            longitude=longitude,
        )

        # Store to InfluxDB as background task
        if background_tasks:
            background_tasks.add_task(write_environmental_data, data)
        else:
            write_environmental_data(data)

        return data

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as error:
        logger.error("Error collecting environmental data: %s", error)
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


@router.get("/historical")
async def historical_environmental_data(
    location: str | None = Query(None, description="Location name, e.g. 'Delhi', 'Indirapuram'"),
    latitude: float | None = Query(None, ge=-90, le=90),
    longitude: float | None = Query(None, ge=-180, le=180),
    range: str = Query("24h", description="Time window, e.g. 1h, 24h, 7d, 30d"),
):
    """
    Query historical measurements from InfluxDB by location name or coordinates.
    """
    if not location and (latitude is None or longitude is None):
        raise HTTPException(
            status_code=400,
            detail="Please provide a location name (e.g. ?location=Delhi) or coordinates to fetch history.",
        )

    resolved_name = location
    lat = latitude
    lon = longitude

    if location and (lat is None or lon is None):
        try:
            lat, lon, resolved_name = await resolve_location(location=location)
        except Exception:
            resolved_name = location

    records = query_historical_environmental_data(
        location=resolved_name,
        latitude=lat,
        longitude=lon,
        range_str=range,
    )

    return {
        "location": {
            "name": resolved_name,
            "latitude": lat,
            "longitude": lon,
        },
        "range": range,
        "count": len(records),
        "data": records,
    }
