from datetime import datetime, timezone


def validate_coordinates(latitude, longitude):

    if not -90 <= latitude <= 90:
        raise ValueError("Invalid latitude")

    if not -180 <= longitude <= 180:
        raise ValueError("Invalid longitude")


def clean_numeric_value(value):

    if value is None:
        return None

    try:
        value = float(value)
    except (TypeError, ValueError):
        return None

    if value < 0:
        return None

    return value


def normalize_timestamp(timestamp):

    if timestamp is None:
        return datetime.now(
            timezone.utc
        ).isoformat()

    return timestamp