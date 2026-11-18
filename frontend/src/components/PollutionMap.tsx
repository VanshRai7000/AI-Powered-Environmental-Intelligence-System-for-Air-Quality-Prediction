import { useEffect, useState } from "react";
import { MapContainer, TileLayer, Circle, CircleMarker, Marker, Popup, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import type { PollutionStation } from "../types/airQuality";

interface PollutionMapProps {
    center: {
        name: string;
        latitude: number;
        longitude: number;
    } | null;
    currentAqi: number | null;
    stations: PollutionStation[];
    loading: boolean;
    error: string | null;
}

function getAqiColor(aqi: number | null): string {
    if (aqi === null) return "#64748b"; // slate-500
    if (aqi <= 50) return "#10b981";    // emerald-500
    if (aqi <= 100) return "#eab308";   // yellow-500
    if (aqi <= 150) return "#f97316";   // orange-500
    if (aqi <= 200) return "#ef4444";   // red-500
    if (aqi <= 300) return "#a855f7";   // purple-500
    return "#be123c";                   // rose-700
}

function getAqiLabel(aqi: number | null): string {
    if (aqi === null) return "N/A";
    if (aqi <= 50) return "Good";
    if (aqi <= 100) return "Moderate";
    if (aqi <= 150) return "Unhealthy (SG)";
    if (aqi <= 200) return "Unhealthy";
    if (aqi <= 300) return "Very Unhealthy";
    return "Hazardous";
}

// Custom SVG pin icon for the user's selected location so Vite never breaks image paths
const userLocationIcon = L.divIcon({
    className: "custom-user-pin",
    html: `<div style="width:18px;height:18px;border-radius:9999px;background:#0f172a;border:3px solid #ffffff;box-shadow:0 2px 8px rgba(0,0,0,0.4);"></div>`,
    iconSize: [18, 18],
    iconAnchor: [9, 9],
});

function MapRecenter({ lat, lon }: { lat: number; lon: number }) {
    const map = useMap();
    useEffect(() => {
        map.setView([lat, lon], 10, { animate: true });
    }, [lat, lon, map]);
    return null;
}

export default function PollutionMap({
    center,
    currentAqi,
    stations,
    loading,
    error,
}: PollutionMapProps) {
    const [selectedStation, setSelectedStation] = useState<PollutionStation | null>(null);

    useEffect(() => {
        setSelectedStation(null);
    }, [center?.latitude, center?.longitude]);

    if (loading) {
        return (
            <div className="bg-white border border-slate-200/80 rounded-xl p-6 shadow-sm animate-pulse">
                <div className="h-5 w-48 bg-slate-200 rounded mb-4" />
                <div className="h-80 bg-slate-100 rounded-xl" />
            </div>
        );
    }

    if (error) {
        return (
            <div className="bg-white border border-rose-200 rounded-xl p-6 shadow-sm">
                <h2 className="text-base font-semibold text-slate-900">Interactive Pollution Map</h2>
                <p className="mt-2 text-sm text-rose-600">{error}</p>
            </div>
        );
    }

    if (!center) {
        return (
            <div className="bg-white border border-slate-200/80 rounded-xl p-6 shadow-sm">
                <div className="flex items-center justify-between pb-4 border-b border-slate-100">
                    <div>
                        <h2 className="text-base font-semibold text-slate-900">
                            Interactive Pollution Map
                        </h2>
                        <p className="text-xs text-slate-500 mt-0.5">
                            Explore selected location AQI zone and nearby monitoring stations
                        </p>
                    </div>
                </div>
                <div className="mt-6 h-64 flex flex-col items-center justify-center border border-dashed border-slate-200 rounded-xl bg-slate-50/50 text-center px-4">
                    <span className="text-2xl mb-2">🗺️</span>
                    <p className="text-sm font-medium text-slate-700">No location selected</p>
                    <p className="text-xs text-slate-400 mt-1">
                        Search for a city or detect GPS above to render the pollution map and nearby sensors.
                    </p>
                </div>
            </div>
        );
    }

    const zoneColor = getAqiColor(currentAqi);

    return (
        <section className="bg-white border border-slate-200/80 rounded-xl p-6 shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-100">
                <div>
                    <h2 className="text-base font-semibold text-slate-900">
                        Interactive Pollution Map
                    </h2>
                    <p className="text-xs text-slate-500 mt-0.5">
                        Showing <span className="font-medium text-slate-700">{center.name}</span> and{" "}
                        {stations.length} regional monitoring {stations.length === 1 ? "station" : "stations"}
                    </p>
                </div>

                {/* Legend */}
                <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-500">
                    <span className="inline-flex items-center gap-1">
                        <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" /> Good
                    </span>
                    <span className="inline-flex items-center gap-1">
                        <span className="w-2.5 h-2.5 rounded-full bg-yellow-500" /> Moderate
                    </span>
                    <span className="inline-flex items-center gap-1">
                        <span className="w-2.5 h-2.5 rounded-full bg-orange-500" /> SG
                    </span>
                    <span className="inline-flex items-center gap-1">
                        <span className="w-2.5 h-2.5 rounded-full bg-red-500" /> Unhealthy
                    </span>
                    <span className="inline-flex items-center gap-1">
                        <span className="w-2.5 h-2.5 rounded-full bg-purple-500" /> Very Unhealthy
                    </span>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                {/* Leaflet Map */}
                <div className="lg:col-span-2 h-80 sm:h-96 rounded-xl overflow-hidden border border-slate-200 z-0">
                    <MapContainer
                        center={[center.latitude, center.longitude]}
                        zoom={10}
                        scrollWheelZoom={true}
                        style={{ height: "100%", width: "100%" }}
                    >
                        <TileLayer
                            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                        />
                        <MapRecenter lat={center.latitude} lon={center.longitude} />

                        {/* User Selected Location AQI Impact Zone */}
                        <Circle
                            center={[center.latitude, center.longitude]}
                            radius={8000}
                            pathOptions={{
                                color: zoneColor,
                                fillColor: zoneColor,
                                fillOpacity: 0.18,
                                weight: 2,
                            }}
                        />

                        {/* User Location Pin */}
                        <Marker position={[center.latitude, center.longitude]} icon={userLocationIcon}>
                            <Popup>
                                <div className="text-xs space-y-1">
                                    <p className="font-bold text-slate-900">{center.name}</p>
                                    <p className="text-slate-600">
                                        Current AQI:{" "}
                                        <span className="font-bold" style={{ color: zoneColor }}>
                                            {currentAqi !== null ? Math.round(currentAqi) : "--"} ({getAqiLabel(currentAqi)})
                                        </span>
                                    </p>
                                    <p className="font-mono text-[10px] text-slate-400">
                                        {center.latitude.toFixed(4)}, {center.longitude.toFixed(4)}
                                    </p>
                                </div>
                            </Popup>
                        </Marker>

                        {/* Nearby Monitoring Stations */}
                        {stations.map((st) => {
                            const stColor = getAqiColor(st.aqi);
                            return (
                                <CircleMarker
                                    key={st.id}
                                    center={[st.latitude, st.longitude]}
                                    radius={9}
                                    pathOptions={{
                                        color: "#ffffff",
                                        weight: 2,
                                        fillColor: stColor,
                                        fillOpacity: 0.9,
                                    }}
                                    eventHandlers={{
                                        click: () => setSelectedStation(st),
                                    }}
                                >
                                    <Popup>
                                        <div className="text-xs space-y-1 min-w-[160px]">
                                            <p className="font-semibold text-slate-900">{st.name}</p>
                                            <div className="flex items-center justify-between">
                                                <span className="text-slate-500">Source: {st.source}</span>
                                                {st.aqi !== null && (
                                                    <span
                                                        className="px-1.5 py-0.5 rounded text-white font-bold text-[10px]"
                                                        style={{ backgroundColor: stColor }}
                                                    >
                                                        AQI {Math.round(st.aqi)}
                                                    </span>
                                                )}
                                            </div>
                                            {st.parameters && st.parameters.length > 0 && (
                                                <p className="text-[10px] text-slate-500">
                                                    Sensors: {st.parameters.join(", ")}
                                                </p>
                                            )}
                                            {st.last_updated && (
                                                <p className="text-[10px] text-slate-400">
                                                    Updated: {new Date(st.last_updated).toLocaleString()}
                                                </p>
                                            )}
                                        </div>
                                    </Popup>
                                </CircleMarker>
                            );
                        })}
                    </MapContainer>
                </div>

                {/* Station Info Panel */}
                <div className="bg-slate-50/70 border border-slate-200/80 rounded-xl p-4 flex flex-col max-h-96">
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500 pb-2 border-b border-slate-200">
                        Monitoring Stations ({stations.length})
                    </h3>

                    {selectedStation && (
                        <div className="mt-3 p-3 bg-white rounded-lg border border-slate-200 shadow-sm space-y-1">
                            <div className="flex items-center justify-between gap-2">
                                <span className="text-xs font-bold text-slate-900 truncate">
                                    {selectedStation.name}
                                </span>
                                <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 font-mono">
                                    {selectedStation.source}
                                </span>
                            </div>
                            <p className="text-xs text-slate-600">
                                AQI:{" "}
                                <span className="font-bold">
                                    {selectedStation.aqi !== null ? Math.round(selectedStation.aqi) : "N/A"}
                                </span>
                            </p>
                            {selectedStation.last_updated && (
                                <p className="text-[10px] text-slate-400">
                                    {new Date(selectedStation.last_updated).toLocaleString()}
                                </p>
                            )}
                        </div>
                    )}

                    <div className="mt-3 flex-1 overflow-y-auto space-y-2 pr-1">
                        {stations.length === 0 ? (
                            <p className="text-xs text-slate-400 py-6 text-center">
                                No physical ground stations found within ~60 km. Satellite grid data (OpenWeatherMap) is active for this location.
                            </p>
                        ) : (
                            stations.map((st) => {
                                const stColor = getAqiColor(st.aqi);
                                const isSelected = selectedStation?.id === st.id;
                                return (
                                    <button
                                        key={st.id}
                                        type="button"
                                        onClick={() => setSelectedStation(st)}
                                        className={`w-full text-left p-2.5 rounded-lg border transition-all cursor-pointer flex items-center justify-between gap-2 ${
                                            isSelected
                                                ? "bg-white border-slate-400 shadow-sm"
                                                : "bg-white/70 border-slate-200/70 hover:bg-white"
                                        }`}
                                    >
                                        <div className="min-w-0">
                                            <p className="text-xs font-medium text-slate-800 truncate">
                                                {st.name}
                                            </p>
                                            <p className="text-[10px] text-slate-400">
                                                {st.source} • {st.latitude.toFixed(2)}, {st.longitude.toFixed(2)}
                                            </p>
                                        </div>
                                        <span
                                            className="shrink-0 text-[11px] font-bold px-2 py-0.5 rounded-full text-white"
                                            style={{ backgroundColor: stColor }}
                                        >
                                            {st.aqi !== null ? Math.round(st.aqi) : "Sensor"}
                                        </span>
                                    </button>
                                );
                            })
                        )}
                    </div>
                </div>
            </div>
        </section>
    );
}

