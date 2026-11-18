// import React from "react";
import AQICard from "../components/AQICard";
import WeatherCard from "../components/WeatherCard";
import TrafficCard from "../components/TrafficCard";
import type { AirQualityData } from "../types/airQuality";
import type { WeatherData } from "../types/weather";
import type { TrafficData } from "../services/environmentalService";

interface EnvironmentalGridProps {
    airQuality: AirQualityData | null;
    weather: WeatherData | null;
    traffic: TrafficData | null;
    loading: boolean;
    error: string | null;
}

export default function EnvironmentalGrid({
    airQuality,
    weather,
    traffic,
    loading,
    error,
}: EnvironmentalGridProps) {
    return (
        <div id="air-quality" className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="transition-all hover:shadow-md rounded-xl">
                <AQICard data={airQuality} loading={loading} error={error} />
            </div>
            <div className="transition-all hover:shadow-md rounded-xl">
                <WeatherCard data={weather} loading={loading} error={error} />
            </div>
            <div className="transition-all hover:shadow-md rounded-xl md:col-span-2 lg:col-span-1">
                <TrafficCard data={traffic} loading={loading} error={error} />
            </div>
        </div>
    );
}