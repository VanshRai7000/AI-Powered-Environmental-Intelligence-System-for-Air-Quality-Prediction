export interface WeatherData {
    latitude: number;
    longitude: number;
    location_name: string | null;
    temperature: number | null;
    feels_like: number | null;
    humidity: number | null;
    wind_speed_kmh: number | null;
    description: string | null;
    icon: string | null;
    source: string;
}

