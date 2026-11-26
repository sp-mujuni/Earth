from datetime import datetime, timedelta, timezone

import pytest

from earth.weather.models import GeoLocation, WeatherForecast, WeatherObservation
from earth.weather.rainfall import RainfallThresholds, screen_next_24h_rainfall


KAMPALA = GeoLocation("Kampala", 0.3476, 32.5825, "Africa/Kampala")


def test_location_rejects_invalid_coordinates():
    with pytest.raises(ValueError):
        GeoLocation("Impossible", 91, 0)


def test_observation_normalizes_timestamp_to_utc():
    local = datetime(2026, 11, 26, 12, tzinfo=timezone(timedelta(hours=3)))
    item = WeatherObservation(KAMPALA, local, "test-station", temperature_c=27)
    assert item.observed_at == datetime(2026, 11, 26, 9, tzinfo=timezone.utc)


def test_observation_rejects_naive_datetime():
    with pytest.raises(ValueError, match="timezone-aware"):
        WeatherObservation(KAMPALA, datetime(2026, 11, 26), "test")


def test_forecast_validates_humidity():
    with pytest.raises(ValueError):
        WeatherForecast(
            KAMPALA, datetime.now(timezone.utc), datetime.now(timezone.utc),
            "test", relative_humidity_pct=120,
        )


def test_rainfall_screening_sums_next_24_hours():
    now = datetime(2026, 11, 26, 0, tzinfo=timezone.utc)
    rows = [
        WeatherForecast(
            KAMPALA, now + timedelta(hours=i), now, "fixture",
            precipitation_mm=3.0,
        )
        for i in range(24)
    ]
    result = screen_next_24h_rainfall(rows, now)
    assert result.forecast_total_mm == 72.0
    assert result.level == "elevated"
    assert "not a flood forecast" in result.disclaimer


def test_rainfall_screening_rejects_mixed_locations():
    now = datetime(2026, 11, 26, 0, tzinfo=timezone.utc)
    other = GeoLocation("Entebbe", 0.0512, 32.4637)
    rows = [
        WeatherForecast(KAMPALA, now, now, "fixture", precipitation_mm=1),
        WeatherForecast(other, now, now, "fixture", precipitation_mm=1),
    ]
    with pytest.raises(ValueError, match="same location"):
        screen_next_24h_rainfall(rows, now)


def test_rainfall_thresholds_must_be_ordered():
    with pytest.raises(ValueError):
        RainfallThresholds(watch_24h_mm=80, elevated_24h_mm=50)
