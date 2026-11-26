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
