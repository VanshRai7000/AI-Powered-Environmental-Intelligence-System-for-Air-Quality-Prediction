export interface LocationRequest {
    latitude: number;
    longitude: number;
    accuracy?: number;
}

export interface LocationResponse {
    latitude: number;
    longitude: number;
    accuracy?: number;
    message: string;
}

export interface LocationSearchResult {
    name: string;
    state?: string | null;
    country?: string | null;
    latitude: number;
    longitude: number;
    display_name: string;
}
