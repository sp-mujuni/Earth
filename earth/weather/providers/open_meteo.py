"""Small standard-library client for the Open-Meteo forecast API.

Provider documentation: https://open-meteo.com/en/docs
The provider returns forecast model output, not ground-truth observations.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import urlopen

from earth.weather.models import GeoLocation, WeatherForecast


class OpenMeteoError(RuntimeError):
    """Raised when the provider response is unavailable or malformed."""


class OpenMeteoClient:
    """Fetch hourly forecasts and normalize them into EARTH domain models."""

    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    def __init__(self, timeout_seconds: float = 15.0) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self.timeout_seconds = timeout_seconds

    def fetch_hourly_forecast(
        self, location: GeoLocation, forecast_days: int = 3
    ) -> list[WeatherForecast]:
        if not 1 <= forecast_days <= 16:
            raise ValueError("forecast_days must be between 1 and 16")

        params = {
            "latitude": location.latitude,
            "longitude": location.longitude,
            "hourly": ",".join(
                [
                    "temperature_2m",
                    "relative_humidity_2m",
                    "precipitation",
                    "precipitation_probability",
                    "wind_speed_10m",
                    "surface_pressure",
                ]
            ),
            "forecast_days": forecast_days,
            "timezone": "UTC",
        }
        url = f"{self.BASE_URL}?{urlencode(params)}"
        try:
            with urlopen(url, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise OpenMeteoError(f"Open-Meteo request failed: {exc}") from exc

        try:
            hourly = payload["hourly"]
            times = hourly["time"]
            issued_at = datetime.now(timezone.utc)
            forecasts = []
            for index, timestamp in enumerate(times):
                forecasts.append(
                    WeatherForecast(
                        location=location,
                        valid_at=datetime.fromisoformat(timestamp).replace(tzinfo=timezone.utc),
                        issued_at=issued_at,
                        source="open-meteo",
                        temperature_c=_at(hourly, "temperature_2m", index),
                        relative_humidity_pct=_at(hourly, "relative_humidity_2m", index),
                        precipitation_mm=_at(hourly, "precipitation", index),
                        precipitation_probability_pct=_at(
                            hourly, "precipitation_probability", index
                        ),
                        wind_speed_kmh=_at(hourly, "wind_speed_10m", index),
                        surface_pressure_hpa=_at(hourly, "surface_pressure", index),
                    )
                )
            return forecasts
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise OpenMeteoError(f"Unexpected Open-Meteo response: {exc}") from exc


def _at(data: dict, key: str, index: int) -> float | None:
    values = data.get(key)
    if values is None:
        return None
    value = values[index]
    return None if value is None else float(value)
