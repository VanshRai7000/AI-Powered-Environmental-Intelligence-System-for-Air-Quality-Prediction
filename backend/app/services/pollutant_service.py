"""
Pollutant data processing utilities.

Responsibilities:
- Validate individual pollutant readings (value, unit, timestamp).
- Normalise inconsistent unit strings from different external providers.
- Merge / deduplicate readings from multiple sources.
- Filter out invalid or obviously erroneous data points.
"""

from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Unit normalisation map
# Maps raw strings from external APIs → canonical unit label
# ---------------------------------------------------------------------------
UNIT_ALIASES: dict[str, str] = {
    # Micrograms per cubic metre
    "µg/m³": "µg/m³",
    "ug/m3": "µg/m³",
    "μg/m3": "µg/m³",
    "micrograms/m3": "µg/m³",
    # Parts per billion
    "ppb": "ppb",
    "PPB": "ppb",
    # Parts per million
    "ppm": "ppm",
    "PPM": "ppm",
    # AQI (dimensionless index value)
    "aqi": "AQI",
    "AQI": "AQI",
}

# Reasonable upper bounds per pollutant label (for sanity-check filtering)
POLLUTANT_MAX: dict[str, float] = {
    "PM2.5": 1000.0,
    "PM10":  2000.0,
    "NO2":   2000.0,
    "O3":    500.0,
    "CO":    100.0,
    "SO2":   1000.0,
}


def normalize_pollutant(
    pollutant: str,
    value: float | None,
    unit: str | None,
) -> dict | None:
    """
    Validate and normalise a single pollutant reading.

    Returns a clean dict or None if the reading should be discarded.
    """
    if pollutant is None or not str(pollutant).strip():
        return None

    # Value checks
    if value is None:
        return None

    try:
        value = float(value)
    except (TypeError, ValueError):
        return None

    if value < 0:
        return None

    label = str(pollutant).strip()
    max_allowed = POLLUTANT_MAX.get(label)
    if max_allowed is not None and value > max_allowed:
        return None

    # Unit normalisation
    normalised_unit = _normalise_unit(unit)

    return {
        "pollutant": label,
        "value": round(value, 4),
        "unit": normalised_unit,
    }


def normalize_pollutants(readings: list[dict]) -> list[dict]:
    """
    Normalise a list of raw pollutant dicts.
    Each dict must have keys: pollutant, value, unit.
    Invalid entries are dropped silently.
    """
    result = []
    for reading in readings:
        clean = normalize_pollutant(
            reading.get("pollutant"),
            reading.get("value"),
            reading.get("unit"),
        )
        if clean is not None:
            result.append(clean)
    return result


def validate_timestamp(raw_timestamp: str | None) -> str | None:
    """
    Validate and normalise a timestamp string to ISO 8601 UTC.
    Returns the original string if it cannot be parsed (best-effort).
    Returns None if input is None or empty.
    """
    if not raw_timestamp:
        return None

    formats = [
        "%Y-%m-%dT%H:%M:%S%z",   # ISO with tz offset
        "%Y-%m-%dT%H:%M:%SZ",    # ISO with explicit Z
        "%Y-%m-%dT%H:%M:%S",     # ISO without tz
        "%Y-%m-%d %H:%M:%S",     # space-separated
        "%Y-%m-%d",               # date only
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(raw_timestamp.strip(), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.isoformat()
        except ValueError:
            continue

    # Return original string as a best-effort fallback
    return raw_timestamp


def merge_pollutant_readings(
    primary: list[dict],
    secondary: list[dict],
) -> list[dict]:
    """
    Merge two lists of normalised pollutant readings.
    Primary source wins when the same pollutant appears in both.
    """
    seen: dict[str, dict] = {}

    for reading in primary:
        name = reading.get("pollutant", "")
        if name:
            seen[name] = reading

    for reading in secondary:
        name = reading.get("pollutant", "")
        if name and name not in seen:
            seen[name] = reading

    return list(seen.values())


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _normalise_unit(unit: str | None) -> str | None:
    if unit is None:
        return None
    cleaned = unit.strip()
    return UNIT_ALIASES.get(cleaned, cleaned) or None
