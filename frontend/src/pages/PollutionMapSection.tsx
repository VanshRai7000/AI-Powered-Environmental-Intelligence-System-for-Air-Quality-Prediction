import PollutionMap from "../components/PollutionMap"
import type { PollutionStation } from "../types/airQuality";

interface PollutionMapSectionProps {
    selectedLoc: { name: string; latitude: number; longitude: number } | null;
    currentAqi: number | null;
    stations: PollutionStation[];
    loading: boolean;
    error: string | null;
}

export default function PollutionMapSection({
    selectedLoc,
    currentAqi,
    stations,
    loading,
    error,
}: PollutionMapSectionProps) {
    return (
        <div id="pollution-map" className="w-full">
            <PollutionMap
                center={selectedLoc}
                currentAqi={currentAqi}
                stations={stations}
                loading={loading}
                error={error}
            />
        </div>
    );
}