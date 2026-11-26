"""Transparent rainfall screening primitives; not official hazard warnings."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable

from earth.weather.models import WeatherForecast


@dataclass(frozen=True, slots=True)
class RainfallThresholds:
    """Configurable screening thresholds, not universal safety thresholds."""

    watch_24h_mm: float = 20.0
    elevated_24h_mm: float = 50.0
    high_24h_mm: float = 100.0
    high_hourly_mm: float = 30.0

    def __post_init__(self) -> None:
        values = (
            self.watch_24h_mm, self.elevated_24h_mm,
            self.high_24h_mm, self.high_hourly_mm,
        )
        if any(value < 0 for value in values):
            raise ValueError("rainfall thresholds cannot be negative")
        if not self.watch_24h_mm <= self.elevated_24h_mm <= self.high_24h_mm:
            raise ValueError("24-hour thresholds must be non-decreasing")


@dataclass(frozen=True, slots=True)
class RainfallScreening:
    location_name: str
    window_start: datetime
    window_end: datetime
    forecast_total_mm: float
    maximum_hourly_mm: float
    level: str
    reasons: tuple[str, ...]
    disclaimer: str = (
        "Rainfall-only screening, not a flood forecast or official warning. "
        "Flood risk also depends on catchment, terrain, drainage, soil saturation, "
        "river levels, and authoritative local alerts."
    )


def screen_next_24h_rainfall(
    forecasts: Iterable[WeatherForecast],
    now: datetime | None = None,
    thresholds: RainfallThresholds = RainfallThresholds(),
) -> RainfallScreening:
    """Summarize forecast rainfall in the next 24 hours for one location."""
    instant = now or datetime.now(timezone.utc)
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    instant = instant.astimezone(timezone.utc)
    end = instant + timedelta(hours=24)
    rows = [
        item for item in forecasts
        if instant <= item.valid_at < end
    ]
    if not rows:
        raise ValueError("no forecast points in the requested 24-hour window")
    names = {item.location.name for item in rows}
    if len(names) != 1:
        raise ValueError("all forecast points must belong to the same location")

    amounts = [item.precipitation_mm or 0.0 for item in rows]
    total = sum(amounts)
    peak = max(amounts)
    if total >= thresholds.high_24h_mm or peak >= thresholds.high_hourly_mm:
        level = "high"
    elif total >= thresholds.elevated_24h_mm:
        level = "elevated"
    elif total >= thresholds.watch_24h_mm:
        level = "watch"
    else:
        level = "below_threshold"

    reasons = []
    if total >= thresholds.watch_24h_mm:
        reasons.append(f"Forecast 24-hour rainfall totals {total:.1f} mm.")
    if peak >= thresholds.high_hourly_mm:
        reasons.append(f"Peak forecast hourly rainfall is {peak:.1f} mm.")
    if not reasons:
        reasons.append(f"Forecast 24-hour rainfall totals {total:.1f} mm, below watch threshold.")

    return RainfallScreening(
        location_name=next(iter(names)),
        window_start=instant,
        window_end=end,
        forecast_total_mm=total,
        maximum_hourly_mm=peak,
        level=level,
        reasons=tuple(reasons),
    )
