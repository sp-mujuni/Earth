from datetime import datetime, timezone
import pytest
from earth.core.timezone import AmbiguousTimeError, NonexistentTimeError, TimeZoneError, get_timezone, get_timezone_info, localize_wall_time

def test_kampala_zone():
    assert get_timezone("Africa/Kampala").key == "Africa/Kampala"

def test_unknown_zone():
    with pytest.raises(TimeZoneError, match="Unknown time zone"):
        get_timezone("Mars/Olympus")

def test_kampala_offset():
    info = get_timezone_info("Africa/Kampala", datetime(2026, 1, 1, 12, tzinfo=timezone.utc))
    assert info.utc_offset == "UTC+03:00"
    assert info.is_dst is False

def test_dst_gap_rejected():
    with pytest.raises(NonexistentTimeError):
        localize_wall_time(datetime(2026, 3, 8, 2, 30), "America/New_York")

def test_dst_fold_requires_choice():
    value = datetime(2026, 11, 1, 1, 30)
    with pytest.raises(AmbiguousTimeError):
        localize_wall_time(value, "America/New_York")
    early = localize_wall_time(value, "America/New_York", fold=0)
    late = localize_wall_time(value, "America/New_York", fold=1)
    assert early.utcoffset() != late.utcoffset()
