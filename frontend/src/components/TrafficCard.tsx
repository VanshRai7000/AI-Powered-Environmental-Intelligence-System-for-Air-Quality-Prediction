import type { TrafficData } from "../services/environmentalService";

interface TrafficCardProps {
    data: TrafficData | null;
    loading: boolean;
    error: string | null;
}

function getCongestionBadge(level: string) {
    switch (level) {
        case "Low":
            return "bg-emerald-100 text-emerald-800";
        case "Moderate":
            return "bg-yellow-100 text-yellow-800";
        case "High":
            return "bg-orange-100 text-orange-800";
        case "Severe":
            return "bg-rose-100 text-rose-800";
        default:
            return "bg-slate-100 text-slate-600";
    }
}

export default function TrafficCard({ data, loading, error }: TrafficCardProps) {
    if (loading) {
        return (
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm animate-pulse space-y-4">
                <div className="h-4 w-28 bg-slate-200 rounded" />
                <div className="h-10 w-24 bg-slate-200 rounded" />
                <div className="grid grid-cols-2 gap-3 pt-2">
                    <div className="h-14 bg-slate-100 rounded-lg" />
                    <div className="h-14 bg-slate-100 rounded-lg" />
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="bg-white rounded-xl border border-rose-200 p-5 shadow-sm">
                <p className="text-sm text-slate-500">Traffic Density</p>
                <p className="mt-3 text-sm text-rose-600">{error}</p>
            </div>
        );
    }

    if (!data) {
        return (
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
                <p className="text-sm text-slate-500">Traffic Density</p>
                <h2 className="text-4xl font-bold mt-2 text-slate-300">--%</h2>
                <p className="text-xs text-slate-400 mt-3">
                    Select a location to view nearby road congestion and flow speed.
                </p>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm flex flex-col justify-between">
            <div>
                <div className="flex items-start justify-between">
                    <div>
                        <p className="text-sm text-slate-500">Traffic Congestion</p>
                        <div className="flex items-end gap-3 mt-1">
                            <h2 className="text-4xl font-bold text-slate-900">
                                {data.congestion_percent !== null ? `${data.congestion_percent}%` : "--"}
                            </h2>
                            <span className={`mb-1 px-2.5 py-0.5 rounded-full text-xs font-semibold ${getCongestionBadge(data.congestion_level)}`}>
                                {data.congestion_level}
                            </span>
                        </div>
                    </div>

                    <span className="text-[11px] font-mono text-slate-400 bg-slate-100 px-2 py-1 rounded-md border border-slate-200">
                        TomTom
                    </span>
                </div>

                {data.road_closure && (
                    <div className="mt-2 px-2.5 py-1 rounded-md bg-rose-50 border border-rose-200 text-xs text-rose-700 font-medium">
                        ⚠️ Road closure reported near segment
                    </div>
                )}
            </div>

            <div className="mt-4 grid grid-cols-2 gap-3 pt-3 border-t border-slate-100">
                <div className="bg-slate-50/70 rounded-lg p-2.5 border border-slate-100">
                    <p className="text-xs text-slate-500">Current Speed</p>
                    <p className="text-base font-semibold text-slate-900 mt-0.5">
                        {data.current_speed_kmph !== null ? `${data.current_speed_kmph} km/h` : "--"}
                    </p>
                </div>

                <div className="bg-slate-50/70 rounded-lg p-2.5 border border-slate-100">
                    <p className="text-xs text-slate-500">Free-Flow Speed</p>
                    <p className="text-base font-semibold text-slate-900 mt-0.5">
                        {data.free_flow_speed_kmph !== null ? `${data.free_flow_speed_kmph} km/h` : "--"}
                    </p>
                </div>
            </div>
        </div>
    );
}

