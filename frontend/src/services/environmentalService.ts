import { api } from "./api";
import type { AirQualityData } from "../types/airQuality";
import type { WeatherData } from "../types/weather";

export interface TrafficData {
    current_speed_kmph: number | null;
    free_flow_speed_kmph: number | null;
    current_travel_time_sec: number | null;
    free_flow_travel_time_sec: number | null;
    confidence: number | null;
    road_closure: boolean | null;
    congestion_percent: number | null;
    congestion_level: string;
    timestamp: string;
}

export interface EnvironmentalData {
    location: {
        name: string;
        latitude: number;
        longitude: number;
    };
    air_quality: AirQualityData | null;
    weather: WeatherData | null;
    traffic: TrafficData | null;
    collected_at: string;
}

export interface HistoricalRecord {
    timestamp: string;
    location_name: string | null;
    aqi: number | null;
    temperature: number | null;
    humidity: number | null;
    wind_speed_kmh: number | null;
    congestion_percent: number | null;
    pm2_5: number | null;
    pm10: number | null;
    no2: number | null;
    o3: number | null;
    co: number | null;
    so2: number | null;
}

export interface HistoricalResponse {
    location: {
        name: string | null;
        latitude: number | null;
        longitude: number | null;
    };
    range: string;
    count: number;
    data: HistoricalRecord[];
}

export async function fetchEnvironmentalData(
    locationOrLat: string | number,
    longitude?: number
): Promise<EnvironmentalData> {
    const params: Record<string, unknown> = {};
    if (typeof locationOrLat === "string") {
        params.location = locationOrLat;
    } else {
        params.latitude = locationOrLat;
        params.longitude = longitude;
    }

    const response = await api.get<EnvironmentalData>("/api/environmental/current", { params });
    return response.data;
}

export async function fetchHistoricalData(
    locationOrLat: string | number,
    longitude?: number,
    range: string = "24h"
): Promise<HistoricalResponse> {
    const params: Record<string, unknown> = { range };
    if (typeof locationOrLat === "string") {
        params.location = locationOrLat;
    } else {
        params.latitude = locationOrLat;
        params.longitude = longitude;
    }

    const response = await api.get<HistoricalResponse>("/api/environmental/historical", { params });
    return response.data;
}
