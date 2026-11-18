import { api } from "./api";
import type {
    LocationRequest,
    LocationResponse,
    LocationSearchResult,
} from "../types/location";

export async function sendLocation(
    location: LocationRequest
): Promise<LocationResponse> {
    const response = await api.post<LocationResponse>(
        "/api/location",
        location
    );
    return response.data;
}

export async function searchLocations(
    query: string
): Promise<LocationSearchResult[]> {
    const response = await api.get<LocationSearchResult[]>(
        "/api/location/search",
        { params: { query } }
    );
    return response.data;
}
