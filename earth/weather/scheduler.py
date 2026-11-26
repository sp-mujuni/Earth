"""UTC-aligned scheduling helpers for globally coordinated refresh cycles."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone


def next_utc_cycle(
    now: datetime | None = None,
    interval_minutes: int = 60,
    phase_minutes: int = 0,
) -> datetime:
    """Return the next future UTC cycle boundary.

    For the default hourly cycle this returns the next exact UTC hour.
    A phase can stagger workloads while preserving a globally shared cadence.
    """
    if interval_minutes < 1 or interval_minutes > 1440:
        raise ValueError("interval_minutes must be between 1 and 1440")
    if not 0 <= phase_minutes < interval_minutes:
        raise ValueError("phase_minutes must be within the interval")
    instant = now or datetime.now(timezone.utc)
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    instant = instant.astimezone(timezone.utc)
    midnight = instant.replace(hour=0, minute=0, second=0, microsecond=0)
    elapsed_minutes = int((instant - midnight).total_seconds() // 60)
    next_index = ((elapsed_minutes - phase_minutes) // interval_minutes) + 1
    boundary = midnight + timedelta(minutes=phase_minutes + next_index * interval_minutes)
    return boundary


def seconds_until_next_cycle(
    now: datetime | None = None,
    interval_minutes: int = 60,
    phase_minutes: int = 0,
) -> float:
    instant = now or datetime.now(timezone.utc)
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    return (next_utc_cycle(instant, interval_minutes, phase_minutes) -
            instant.astimezone(timezone.utc)).total_seconds()
