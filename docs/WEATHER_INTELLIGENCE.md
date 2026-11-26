# Weather intelligence foundation

EARTH's weather subsystem is geographically anchored and UTC-normalized. It is designed
to complement, not replace, the temporal engine.

## Domain model

- `GeoLocation` represents a point by latitude and longitude. A timezone is optional
  display metadata; weather systems must not be partitioned by time-zone boundaries.
- `WeatherObservation` represents a measured record from a named source.
- `WeatherForecast` represents model output and retains both its valid time and issue time.
- All timestamps must be timezone-aware and are normalized to UTC on construction.

The distinction between observation and forecast is deliberate. The existing files under
`weather/` contain synthetic simulations and must not be loaded as real observations.

## Provider adapter

`OpenMeteoClient` fetches hourly forecast fields from Open-Meteo and normalizes them
into `WeatherForecast` records. It uses Python's standard library and needs network access
only when a caller invokes it. The adapter is not an ingestion scheduler or a persistent
archive. Production deployments should add caching, retries, provider attribution,
rate-limit handling, and storage before running frequent global collection cycles.

Example:

```python
from earth.weather.models import GeoLocation
from earth.weather.providers import OpenMeteoClient

kampala = GeoLocation(
    name="Kampala",
    latitude=0.3476,
    longitude=32.5825,
    timezone_name="Africa/Kampala",
)
forecast = OpenMeteoClient().fetch_hourly_forecast(kampala, forecast_days=3)
```

## UTC synchronization

A future scheduler should align collection windows to UTC boundaries (for example,
hourly at minute 00) and store provider issue time, retrieval time, and forecast valid
time separately. Locations remain geographic coordinates, stations, administrative
areas, or hydrological catchments. Local time zones are used for display and user-facing
schedules only.

## Rainfall screening

`screen_next_24h_rainfall` calculates a transparent total and peak hourly rainfall
screen from forecast records. Its default thresholds are configurable engineering
screening values, not universal scientific thresholds or official alerts.

Rainfall alone cannot establish flood risk. A credible flood model also needs catchment
boundaries, terrain and drainage, soil saturation, river gauges, and local warning data.
Drought assessment requires longer climatological baselines, soil moisture,
evapotranspiration, and water availability; a short dry spell is not a drought diagnosis.

## Next engineering steps

1. Add provider response fixtures and robust retry/cache behaviour.
2. Add a persistence layer for observations, forecasts, and provenance.
3. Implement a UTC-aligned scheduler with idempotent collection runs.
4. Integrate official meteorological warnings and river-gauge sources by region.
5. Build catchment-aware flood and long-baseline drought indicators.
6. Add data quality, missingness, freshness, and provider-health monitoring.


## Persistent storage and ingestion

`WeatherStore` uses SQLite and creates its database directory automatically. It stores
observations and forecasts separately, including geographic coordinates, source,
forecast valid time, forecast issue time, and retrieval time. Unique constraints make
repeated ingestion of the same source/location/valid-time/issue-time record idempotent.
A newer forecast issue for the same valid time is retained as a separate record so
forecast revisions can be evaluated later.

`ForecastIngestor` fetches each configured location independently. A failure for one
location is recorded in the report and does not prevent other locations from being
ingested. The current implementation is sequential and intended as a dependable
first collector; distributed workers and concurrency can be added after provider
rate limits and retry policy are established.

Example locations file:

```json
[
  {
    "name": "Kampala",
    "latitude": 0.3476,
    "longitude": 32.5825,
    "timezone_name": "Africa/Kampala"
  },
  {
    "name": "Entebbe",
    "latitude": 0.0512,
    "longitude": 32.4637,
    "timezone_name": "Africa/Kampala"
  }
]
```

Run one ingestion cycle:

```bash
earth-weather ingest --locations config/weather_locations.json --database data/earth_weather.sqlite3 --days 3
```

Inspect the next UTC hourly boundary:

```bash
earth-weather next-cycle
```

The scheduler helper calculates the next strictly-future UTC boundary. It does not
create a persistent background daemon. Production scheduling should be provided by
systemd, cron, a container scheduler, or a managed job service, invoking the ingestion
command at the calculated UTC cadence. This avoids hiding long-running scheduling
state inside the CLI and makes deployments observable and restartable.

## Current operational boundary

This is a single-process SQLite collector, not yet a global distributed ingestion
network. It does not yet implement retries/backoff, provider quotas, alert delivery,
station observation adapters, or a retention policy. SQLite is suitable for local
development and a single-node prototype; a multi-worker deployment should migrate
to a server database with explicit transaction and concurrency policy.
