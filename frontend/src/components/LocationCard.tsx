import { useState, useEffect, useRef } from "react";
import { getCurrentLocation } from "../services/locationService";
import { sendLocation, searchLocations } from "../services/locationApi";
import type { LocationSearchResult } from "../types/location";

interface LocationCardProps {
    /** Called once valid coordinates are obtained */
    onLocationDetected: (lat: number, lon: number, locationName?: string) => void;
}

export default function LocationCard({ onLocationDetected }: LocationCardProps) {
    const [latitude, setLatitude] = useState<number | null>(null);
    const [longitude, setLongitude] = useState<number | null>(null);
    const [selectedName, setSelectedName] = useState<string | null>(null);
    const [message, setMessage] = useState("Enter your city or click 'Detect GPS' for automated lookup.");
    const [gpsLoading, setGpsLoading] = useState(false);

    // Search state
    const [query, setQuery] = useState("");
    const [searchLoading, setSearchLoading] = useState(false);
    const [suggestions, setSuggestions] = useState<LocationSearchResult[]>([]);
    const [showSuggestions, setShowSuggestions] = useState(false);
    const searchContainerRef = useRef<HTMLDivElement>(null);

    // Close suggestions if clicking outside
    useEffect(() => {
        function handleClickOutside(e: MouseEvent) {
            if (searchContainerRef.current && !searchContainerRef.current.contains(e.target as Node)) {
                setShowSuggestions(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    // Perform location search
    const handleSearch = async (e?: React.FormEvent) => {
        if (e) e.preventDefault();
        const trimmed = query.trim();
        if (trimmed.length < 2) return;

        setSearchLoading(true);
        try {
            const results = await searchLocations(trimmed);
            setSuggestions(results);
            setShowSuggestions(true);
            if (results.length === 0) {
                setMessage(`No matching locations found for "${trimmed}". Try a nearby city name.`);
            }
        } catch {
            setMessage("Failed to search location. Please check your network or try again.");
        } finally {
            setSearchLoading(false);
        }
    };

    // User chooses a search suggestion
    const handleSelectLocation = async (item: LocationSearchResult) => {
        setLatitude(item.latitude);
        setLongitude(item.longitude);
        setSelectedName(item.display_name);
        setQuery(item.name);
        setShowSuggestions(false);
        setMessage(`Location set to ${item.display_name}.`);

        try {
            await sendLocation({
                latitude: item.latitude,
                longitude: item.longitude,
            });
        } catch {
            // non-fatal
        }

        onLocationDetected(item.latitude, item.longitude, item.display_name);
    };

    // Browser GPS detection
    const detectLocation = async () => {
        setGpsLoading(true);
        setMessage("Requesting browser GPS permission...");

        try {
            const location = await getCurrentLocation();

            setLatitude(location.latitude);
            setLongitude(location.longitude);
            setSelectedName(null);
            setMessage("Browser location detected.");

            await sendLocation({
                latitude: location.latitude,
                longitude: location.longitude,
            });

            onLocationDetected(location.latitude, location.longitude);
        } catch (error: any) {
            setMessage(error?.message ?? "Unable to retrieve browser GPS.");
        } finally {
            setGpsLoading(false);
        }
    };

    return (
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
                <div>
                    <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                        Active Monitoring Location
                    </p>
                    <h3 className="text-lg font-bold text-slate-900 mt-0.5 flex items-center gap-2">
                        {selectedName ? (
                            <>
                                <span className="text-emerald-600">📍</span>
                                <span>{selectedName}</span>
                            </>
                        ) : latitude !== null && longitude !== null ? (
                            <>
                                <span className="text-emerald-600">📍</span>
                                <span>GPS Coordinates Active</span>
                            </>
                        ) : (
                            <span className="text-slate-400 font-normal text-base">No location selected yet</span>
                        )}
                    </h3>

                    {latitude !== null && longitude !== null && (
                        <div className="flex items-center gap-3 mt-1 text-xs text-slate-500 font-mono">
                            <span>Lat: {latitude.toFixed(5)}</span>
                            <span>•</span>
                            <span>Lon: {longitude.toFixed(5)}</span>
                        </div>
                    )}
                </div>

                {/* GPS Detect Button */}
                <button
                    type="button"
                    onClick={detectLocation}
                    disabled={gpsLoading}
                    className="inline-flex items-center gap-2 px-3.5 py-2 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 border border-slate-200 rounded-lg transition-colors disabled:opacity-50 cursor-pointer self-start sm:self-auto shrink-0"
                    title="Detect approximate location via browser"
                >
                    {gpsLoading ? (
                        <>
                            <svg className="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                            </svg>
                            <span>Detecting...</span>
                        </>
                    ) : (
                        <>
                            <svg className="w-3.5 h-3.5 text-slate-500" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M12 11c0-1.657-1.343-3-3-3S6 9.343 6 11c0 2.21 3 5 3 5s3-2.79 3-5zM21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            <span>Detect GPS</span>
                        </>
                    )}
                </button>
            </div>

            {/* City / Locality Search Bar */}
            <div ref={searchContainerRef} className="relative">
                <form onSubmit={handleSearch} className="flex gap-2">
                    <div className="relative flex-1">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                            </svg>
                        </div>
                        <input
                            type="text"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            onFocus={() => {
                                if (suggestions.length > 0) setShowSuggestions(true);
                            }}
                            placeholder="Type exact city, suburb, or neighborhood (e.g. Indirapuram, Whitefield, Bandra)..."
                            className="w-full pl-9 pr-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900/10 focus:border-slate-400 transition-all text-slate-900 placeholder:text-slate-400"
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={searchLoading || query.trim().length < 2}
                        className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-lg transition-colors disabled:opacity-40 cursor-pointer shrink-0"
                    >
                        {searchLoading ? "Searching..." : "Set Location"}
                    </button>
                </form>

                {/* Suggestions Dropdown */}
                {showSuggestions && suggestions.length > 0 && (
                    <div className="absolute z-30 mt-1.5 w-full bg-white rounded-lg border border-slate-200 shadow-lg overflow-hidden py-1">
                        {suggestions.map((item, idx) => (
                            <button
                                key={`${item.latitude}-${item.longitude}-${idx}`}
                                type="button"
                                onClick={() => handleSelectLocation(item)}
                                className="w-full text-left px-3.5 py-2.5 hover:bg-slate-50 flex items-center justify-between text-sm transition-colors border-b last:border-b-0 border-slate-100"
                            >
                                <div className="flex items-center gap-2">
                                    <span className="text-slate-400 text-xs">📍</span>
                                    <span className="font-medium text-slate-800">{item.display_name}</span>
                                </div>
                                <span className="text-[11px] font-mono text-slate-400">
                                    {item.latitude.toFixed(2)}, {item.longitude.toFixed(2)}
                                </span>
                            </button>
                        ))}
                    </div>
                )}
            </div>

            {/* Status message */}
            <p className={`text-xs ${
                message.toLowerCase().includes("denied") ||
                message.toLowerCase().includes("unable") ||
                message.toLowerCase().includes("failed") ||
                message.toLowerCase().includes("no matching")
                    ? "text-rose-500"
                    : "text-slate-400"
            }`}>
                {message}
            </p>
        </div>
    );
}
