from datetime import datetime, timezone
import pytest
from earth.core.conversion import compare_locations, convert_local_datetime

def test_kampala_to_london():
    result = convert_local_datetime(datetime(2026, 11, 24, 14, 30), "Africa/Kampala", "Europe/London")
    assert result.target_local.startswith("2026-11-24T11:30:00")
    assert result.target_utc_offset == "UTC+00:00"

def test_chatham_45_minute_offset():
    result = convert_local_datetime(datetime(2026, 1, 15, 12), "Africa/Kampala", "Pacific/Chatham")
    assert result.target_utc_offset == "UTC+13:45"

def test_date_line_change():
    result = convert_local_datetime(datetime(2026, 1, 1, 1), "Africa/Kampala", "America/Los_Angeles")
    assert result.day_difference == -1

def test_compare_requires_aware_instant():
    with pytest.raises(ValueError, match="timezone-aware"):
        compare_locations(datetime(2026, 1, 1, 12), ["Africa/Kampala"])

def test_compare_same_instant():
    rows = compare_locations(datetime(2026, 1, 1, 12, tzinfo=timezone.utc), ["Africa/Kampala", "Asia/Tokyo"])
    assert rows[0]["local_datetime"].startswith("2026-01-01T15:00:00")
    assert rows[1]["local_datetime"].startswith("2026-01-01T21:00:00")
