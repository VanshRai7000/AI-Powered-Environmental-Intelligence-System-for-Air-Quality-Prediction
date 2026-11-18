import httpx
from datetime import datetime, timezone

from app.config.settings import settings


# --------------------------------------------------
# 1. TomTom API Configuration
# --------------------------------------------------

TOMTOM_URL = (
    "https://api.tomtom.com/traffic/services/4/"
    "flowSegmentData/absolute/10/json"
)


# --------------------------------------------------
# 2. Get Traffic Data from TomTom
# --------------------------------------------------

async def get_traffic_data(
    latitude: float,
    longitude: float
):
    api_key = settings.tomtom_api_key.strip()
    if not api_key:
        return {}

    params = {
        "key": api_key,
        "point": f"{latitude},{longitude}",
        "unit": "kmph",
    }

    async with httpx.AsyncClient(timeout=15) as client:

        response = await client.get(
            TOMTOM_URL,
            params=params
        )

        response.raise_for_status()

        data = response.json()

        flow = data.get(
            "flowSegmentData",
            {}
        )

        return flow


# --------------------------------------------------
# 3. Calculate Congestion Percentage
# --------------------------------------------------

def calculate_congestion(
    current_speed,
    free_flow_speed
):

    if (
        current_speed is None
        or free_flow_speed is None
    ):
        return None

    if free_flow_speed <= 0:
        return None

    ratio = 1 - (
        current_speed / free_flow_speed
    )

    # Keep value between 0 and 1
    ratio = max(
        0,
        min(1, ratio)
    )

    return round(
        ratio * 100,
        2
    )


# --------------------------------------------------
# 4. Determine Congestion Level
# --------------------------------------------------

def get_congestion_level(percent):

    if percent is None:
        return "Unknown"

    if percent < 20:
        return "Low"

    if percent < 50:
        return "Moderate"

    if percent < 75:
        return "High"

    return "Severe"


# --------------------------------------------------
# 5. Normalize TomTom Response
# --------------------------------------------------

def normalize_traffic(flow):

    current_speed = flow.get(
        "currentSpeed"
    )

    free_flow_speed = flow.get(
        "freeFlowSpeed"
    )

    congestion = calculate_congestion(
        current_speed,
        free_flow_speed
    )

    return {

        "current_speed_kmph":
            current_speed,

        "free_flow_speed_kmph":
            free_flow_speed,

        "current_travel_time_sec":
            flow.get(
                "currentTravelTime"
            ),

        "free_flow_travel_time_sec":
            flow.get(
                "freeFlowTravelTime"
            ),

        "confidence":
            flow.get(
                "confidence"
            ),

        "road_closure":
            flow.get(
                "roadClosure"
            ),

        "congestion_percent":
            congestion,

        "congestion_level":
            get_congestion_level(
                congestion
            ),

        "timestamp":
            datetime.now(
                timezone.utc
            ).isoformat()
    }