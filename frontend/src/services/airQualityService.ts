import { api } from "./api";
import type { AirQualityData, StationsResponse } from "../types/airQuality";

export async function fetchAirQuality(
    locationOrLat: string | number,
    longitude?: number
): Promise<AirQualityData> {
    const params: Record<string, unknown> = {};
    if (typeof locationOrLat === "string") {
        params.location = locationOrLat;
    } else {
        params.latitude = locationOrLat;
        params.longitude = longitude;
    }

    const response = await api.get<AirQualityData>("/api/air-quality/current", {
        params,
    });
    return response.data;
}

export async function fetchNearbyStations(
    locationOrLat: string | number,
    longitude?: number
): Promise<StationsResponse> {
    const params: Record<string, unknown> = {};
    if (typeof locationOrLat === "string") {
        params.location = locationOrLat;
    } else {
        params.latitude = locationOrLat;
        params.longitude = longitude;
    }

    const response = await api.get<StationsResponse>("/api/air-quality/stations", {
        params,
    });
    return response.data;
}
