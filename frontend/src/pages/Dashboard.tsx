import { useEffect, useState } from "react";
import Header from "../components/Header";
import Sidebar from "../components/Sidebar";
import LocationCard from "../components/LocationCard";

// Modular section pages
import EnvironmentalGrid from "./EnvironmentalGrid";
import PollutionMapSection from "./PollutionMapSection";
import HistoricalAnalytics from "./HistoricalAnalytics";

import { checkBackendHealth } from "../services/healthService";
import { fetchNearbyStations } from "../services/airQualityService";
import {
    fetchEnvironmentalData,
    fetchHistoricalData,
    type HistoricalRecord,
    type TrafficData,
} from "../services/environmentalService";
import type { AirQualityData, PollutionStation } from "../types/airQuality";
import type { WeatherData } from "../types/weather";

const STATUS_MAP = {
    healthy: {
        badgeBg: "bg-emerald-50 text-emerald-700 border-emerald-200",
        dot: "bg-emerald-500",
        label: "All Systems Operational",
    },
    degraded: {
        badgeBg: "bg-amber-50 text-amber-700 border-amber-200",
        dot: "bg-amber-500",
        label: "Degraded Performance",
    },
    offline: {
        badgeBg: "bg-rose-50 text-rose-700 border-rose-200",
        dot: "bg-rose-500",
        label: "Backend Disconnected",
    },
    checking: {
        badgeBg: "bg-slate-100 text-slate-600 border-slate-200",
        dot: "bg-slate-400 animate-pulse",
        label: "Checking System Health...",
    },
};

const PAGE_TITLES: Record<string, { title: string; subtitle: string }> = {
    overview: {
        title: "Environmental Intelligence Dashboard",
        subtitle: "Real-time AQI, pollutants, weather, road traffic & InfluxDB telemetry",
    },
    "air-quality": {
        title: "Air Quality, Weather & Traffic",
        subtitle: "Detailed pollutant breakdown, meteorological conditions & road congestion",
    },
    "pollution-map": {
        title: "Interactive Pollution Map",
        subtitle: "Explore regional AQI zones and nearby physical monitoring stations",
    },
    analytics: {
        title: "Historical Analytics",
        subtitle: "Time-series environmental records persisted in InfluxDB",
    },
};

