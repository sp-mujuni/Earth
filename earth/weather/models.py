"""Validated, provider-neutral weather domain models."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from math import isfinite


def _utc(value: datetime, field: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _number(value: float | None, field: str, low: float | None = None,
            high: float | None = None) -> None:
    if value is None:
        return
    if not isfinite(value):
        raise ValueError(f"{field} must be finite")
    if low is not None and value < low:
        raise ValueError(f"{field} must be at least {low}")
    if high is not None and value > high:
        raise ValueError(f"{field} must be at most {high}")


@dataclass(frozen=True, slots=True)
class GeoLocation:
    """A geographic point. Timezone is display metadata, not a weather boundary."""
    name: str
    latitude: float
    longitude: float
    timezone_name: str | None = None
    elevation_m: float | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("location name cannot be empty")
        _number(self.latitude, "latitude", -90, 90)
        _number(self.longitude, "longitude", -180, 180)
        _number(self.elevation_m, "elevation_m")


@dataclass(frozen=True, slots=True)
class WeatherObservation:
    """A measured weather record, distinct from model-generated forecasts."""
    location: GeoLocation
    observed_at: datetime
    source: str
    temperature_c: float | None = None
    precipitation_mm: float | None = None
    relative_humidity_pct: float | None = None
    wind_speed_kmh: float | None = None
    surface_pressure_hpa: float | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "observed_at", _utc(self.observed_at, "observed_at"))
        if not self.source.strip():
            raise ValueError("source cannot be empty")
        _number(self.temperature_c, "temperature_c")
        _number(self.precipitation_mm, "precipitation_mm", 0)
        _number(self.relative_humidity_pct, "relative_humidity_pct", 0, 100)
        _number(self.wind_speed_kmh, "wind_speed_kmh", 0)
        _number(self.surface_pressure_hpa, "surface_pressure_hpa", 0)


@dataclass(frozen=True, slots=True)
class WeatherForecast:
    """A forecast for a location and valid time, retaining issue-time provenance."""
    location: GeoLocation
    valid_at: datetime
    issued_at: datetime
    source: str
    temperature_c: float | None = None
    precipitation_mm: float | None = None
    precipitation_probability_pct: float | None = None
    relative_humidity_pct: float | None = None
    wind_speed_kmh: float | None = None
    surface_pressure_hpa: float | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "valid_at", _utc(self.valid_at, "valid_at"))
        object.__setattr__(self, "issued_at", _utc(self.issued_at, "issued_at"))
        if not self.source.strip():
            raise ValueError("source cannot be empty")
        _number(self.temperature_c, "temperature_c")
        _number(self.precipitation_mm, "precipitation_mm", 0)
        _number(self.precipitation_probability_pct, "precipitation_probability_pct", 0, 100)
        _number(self.relative_humidity_pct, "relative_humidity_pct", 0, 100)
        _number(self.wind_speed_kmh, "wind_speed_kmh", 0)
        _number(self.surface_pressure_hpa, "surface_pressure_hpa", 0)
