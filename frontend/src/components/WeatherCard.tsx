import type { WeatherData } from "../types/weather";

interface WeatherCardProps {
    data: WeatherData | null;
    loading: boolean;
    error: string | null;
}

export default function WeatherCard({ data, loading, error }: WeatherCardProps) {
    if (loading) {
        return (
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm animate-pulse space-y-4">
                <div className="h-4 w-20 bg-slate-200 rounded" />
                <div className="h-10 w-28 bg-slate-200 rounded" />
                <div className="space-y-2 pt-2">
                    <div className="h-4 w-36 bg-slate-100 rounded" />
                    <div className="h-4 w-40 bg-slate-100 rounded" />
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="bg-white rounded-xl border border-rose-200 p-5 shadow-sm">
                <p className="text-sm text-slate-500">Weather</p>
                <p className="mt-3 text-sm text-rose-600">{error}</p>
            </div>
        );
    }

    if (!data) {
        return (
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
                <p className="text-sm text-slate-500">Weather</p>
                <h2 className="text-4xl font-bold mt-2 text-slate-300">-- °C</h2>
                <div className="mt-4 text-sm text-slate-400 space-y-1">
                    <p>Humidity: --%</p>
                    <p>Wind Speed: -- km/h</p>
                </div>
                <p className="text-xs text-slate-400 mt-3">
                    Detect your location to load real-time weather.
                </p>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
            <div className="flex items-start justify-between">
                <div>
                    <p className="text-sm text-slate-500">Current Weather</p>
                    <div className="flex items-center gap-2 mt-1">
                        <h2 className="text-4xl font-bold text-slate-900">
                            {data.temperature !== null ? `${data.temperature}°C` : "--"}
                        </h2>
                        {data.icon && (
                            <img
                                src={`https://openweathermap.org/img/wn/${data.icon}.png`}
                                alt={data.description ?? "Weather icon"}
                                className="w-10 h-10 -my-2"
                            />
                        )}
                    </div>
                    {data.description && (
                        <p className="text-xs text-slate-600 capitalize mt-0.5">
                            {data.description}
                            {data.feels_like !== null ? ` (Feels like ${data.feels_like}°C)` : ""}
                        </p>
                    )}
                </div>

                <span className="text-[11px] font-mono text-slate-400 bg-slate-100 px-2 py-1 rounded-md border border-slate-200">
                    {data.source}
                </span>
            </div>

            {data.location_name && (
                <p className="text-xs text-slate-500 mt-2 flex items-center gap-1">
                    <span>📍</span> {data.location_name}
                </p>
            )}

            <div className="mt-4 grid grid-cols-2 gap-3 pt-3 border-t border-slate-100">
                <div className="bg-slate-50/70 rounded-lg p-2.5 border border-slate-100">
                    <p className="text-xs text-slate-500">Humidity</p>
                    <p className="text-base font-semibold text-slate-900 mt-0.5">
                        {data.humidity !== null ? `${data.humidity}%` : "--"}
                    </p>
                </div>

                <div className="bg-slate-50/70 rounded-lg p-2.5 border border-slate-100">
                    <p className="text-xs text-slate-500">Wind Speed</p>
                    <p className="text-base font-semibold text-slate-900 mt-0.5">
                        {data.wind_speed_kmh !== null ? `${data.wind_speed_kmh} km/h` : "--"}
                    </p>
                </div>
            </div>
        </div>
    );
}