export default function Dashboard() {
    const [activeSection, setActiveSection] = useState("overview");

    // ── Health State ──────────────────────────────────────────────────────────
    const [health, setHealth] = useState({
        status: "checking",
        database: "connecting...",
        lastChecked: null as string | null,
    });
    const [isRefreshing, setIsRefreshing] = useState(false);

    // ── Location & Combined Environmental State ───────────────────────────────
    const [selectedLoc, setSelectedLoc] = useState<{
        name: string;
        latitude: number;
        longitude: number;
    } | null>(null);
    const [airQuality, setAirQuality] = useState<AirQualityData | null>(null);
    const [weather, setWeather] = useState<WeatherData | null>(null);
    const [traffic, setTraffic] = useState<TrafficData | null>(null);
    const [envLoading, setEnvLoading] = useState(false);
    const [envError, setEnvError] = useState<string | null>(null);

    // ── Map Stations State ────────────────────────────────────────────────────
    const [stations, setStations] = useState<PollutionStation[]>([]);
    const [stationsLoading, setStationsLoading] = useState(false);
    const [stationsError, setStationsError] = useState<string | null>(null);

    // ── Historical Telemetry State ────────────────────────────────────────────
    const [activeRange, setActiveRange] = useState<"1h" | "24h" | "7d" | "30d">("24h");
    const [history, setHistory] = useState<HistoricalRecord[]>([]);
    const [historyLoading, setHistoryLoading] = useState(false);

    // ── Handlers ──────────────────────────────────────────────────────────────
    const fetchHealth = async () => {
        setIsRefreshing(true);
        try {
            const data = await checkBackendHealth();
            setHealth({
                status: data.status || "healthy",
                database: data.database || "connected",
                lastChecked: new Date().toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                }),
            });
        } catch {
            setHealth({
                status: "offline",
                database: "disconnected",
                lastChecked: new Date().toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                }),
            });
        } finally {
            setIsRefreshing(false);
        }
    };

    const loadHistorical = async (
        target: string | number,
        targetLon: number | undefined,
        range: string
    ) => {
        setHistoryLoading(true);
        try {
            const res = await fetchHistoricalData(target, targetLon, range);
            setHistory(res.data || []);
        } catch {
            setHistory([]);
        } finally {
            setHistoryLoading(false);
        }
    };

    const handleLocationDetected = async (lat: number, lon: number, locationName?: string) => {
        const target = locationName && locationName.trim() ? locationName.trim() : lat;
        const targetLon = typeof target === "string" ? undefined : lon;

        // 1. Fetch unified Environmental Data (AQI + Weather + Traffic) and store in InfluxDB
        setEnvLoading(true);
        setEnvError(null);
        try {
            const env = await fetchEnvironmentalData(target, targetLon);
            const resolvedLoc = {
                name: locationName || env.location.name,
                latitude: env.location.latitude,
                longitude: env.location.longitude,
            };
            setSelectedLoc(resolvedLoc);

            if (env.air_quality) {
                setAirQuality({
                    ...env.air_quality,
                    station_name: resolvedLoc.name,
                });
            } else {
                setAirQuality(null);
            }

            if (env.weather) {
                setWeather({
                    ...env.weather,
                    location_name: resolvedLoc.name,
                });
            } else {
                setWeather(null);
            }

            setTraffic(env.traffic);

            // Refresh historical telemetry after background InfluxDB write finishes
            setTimeout(() => {
                loadHistorical(resolvedLoc.name, undefined, activeRange);
            }, 700);
        } catch (err: any) {
            const detail =
                err?.response?.data?.detail ??
                err?.message ??
                "Failed to fetch environmental data. Make sure the backend server is running.";
            setEnvError(detail);
        } finally {
            setEnvLoading(false);
        }

        // 2. Fetch Nearby Monitoring Stations for the Interactive Map
        setStationsLoading(true);
        setStationsError(null);
        try {
            const stRes = await fetchNearbyStations(target, targetLon);
            setStations(stRes.stations || []);
        } catch (err: any) {
            setStationsError(
                err?.response?.data?.detail ?? "Unable to load nearby monitoring stations."
            );
            setStations([]);
        } finally {
            setStationsLoading(false);
        }
    };

    const handleRangeChange = (range: "1h" | "24h" | "7d" | "30d") => {
        setActiveRange(range);
        if (selectedLoc) {
            loadHistorical(selectedLoc.name, undefined, range);
        }
    };

    const handleSelectSection = (sectionId: string) => {
        setActiveSection(sectionId);
    };

    useEffect(() => {
        fetchHealth();
    }, []);

    const statusConfig = STATUS_MAP[health.status as keyof typeof STATUS_MAP] || STATUS_MAP.healthy;
    const pageMeta = PAGE_TITLES[activeSection] || PAGE_TITLES.overview;

    return (
        <div className="min-h-screen bg-slate-50/60 font-sans text-slate-900 flex">
            <Sidebar activeSection={activeSection} onSelectSection={handleSelectSection} />

            <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
                <Header />

                <main className="flex-1 overflow-y-auto px-6 py-8 max-w-7xl w-full mx-auto space-y-6">
                    {/* Top Bar */}
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-slate-200/80">
                        <div>
                            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
                                {pageMeta.title}
                            </h1>
                            <p className="text-sm text-slate-500 mt-1">{pageMeta.subtitle}</p>
                        </div>

                        <div className="flex flex-wrap items-center gap-3">
                            {health.lastChecked && (
                                <span className="text-xs text-slate-400 hidden md:inline">
                                    Updated {health.lastChecked}
                                </span>
                            )}

                            <button
                                type="button"
                                onClick={fetchHealth}
                                disabled={isRefreshing}
                                className="inline-flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 hover:text-slate-900 transition-colors shadow-sm disabled:opacity-50 cursor-pointer"
                            >
                                <svg
                                    className={`w-3.5 h-3.5 ${isRefreshing ? "animate-spin" : ""}`}
                                    fill="none"
                                    stroke="currentColor"
                                    strokeWidth="2"
                                    viewBox="0 0 24 24"
                                >
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                                    />
                                </svg>
                                {isRefreshing ? "Syncing..." : "Refresh"}
                            </button>

                            <div
                                className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs font-medium shadow-sm ${statusConfig.badgeBg}`}
                            >
                                <span className={`h-2 w-2 rounded-full ${statusConfig.dot}`} />
                                <span>{statusConfig.label}</span>
                                <span className="text-slate-300 font-normal">|</span>
                                <span className="font-mono text-[11px] opacity-80">
                                    DB: {health.database}
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* Mobile Page Switcher */}
                    <div className="flex md:hidden flex-wrap gap-2">
                        {[
                            { id: "overview", label: "📊 Dashboard" },
                            { id: "air-quality", label: "🌬️ Air & Weather" },
                            { id: "pollution-map", label: "🗺️ Map" },
                            { id: "analytics", label: "📈 History" },
                        ].map((tab) => (
                            <button
                                key={tab.id}
                                type="button"
                                onClick={() => setActiveSection(tab.id)}
                                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer ${
                                    activeSection === tab.id
                                        ? "bg-slate-900 text-white"
                                        : "bg-white border border-slate-200 text-slate-600"
                                }`}
                            >
                                {tab.label}
                            </button>
                        ))}
                    </div>

                    {/* Global API Error Banner */}
                    {envError && (
                        <div className="bg-rose-50 border border-rose-200 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                            <div className="flex items-center gap-2.5 text-sm text-rose-700">
                                <span>⚠️</span>
                                <span>{envError}</span>
                            </div>
                            {selectedLoc && (
                                <button
                                    type="button"
                                    onClick={() =>
                                        handleLocationDetected(
                                            selectedLoc.latitude,
                                            selectedLoc.longitude,
                                            selectedLoc.name
                                        )
                                    }
                                    className="px-3 py-1.5 bg-rose-600 text-white text-xs font-medium rounded-lg hover:bg-rose-700 transition-colors cursor-pointer self-start sm:self-auto"
                                >
                                    Retry
                                </button>
                            )}
                        </div>
                    )}

                    {/* Persistent Location Card across all pages */}
                    <div className="transition-all hover:shadow-md rounded-xl">
                        <LocationCard onLocationDetected={handleLocationDetected} />
                    </div>

                    {/* Page Content Switcher */}
                    {(activeSection === "overview" || activeSection === "air-quality") && (
                        <EnvironmentalGrid
                            airQuality={airQuality}
                            weather={weather}
                            traffic={traffic}
                            loading={envLoading}
                            error={envError}
                        />
                    )}

                    {(activeSection === "overview" || activeSection === "pollution-map") && (
                        <PollutionMapSection
                            selectedLoc={selectedLoc}
                            currentAqi={airQuality?.aqi ?? null}
                            stations={stations}
                            loading={stationsLoading}
                            error={stationsError}
                        />
                    )}

                    {(activeSection === "overview" || activeSection === "analytics") && (
                        <HistoricalAnalytics
                            selectedLoc={selectedLoc}
                            history={history}
                            loading={historyLoading}
                            activeRange={activeRange}
                            onRangeChange={handleRangeChange}
                        />
                    )}
                </main>
            </div>
        </div>
    );
}
