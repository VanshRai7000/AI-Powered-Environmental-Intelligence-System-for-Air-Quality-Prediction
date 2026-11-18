import { api } from "./api";
import type { WeatherData } from "../types/weather";

export async function fetchWeather(
    locationOrLat: string | number,
    longitude?: number
): Promise<WeatherData> {
    const params: Record<string, any> = {};
    if (typeof locationOrLat === "string") {
        params.location = locationOrLat;
    } else {
        params.latitude = locationOrLat;
        params.longitude = longitude;
    }

    const response = await api.get<WeatherData>("/api/weather/current", {
        params,
    });
    return response.data;
}
