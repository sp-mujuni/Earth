"""SQLite persistence for weather records and their provenance.

SQLite is the local default. The repository interface can later be backed by
PostgreSQL without changing domain models or provider adapters.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from earth.weather.models import WeatherForecast, WeatherObservation


def _iso(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("stored timestamps must be timezone-aware")
    return value.astimezone(timezone.utc).isoformat()


class WeatherStore:
    """Transactional SQLite store with idempotent record identities."""

    def __init__(self, database_path: str | Path = "data/earth_weather.sqlite3") -> None:
        self.database_path = str(database_path)
        if self.database_path != ":memory:":
            Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.database_path)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._initialize()

    def _initialize(self) -> None:
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS weather_observations (
                id INTEGER PRIMARY KEY,
                location_name TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                timezone_name TEXT,
                elevation_m REAL,
                observed_at TEXT NOT NULL,
                source TEXT NOT NULL,
                retrieved_at TEXT NOT NULL,
                temperature_c REAL,
                precipitation_mm REAL,
                relative_humidity_pct REAL,
                wind_speed_kmh REAL,
                surface_pressure_hpa REAL,
                UNIQUE(location_name, latitude, longitude, source, observed_at)
            );

            CREATE TABLE IF NOT EXISTS weather_forecasts (
                id INTEGER PRIMARY KEY,
                location_name TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                timezone_name TEXT,
                elevation_m REAL,
                valid_at TEXT NOT NULL,
                issued_at TEXT NOT NULL,
                source TEXT NOT NULL,
                retrieved_at TEXT NOT NULL,
                temperature_c REAL,
                precipitation_mm REAL,
                precipitation_probability_pct REAL,
                relative_humidity_pct REAL,
                wind_speed_kmh REAL,
                surface_pressure_hpa REAL,
                UNIQUE(location_name, latitude, longitude, source, valid_at, issued_at)
            );

            CREATE INDEX IF NOT EXISTS idx_observations_location_time
                ON weather_observations(location_name, observed_at);
            CREATE INDEX IF NOT EXISTS idx_forecasts_location_valid
                ON weather_forecasts(location_name, valid_at);
            CREATE INDEX IF NOT EXISTS idx_forecasts_source_issue
                ON weather_forecasts(source, issued_at);
            """
        )
        self._connection.commit()

    def save_observations(
        self, records: Iterable[WeatherObservation],
        retrieved_at: datetime | None = None,
    ) -> int:
        received = _iso(retrieved_at or datetime.now(timezone.utc))
        rows = []
        for item in records:
            loc = item.location
            rows.append((
                loc.name, loc.latitude, loc.longitude, loc.timezone_name, loc.elevation_m,
                _iso(item.observed_at), item.source, received, item.temperature_c,
                item.precipitation_mm, item.relative_humidity_pct, item.wind_speed_kmh,
                item.surface_pressure_hpa,
            ))
        with self._connection:
            self._connection.executemany(
                """
                INSERT INTO weather_observations (
                    location_name, latitude, longitude, timezone_name, elevation_m,
                    observed_at, source, retrieved_at, temperature_c, precipitation_mm,
                    relative_humidity_pct, wind_speed_kmh, surface_pressure_hpa
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(location_name, latitude, longitude, source, observed_at)
                DO UPDATE SET
                    retrieved_at=excluded.retrieved_at,
                    temperature_c=excluded.temperature_c,
                    precipitation_mm=excluded.precipitation_mm,
                    relative_humidity_pct=excluded.relative_humidity_pct,
                    wind_speed_kmh=excluded.wind_speed_kmh,
                    surface_pressure_hpa=excluded.surface_pressure_hpa
                """,
                rows,
            )
        return len(rows)

    def save_forecasts(
        self, records: Iterable[WeatherForecast],
        retrieved_at: datetime | None = None,
    ) -> int:
        received = _iso(retrieved_at or datetime.now(timezone.utc))
        rows = []
        for item in records:
            loc = item.location
            rows.append((
                loc.name, loc.latitude, loc.longitude, loc.timezone_name, loc.elevation_m,
                _iso(item.valid_at), _iso(item.issued_at), item.source, received,
                item.temperature_c, item.precipitation_mm,
                item.precipitation_probability_pct, item.relative_humidity_pct,
                item.wind_speed_kmh, item.surface_pressure_hpa,
            ))
        with self._connection:
            self._connection.executemany(
                """
                INSERT INTO weather_forecasts (
                    location_name, latitude, longitude, timezone_name, elevation_m,
                    valid_at, issued_at, source, retrieved_at, temperature_c,
                    precipitation_mm, precipitation_probability_pct,
                    relative_humidity_pct, wind_speed_kmh, surface_pressure_hpa
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(location_name, latitude, longitude, source, valid_at, issued_at)
                DO UPDATE SET
                    retrieved_at=excluded.retrieved_at,
                    temperature_c=excluded.temperature_c,
                    precipitation_mm=excluded.precipitation_mm,
                    precipitation_probability_pct=excluded.precipitation_probability_pct,
                    relative_humidity_pct=excluded.relative_humidity_pct,
                    wind_speed_kmh=excluded.wind_speed_kmh,
                    surface_pressure_hpa=excluded.surface_pressure_hpa
                """,
                rows,
            )
        return len(rows)

    def count(self, record_type: str) -> int:
        tables = {
            "observations": "weather_observations",
            "forecasts": "weather_forecasts",
        }
        if record_type not in tables:
            raise ValueError("record_type must be 'observations' or 'forecasts'")
        row = self._connection.execute(
            f"SELECT COUNT(*) AS total FROM {tables[record_type]}"
        ).fetchone()
        return int(row["total"])

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> "WeatherStore":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()
