"""Date-aware conversion and comparison using UTC instants."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from earth.core.timezone import get_timezone, localize_wall_time

@dataclass(frozen=True)
class ConversionResult:
    source_timezone: str
    target_timezone: str
    source_local: str
    utc: str
    target_local: str
    target_utc_offset: str
    target_is_dst: bool
    day_difference: int
    def to_dict(self) -> dict:
        return asdict(self)

def _offset_text(value) -> str:
    total = int(value.total_seconds() // 60)
    sign = "+" if total >= 0 else "-"
    hours, minutes = divmod(abs(total), 60)
    return f"UTC{sign}{hours:02d}:{minutes:02d}"

def convert_local_datetime(local_datetime: datetime, source_timezone: str, target_timezone: str, *, fold: int | None = None) -> ConversionResult:
    """Convert a naive source wall time into a destination's local civil time."""
    source = localize_wall_time(local_datetime, source_timezone, fold=fold)
    return convert_wall_time(source, source_timezone, target_timezone)

def convert_wall_time(source_datetime: datetime, source_timezone: str, target_timezone: str) -> ConversionResult:
    """Convert an aware datetime into another IANA time zone."""
    if source_datetime.tzinfo is None:
        raise ValueError("source_datetime must be timezone-aware.")
    source_zone, target_zone = get_timezone(source_timezone), get_timezone(target_timezone)
    source_local = source_datetime.astimezone(source_zone)
    utc_moment = source_local.astimezone(timezone.utc)
    target_local = utc_moment.astimezone(target_zone)
    return ConversionResult(source_timezone, target_timezone, source_local.isoformat(), utc_moment.isoformat(), target_local.isoformat(), _offset_text(target_local.utcoffset()), bool(target_local.dst() and target_local.dst().total_seconds()), (target_local.date() - source_local.date()).days)

def compare_locations(instant: datetime, timezones: list[str]) -> list[dict]:
    """Render one exact instant in several zones."""
    if instant.tzinfo is None:
        raise ValueError("instant must be timezone-aware; provide an offset or UTC.")
    utc_moment = instant.astimezone(timezone.utc)
    rows = []
    for identifier in timezones:
        local = utc_moment.astimezone(get_timezone(identifier))
        rows.append({"timezone": identifier, "local_datetime": local.isoformat(), "abbreviation": local.tzname(), "utc_offset": _offset_text(local.utcoffset()), "is_dst": bool(local.dst() and local.dst().total_seconds())})
    return rows
