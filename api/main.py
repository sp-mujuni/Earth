"""FastAPI application exposing EARTH temporal and weather intelligence.

Run with: uvicorn api.main:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import hmac
import os
import sqlite3
from contextlib import asynccontextmanager, closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from earth.weather.ingestion import ForecastIngestor
from earth.weather.models import GeoLocation
from earth.weather.providers import OpenMeteoClient
from earth.weather.storage import WeatherStore


def database_path() -> str:
    return os.getenv("EARTH_WEATHER_DB", "data/earth_weather.sqlite3")


def _connect() -> sqlite3.Connection:
    path = database_path()
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    # Initialize schema on first use, including on an empty deployment.
    with WeatherStore(path):
        pass
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def _dict(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)


class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: datetime
    database: str


class LocationResponse(BaseModel):
    name: str
    latitude: float
    longitude: float
    timezone_name: str | None = None
    latest_forecast_at: datetime | None = None
    forecast_points: int = 0


class ForecastPoint(BaseModel):
    valid_at: datetime
    issued_at: datetime
    source: str
    temperature_c: float | None = None
    precipitation_mm: float | None = None
    precipitation_probability_pct: float | None = None
    relative_humidity_pct: float | None = None
    wind_speed_kmh: float | None = None
    surface_pressure_hpa: float | None = None


class OverviewResponse(BaseModel):
    status: str
    locations_monitored: int
    forecast_points: int
    observation_points: int
    latest_retrieval_at: datetime | None = None
    data_source: str


class IngestRequest(BaseModel):
    locations: list[GeoLocation] = Field(min_length=1, max_length=100)
    forecast_days: int = Field(default=3, ge=1, le=16)


def _authorized(x_earth_ingest_token: str | None = Header(default=None)) -> None:
    expected = os.getenv("EARTH_INGEST_TOKEN")
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="Ingestion endpoint is disabled. Configure EARTH_INGEST_TOKEN.",
        )
    if not x_earth_ingest_token or not hmac.compare_digest(x_earth_ingest_token, expected):
        raise HTTPException(status_code=401, detail="Invalid ingestion token.")


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Create the SQLite schema before the first request.
    with WeatherStore(database_path()):
        pass
    yield


app = FastAPI(
    title="EARTH Intelligence API",
    version="0.1.0",
    description=(
        "Geographic weather intelligence and global temporal services. "
        "Weather forecasts are model output, not measured observations or official warnings."
    ),
    lifespan=lifespan,
)

origins = [
    item.strip()
    for item in os.getenv(
        "EARTH_CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if item.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Earth-Ingest-Token"],
)


@app.get("/api/v1/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    with closing(_connect()) as connection:
        connection.execute("SELECT 1").fetchone()
    return HealthResponse(
        status="operational",
        service="earth-api",
        timestamp=datetime.now(timezone.utc),
        database=database_path(),
    )


@app.get("/api/v1/overview", response_model=OverviewResponse, tags=["weather"])
def overview() -> OverviewResponse:
    with _connect() as connection:
        forecasts = connection.execute(
            "SELECT COUNT(*) AS n, MAX(retrieved_at) AS latest FROM weather_forecasts"
        ).fetchone()
        observations = connection.execute(
            "SELECT COUNT(*) AS n FROM weather_observations"
        ).fetchone()
        locations = connection.execute(
            "SELECT COUNT(*) AS n FROM (SELECT DISTINCT location_name, latitude, longitude FROM weather_forecasts)"
        ).fetchone()
    return OverviewResponse(
        status="operational",
        locations_monitored=int(locations["n"]),
        forecast_points=int(forecasts["n"]),
        observation_points=int(observations["n"]),
        latest_retrieval_at=(
            datetime.fromisoformat(forecasts["latest"])
            if forecasts["latest"] else None
        ),
        data_source="Stored provider forecasts and verified observations",
    )


@app.get("/api/v1/locations", response_model=list[LocationResponse], tags=["weather"])
def locations() -> list[LocationResponse]:
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT location_name AS name, latitude, longitude, timezone_name,
                   MAX(valid_at) AS latest_forecast_at, COUNT(*) AS forecast_points
            FROM weather_forecasts
            GROUP BY location_name, latitude, longitude, timezone_name
            ORDER BY location_name
            """
        ).fetchall()
    return [LocationResponse(**_dict(row)) for row in rows]


@app.get("/api/v1/forecast", response_model=list[ForecastPoint], tags=["weather"])
def forecast(
    location: str = Query(min_length=1, max_length=120),
    hours: int = Query(default=48, ge=1, le=384),
) -> list[ForecastPoint]:
    now = datetime.now(timezone.utc)
    end = now + timedelta(hours=hours)
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT valid_at, issued_at, source, temperature_c, precipitation_mm,
                   precipitation_probability_pct, relative_humidity_pct,
                   wind_speed_kmh, surface_pressure_hpa
            FROM weather_forecasts
            WHERE location_name = ? AND valid_at >= ? AND valid_at < ?
            ORDER BY valid_at ASC, issued_at DESC
            """,
            (location, now.isoformat(), end.isoformat()),
        ).fetchall()
    # Keep the newest issue for each valid hour.
    unique: dict[str, ForecastPoint] = {}
    for row in rows:
        point = ForecastPoint(**_dict(row))
        unique.setdefault(point.valid_at.isoformat(), point)
    return list(unique.values())


@app.post(
    "/api/v1/ingest",
    dependencies=[Depends(_authorized)],
    tags=["operations"],
)
def ingest(request: IngestRequest) -> dict[str, Any]:
    provider = OpenMeteoClient()
    with WeatherStore(database_path()) as store:
        report = ForecastIngestor(provider, store).ingest(
            request.locations, request.forecast_days
        )
    return {
        "source": report.source,
        "started_at": report.started_at,
        "completed_at": report.completed_at,
        "fetched_total": report.fetched_total,
        "persisted_total": report.persisted_total,
        "failed_locations": report.failed_locations,
        "locations": [
            {
                "name": item.location_name,
                "fetched": item.fetched,
                "persisted": item.persisted,
                "error": item.error,
            }
            for item in report.locations
        ],
    }


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {"name": "EARTH Intelligence API", "docs": "/docs", "health": "/api/v1/health"}
