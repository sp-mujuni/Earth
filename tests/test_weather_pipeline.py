from datetime import datetime, timedelta, timezone

import pytest

from earth.weather.ingestion import ForecastIngestor
from earth.weather.models import GeoLocation, WeatherForecast, WeatherObservation
from earth.weather.scheduler import next_utc_cycle, seconds_until_next_cycle
from earth.weather.storage import WeatherStore

KAMPALA = GeoLocation("Kampala", 0.3476, 32.5825, "Africa/Kampala")


def forecast(location=KAMPALA, valid_at=None, issued_at=None, rain=1.5):
    now = datetime(2026, 11, 26, 8, tzinfo=timezone.utc)
    return WeatherForecast(
        location, valid_at or now, issued_at or now, "fixture",
        precipitation_mm=rain, temperature_c=25,
    )


def test_store_persists_and_deduplicates_forecasts():
    with WeatherStore(":memory:") as store:
        item = forecast()
        assert store.save_forecasts([item]) == 1
        assert store.save_forecasts([item]) == 1
        assert store.count("forecasts") == 1


def test_store_keeps_distinct_forecast_issues():
    with WeatherStore(":memory:") as store:
        valid = datetime(2026, 11, 27, 8, tzinfo=timezone.utc)
        first = forecast(valid_at=valid, issued_at=datetime(2026, 11, 26, 6, tzinfo=timezone.utc))
        second = forecast(valid_at=valid, issued_at=datetime(2026, 11, 26, 7, tzinfo=timezone.utc), rain=4)
        store.save_forecasts([first, second])
        assert store.count("forecasts") == 2


def test_store_persists_observations():
    now = datetime(2026, 11, 26, 8, tzinfo=timezone.utc)
    item = WeatherObservation(KAMPALA, now, "station-a", temperature_c=26)
    with WeatherStore(":memory:") as store:
        assert store.save_observations([item]) == 1
        assert store.count("observations") == 1


def test_store_rejects_unknown_count_table():
    with WeatherStore(":memory:") as store:
        with pytest.raises(ValueError):
            store.count("users")


def test_scheduler_returns_next_hour_boundary():
    now = datetime(2026, 11, 26, 8, 23, tzinfo=timezone.utc)
    assert next_utc_cycle(now) == datetime(2026, 11, 26, 9, tzinfo=timezone.utc)
    assert seconds_until_next_cycle(now) == 37 * 60


def test_scheduler_boundary_is_strictly_future():
    now = datetime(2026, 11, 26, 8, 0, tzinfo=timezone.utc)
    assert next_utc_cycle(now) == now + timedelta(hours=1)


def test_scheduler_supports_staggered_phase():
    now = datetime(2026, 11, 26, 8, 10, tzinfo=timezone.utc)
    assert next_utc_cycle(now, interval_minutes=60, phase_minutes=15) == datetime(
        2026, 11, 26, 8, 15, tzinfo=timezone.utc
    )


def test_scheduler_requires_aware_time():
    with pytest.raises(ValueError, match="timezone-aware"):
        next_utc_cycle(datetime(2026, 11, 26, 8))


def test_ingestor_persists_success_and_reports_failure():
    class Provider:
        def fetch_hourly_forecast(self, location, forecast_days=3):
            if location.name == "Broken":
                raise RuntimeError("provider unavailable")
            return [forecast(location=location)]

    broken = GeoLocation("Broken", 1, 1)
    with WeatherStore(":memory:") as store:
        report = ForecastIngestor(Provider(), store).ingest([KAMPALA, broken])
        assert report.fetched_total == 1
        assert report.persisted_total == 1
        assert report.failed_locations == ("Broken",)
        assert store.count("forecasts") == 1


def test_ingestor_rejects_empty_location_list():
    class Provider:
        def fetch_hourly_forecast(self, location, forecast_days=3):
            return []

    with WeatherStore(":memory:") as store:
        with pytest.raises(ValueError, match="at least one location"):
            ForecastIngestor(Provider(), store).ingest([])
