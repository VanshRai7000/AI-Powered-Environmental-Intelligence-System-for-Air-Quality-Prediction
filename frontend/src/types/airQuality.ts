export interface PollutantReading {
    pollutant: string;
    value: number | null;
    unit: string | null;
}

export interface AirQualityData {
    latitude: number;
    longitude: number;
    aqi: number | null;
    pollutants: PollutantReading[];
    station_name: string | null;
    timestamp: string | null;
    source: string;
}

export interface PollutionStation {
    id: string;
    name: string;
    latitude: number;
    longitude: number;
    aqi: number | null;
    parameters?: string[];
    last_updated: string | null;
    source: string;
}

export interface StationsResponse {
    center: {
        name: string;
        latitude: number;
        longitude: number;
    };
    count: number;
    stations: PollutionStation[];
}
