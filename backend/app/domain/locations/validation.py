from math import isfinite

from .errors import ConfigurationError


def validate_name(name: str, label: str) -> str:
    if not isinstance(name, str) or not name.strip():
        raise ConfigurationError(f"{label} is required.")

    cleaned = name.strip()

    if len(cleaned) > 128:
        raise ConfigurationError(
            f"{label} must not exceed 128 characters."
        )

    return cleaned


def validate_zone(
    name: str,
    low: float,
    high: float,
    schedule: dict,
) -> str:
    cleaned_name = validate_name(name, "Zone name")

    for value in (low, high):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ConfigurationError(
                "Moisture thresholds must be numbers."
            )

        if not isfinite(value) or not 0.0 <= value <= 1.0:
            raise ConfigurationError(
                "Moisture thresholds must be between 0 and 1."
            )

    if low >= high:
        raise ConfigurationError(
            "The low threshold must be less than the high threshold."
        )

    if not isinstance(schedule, dict):
        raise ConfigurationError("Schedule must be an object.")

    return cleaned_name