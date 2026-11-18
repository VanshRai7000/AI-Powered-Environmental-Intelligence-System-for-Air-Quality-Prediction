import pytest
import respx
import httpx

from app.services.traffic_service import (
    get_traffic_data,
    calculate_congestion,
    get_congestion_level,
    normalize_traffic,
    TOMTOM_URL,
)


def test_calculate_congestion():
    # Normal case: current 30, free-flow 60 -> 50% congestion
    assert calculate_congestion(30, 60) == 50.0

    # Free flow: current 60, free-flow 60 -> 0% congestion
    assert calculate_congestion(60, 60) == 0.0

    # Gridlock: current 0, free-flow 60 -> 100% congestion
    assert calculate_congestion(0, 60) == 100.0

    # Current speed higher than free flow
    assert calculate_congestion(70, 60) == 0.0

    # Edge cases
    assert calculate_congestion(None, 60) is None
    assert calculate_congestion(30, None) is None
    assert calculate_congestion(30, 0) is None


def test_get_congestion_level():
    assert get_congestion_level(10) == "Low"
    assert get_congestion_level(35) == "Moderate"
    assert get_congestion_level(60) == "High"
    assert get_congestion_level(85) == "Severe"
    assert get_congestion_level(None) == "Unknown"


def test_normalize_traffic():
    raw_flow = {
        "currentSpeed": 25,
        "freeFlowSpeed": 50,
        "currentTravelTime": 120,
        "freeFlowTravelTime": 60,
        "confidence": 0.95,
        "roadClosure": False,
    }
    result = normalize_traffic(raw_flow)
    assert result["current_speed_kmph"] == 25
    assert result["free_flow_speed_kmph"] == 50
    assert result["congestion_percent"] == 50.0
    assert result["congestion_level"] == "High"
    assert result["confidence"] == 0.95
    assert result["timestamp"] is not None


@pytest.mark.asyncio
@respx.mock
async def test_traffic_api_success():
    respx.get(TOMTOM_URL).respond(
        200,
        json={
            "flowSegmentData": {
                "currentSpeed": 35,
                "freeFlowSpeed": 50,
                "currentTravelTime": 180,
                "freeFlowTravelTime": 120,
                "confidence": 0.88,
                "roadClosure": False,
            }
        },
    )

    flow = await get_traffic_data(28.6139, 77.2090)
    assert flow["currentSpeed"] == 35
    assert flow["freeFlowSpeed"] == 50


@pytest.mark.asyncio
@respx.mock
async def test_traffic_api_invalid_credentials_403():
    respx.get(TOMTOM_URL).respond(403, json={"error": "Forbidden: Invalid Key"})

    with pytest.raises(httpx.HTTPStatusError):
        await get_traffic_data(28.6139, 77.2090)


@pytest.mark.asyncio
@respx.mock
async def test_traffic_api_rate_limit_429():
    respx.get(TOMTOM_URL).respond(429, json={"error": "Too Many Requests"})

    with pytest.raises(httpx.HTTPStatusError):
        await get_traffic_data(28.6139, 77.2090)


@pytest.mark.asyncio
@respx.mock
async def test_traffic_api_timeout():
    respx.get(TOMTOM_URL).mock(side_effect=httpx.TimeoutException("Connection timed out"))

    with pytest.raises(httpx.TimeoutException):
        await get_traffic_data(28.6139, 77.2090)
