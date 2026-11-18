import type { HistoricalRecord } from "../services/environmentalService";

interface HistoricalAnalyticsProps {
    selectedLoc: { name: string; latitude: number; longitude: number } | null;
    history: HistoricalRecord[];
    loading: boolean;
    activeRange: "1h" | "24h" | "7d" | "30d";
    onRangeChange: (range: "1h" | "24h" | "7d" | "30d") => void;
}

export default function HistoricalAnalytics({
    selectedLoc,
    history,
    loading,
    activeRange,
    onRangeChange,
}: HistoricalAnalyticsProps) {
    const ranges = ["1h", "24h", "7d", "30d"] as const;

    return (
        <section id="analytics" className="bg-white border border-slate-200/80 rounded-xl p-6 shadow-sm">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
                <div>
                    <h2 className="text-base font-semibold text-slate-900">
                        Historical Telemetry (InfluxDB)
                    </h2>
                    <p className="text-xs text-slate-500 mt-0.5">
                        Time-series environmental records stored for{" "}
                        {selectedLoc ? selectedLoc.name : "your selected location"}
                        {history.length > 0 ? ` (${history.length} records)` : ""}
                    </p>
                </div>

                {/* Time Range Selector */}
                <div className="inline-flex rounded-lg bg-slate-100 p-0.5 border border-slate-200/60 text-xs font-medium self-start sm:self-auto">
                    {ranges.map((range) => (
                        <button
                            key={range}
                            type="button"
                            onClick={() => onRangeChange(range)}
                            className={`px-3 py-1 rounded-md transition-all cursor-pointer uppercase ${
                                activeRange === range
                                    ? "bg-white text-slate-900 shadow-sm font-semibold"
                                    : "text-slate-500 hover:text-slate-900"
                            }`}
                        >
                            {range}
                        </button>
                    ))}
                </div>
            </div>

            {loading ? (
                <div className="mt-6 py-10 text-center text-xs text-slate-400 animate-pulse">
                    Querying historical records from InfluxDB...
                </div>
            ) : history.length > 0 ? (
                <div className="mt-4 overflow-x-auto">
                    <table className="w-full text-left border-collapse text-xs">
                        <thead>
                            <tr className="border-b border-slate-200 text-slate-500">
                                <th className="py-2.5 px-3 font-semibold">Timestamp</th>
                                <th className="py-2.5 px-3 font-semibold">Location</th>
                                <th className="py-2.5 px-3 font-semibold">AQI</th>
                                <th className="py-2.5 px-3 font-semibold">PM2.5</th>
                                <th className="py-2.5 px-3 font-semibold">PM10</th>
                                <th className="py-2.5 px-3 font-semibold">Temp</th>
                                <th className="py-2.5 px-3 font-semibold">Humidity</th>
                                <th className="py-2.5 px-3 font-semibold">Traffic</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                            {history.slice(-15).reverse().map((row, idx) => (
                                <tr key={`${row.timestamp}-${idx}`} className="hover:bg-slate-50/70">
                                    <td className="py-2.5 px-3 font-mono text-slate-500 whitespace-nowrap">
                                        {new Date(row.timestamp).toLocaleString([], {
                                            month: "short",
                                            day: "numeric",
                                            hour: "2-digit",
                                            minute: "2-digit",
                                        })}
                                    </td>
                                    <td className="py-2.5 px-3 text-slate-700 font-medium">
                                        {row.location_name ?? "--"}
                                    </td>
                                    <td className="py-2.5 px-3 font-bold text-slate-900">
                                        {row.aqi != null ? Math.round(row.aqi) : "--"}
                                    </td>
                                    <td className="py-2.5 px-3 text-slate-600">
                                        {row.pm2_5 != null ? `${row.pm2_5} µg/m³` : "--"}
                                    </td>
                                    <td className="py-2.5 px-3 text-slate-600">
                                        {row.pm10 != null ? `${row.pm10} µg/m³` : "--"}
                                    </td>
                                    <td className="py-2.5 px-3 text-slate-600">
                                        {row.temperature != null ? `${row.temperature}°C` : "--"}
                                    </td>
                                    <td className="py-2.5 px-3 text-slate-600">
                                        {row.humidity != null ? `${row.humidity}%` : "--"}
                                    </td>
                                    <td className="py-2.5 px-3 text-slate-600">
                                        {row.congestion_percent != null
                                            ? `${row.congestion_percent}%`
                                            : "--"}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            ) : (
                <div className="mt-6 flex flex-col items-center justify-center py-10 px-4 border border-dashed border-slate-200 rounded-xl bg-slate-50/50">
                    <div className="w-10 h-10 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-400 mb-2">
                        📈
                    </div>
                    <h4 className="text-sm font-medium text-slate-800">
                        {selectedLoc
                            ? "No historical records stored yet for this window"
                            : "Waiting for location selection"}
                    </h4>
                    <p className="text-xs text-slate-500 text-center max-w-sm mt-1">
                        Each time you query a location, measurements are stored in InfluxDB and will
                        appear here immediately.
                    </p>
                </div>
            )}
        </section>
    );
}
