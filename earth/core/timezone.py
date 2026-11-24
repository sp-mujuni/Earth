"""IANA time-zone resolution and safe local wall-time handling."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

class TimeZoneError(ValueError):
    """Invalid time-zone identifier or local wall time."""
class AmbiguousTimeError(TimeZoneError):
    """A local wall time occurs twice during a clock rollback."""
class NonexistentTimeError(TimeZoneError):
    """A local wall time is skipped during a clock advance."""

@dataclass(frozen=True)
class TimeZoneInfo:
    identifier: str
    display_name: str
    utc_offset: str
    is_dst: bool

def get_timezone(identifier: str) -> ZoneInfo:
    """Resolve an IANA identifier; never fall back to the host's local zone."""
    value = identifier.strip()
    if not value:
        raise TimeZoneError("A time-zone identifier is required.")
    try:
        return ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise TimeZoneError(f"Unknown time zone '{identifier}'. Use an IANA identifier such as Africa/Kampala.") from exc

def _offset_text(value) -> str:
    if value is None:
        return "unknown"
    total = int(value.total_seconds() // 60)
    sign = "+" if total >= 0 else "-"
    hours, minutes = divmod(abs(total), 60)
    return f"UTC{sign}{hours:02d}:{minutes:02d}"

def get_timezone_info(identifier: str, instant: datetime | None = None) -> TimeZoneInfo:
    """Return zone metadata at an instant (defaults to current UTC)."""
    zone = get_timezone(identifier)
    moment = instant or datetime.now(timezone.utc)
    if moment.tzinfo is None:
        raise TimeZoneError("instant must be timezone-aware.")
    local = moment.astimezone(zone)
    return TimeZoneInfo(identifier, local.tzname() or identifier, _offset_text(local.utcoffset()), bool(local.dst() and local.dst().total_seconds()))

def localize_wall_time(value: datetime, identifier: str, *, fold: int | None = None) -> datetime:
    """Attach a zone to a naive wall time, rejecting DST gaps and unresolved folds."""
    if value.tzinfo is not None:
        raise TimeZoneError("Expected a naive local datetime, without tzinfo.")
    if fold not in (None, 0, 1):
        raise TimeZoneError("fold must be 0, 1, or None.")
    zone = get_timezone(identifier)
    candidates = []
    for candidate_fold in (0, 1):
        candidate = value.replace(tzinfo=zone, fold=candidate_fold)
        round_trip = candidate.astimezone(timezone.utc).astimezone(zone)
        if round_trip.replace(tzinfo=None) == value and not any(x.utcoffset() == candidate.utcoffset() for x in candidates):
            candidates.append(candidate)
    if not candidates:
        raise NonexistentTimeError(f"{value.isoformat(sep=' ')} does not exist in {identifier} because clocks move forward.")
    if len(candidates) == 2:
        if fold is None:
            raise AmbiguousTimeError(f"{value.isoformat(sep=' ')} occurs twice in {identifier}; specify fold=0 or fold=1.")
        return next(item for item in candidates if item.fold == fold)
    return candidates[0]
