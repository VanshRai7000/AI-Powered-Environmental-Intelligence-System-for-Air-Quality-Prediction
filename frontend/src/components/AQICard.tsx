import type { AirQualityData } from "../types/airQuality";

interface AQICardProps {
    data: AirQualityData | null;
    loading: boolean;
    error: string | null;
}

// AQI category config
function getAQICategory(aqi: number | null) {
    if (aqi === null) return null;
    if (aqi <= 50)  return { label: "Good",            bg: "bg-emerald-50",  text: "text-emerald-700",  border: "border-emerald-200",  dot: "bg-emerald-500",  badge: "bg-emerald-100 text-emerald-800" };
    if (aqi <= 100) return { label: "Moderate",         bg: "bg-yellow-50",   text: "text-yellow-700",   border: "border-yellow-200",   dot: "bg-yellow-400",   badge: "bg-yellow-100 text-yellow-800"  };
    if (aqi <= 150) return { label: "Unhealthy for SG", bg: "bg-orange-50",   text: "text-orange-700",   border: "border-orange-200",   dot: "bg-orange-500",   badge: "bg-orange-100 text-orange-800"  };
    if (aqi <= 200) return { label: "Unhealthy",        bg: "bg-red-50",      text: "text-red-700",      border: "border-red-200",      dot: "bg-red-500",      badge: "bg-red-100 text-red-800"        };
    if (aqi <= 300) return { label: "Very Unhealthy",   bg: "bg-purple-50",   text: "text-purple-700",   border: "border-purple-200",   dot: "bg-purple-500",   badge: "bg-purple-100 text-purple-800"  };
    return           { label: "Hazardous",              bg: "bg-rose-50",     text: "text-rose-800",     border: "border-rose-300",     dot: "bg-rose-700",     badge: "bg-rose-200 text-rose-900"      };
}

export default function AQICard({ data, loading, error }: AQICardProps) {
    const category = data ? getAQICategory(data.aqi) : null;

    // ── Loading state ──────────────────────────────────────────────────────────
    if (loading) {
        return (
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm animate-pulse space-y-4">
                <div className="h-4 w-24 bg-slate-200 rounded" />
                <div className="h-12 w-20 bg-slate-200 rounded" />
                <div className="grid grid-cols-3 gap-3">
                    {[...Array(6)].map((_, i) => (
                        <div key={i} className="h-14 bg-slate-100 rounded-lg" />
                    ))}
                </div>
            </div>
        );
    }

    // ── Error state ───────────────────────────────────────────────────────────
    if (error) {
        return (
            <div className="bg-white rounded-xl border border-rose-200 p-5 shadow-sm">
                <p className="text-sm text-slate-500">Current AQI</p>
                <p className="mt-3 text-sm text-rose-600">{error}</p>
            </div>
        );
    }

    // ── Empty / waiting state ─────────────────────────────────────────────────
    if (!data) {
        return (
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
                <p className="text-sm text-slate-500">Current AQI</p>
                <h2 className="text-4xl font-bold mt-2 text-slate-300">--</h2>
                <p className="text-sm text-slate-400 mt-2">
                    Detect your location to load air quality data.
                </p>
            </div>
        );
    }

    // ── Data state ────────────────────────────────────────────────────────────
    return (
        <div className={`rounded-xl border p-5 shadow-sm ${category?.bg ?? "bg-white"} ${category?.border ?? "border-slate-200"}`}>

            {/* Header row */}
            <div className="flex items-start justify-between">
                <div>
                    <p className="text-sm text-slate-500">Current AQI</p>
                    <div className="flex items-end gap-3 mt-1">
                        <h2 className={`text-5xl font-bold ${category?.text ?? "text-slate-900"}`}>
                            {data.aqi !== null ? Math.round(data.aqi) : "--"}
                        </h2>
                        {category && (
                            <span className={`mb-1 px-2 py-0.5 rounded-full text-xs font-semibold ${category.badge}`}>
                                {category.label}
                            </span>
                        )}
                    </div>
                </div>

                {/* Source badge */}
                <span className="text-[11px] font-mono text-slate-400 bg-slate-100 px-2 py-1 rounded-md border border-slate-200">
                    {data.source}
                </span>
            </div>

            {/* Station + timestamp */}
            {(data.station_name || data.timestamp) && (
                <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1">
                    {data.station_name && (
                        <p className="text-xs text-slate-500 flex items-center gap-1">
                            <span>📍</span> {data.station_name}
                        </p>
                    )}
                    {data.timestamp && (
                        <p className="text-xs text-slate-400">
                            {new Date(data.timestamp).toLocaleString([], {
                                dateStyle: "medium",
                                timeStyle: "short",
                            })}
                        </p>
                    )}
                </div>
            )}

            {/* Pollutants grid */}
            {data.pollutants.length > 0 && (
                <div className="mt-4 grid grid-cols-3 gap-2">
                    {data.pollutants.map((p) => (
                        <div
                            key={p.pollutant}
                            className="bg-white/70 border border-white rounded-lg px-3 py-2 text-center shadow-sm"
                        >
                            <p className="text-xs font-semibold text-slate-600">{p.pollutant}</p>
                            <p className="text-base font-bold text-slate-900 mt-0.5">
                                {p.value !== null ? p.value : "--"}
                            </p>
                            <p className="text-[10px] text-slate-400">{p.unit ?? ""}</p>
                        </div>
                    ))}
                </div>
            )}

            {/* No pollutants fallback */}
            {data.pollutants.length === 0 && (
                <p className="mt-3 text-xs text-slate-400">
                    No individual pollutant readings available.
                </p>
            )}
        </div>
    );
}
