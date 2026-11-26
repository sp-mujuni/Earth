"""Provider-to-store forecast ingestion orchestration."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol, Sequence

from earth.weather.models import GeoLocation, WeatherForecast
from earth.weather.storage import WeatherStore


class ForecastProvider(Protocol):
    def fetch_hourly_forecast(
        self, location: GeoLocation, forecast_days: int = 3
    ) -> list[WeatherForecast]: ...


@dataclass(frozen=True, slots=True)
class LocationIngestion:
    location_name: str
    fetched: int
    persisted: int
    error: str | None = None


@dataclass(frozen=True, slots=True)
class IngestionReport:
    started_at: datetime
    completed_at: datetime
    source: str
    locations: tuple[LocationIngestion, ...]

    @property
    def fetched_total(self) -> int:
        return sum(item.fetched for item in self.locations)

    @property
    def persisted_total(self) -> int:
        return sum(item.persisted for item in self.locations)

    @property
    def failed_locations(self) -> tuple[str, ...]:
        return tuple(item.location_name for item in self.locations if item.error)


class ForecastIngestor:
    """Fetch each location independently and persist successful results."""

    def __init__(self, provider: ForecastProvider, store: WeatherStore) -> None:
        self.provider = provider
        self.store = store

    def ingest(
        self, locations: Sequence[GeoLocation], forecast_days: int = 3
    ) -> IngestionReport:
        if not locations:
            raise ValueError("at least one location is required")
        if not 1 <= forecast_days <= 16:
            raise ValueError("forecast_days must be between 1 and 16")
        started = datetime.now(timezone.utc)
        results = []
        source = getattr(self.provider, "SOURCE", None) or self.provider.__class__.__name__
        for location in locations:
            try:
                forecasts = self.provider.fetch_hourly_forecast(location, forecast_days)
                if any(item.location != location for item in forecasts):
                    raise ValueError("provider returned records for a different location")
                persisted = self.store.save_forecasts(forecasts)
                results.append(LocationIngestion(location.name, len(forecasts), persisted))
            except Exception as exc:
                results.append(LocationIngestion(location.name, 0, 0, str(exc)))
        return IngestionReport(
            started_at=started,
            completed_at=datetime.now(timezone.utc),
            source=str(source),
            locations=tuple(results),
        )
