"""Command-line entry point for weather ingestion and cycle inspection."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from earth.weather.ingestion import ForecastIngestor
from earth.weather.models import GeoLocation
from earth.weather.providers import OpenMeteoClient
from earth.weather.scheduler import next_utc_cycle
from earth.weather.storage import WeatherStore


def _load_locations(path: str) -> list[GeoLocation]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("locations file must contain a JSON array")
    return [GeoLocation(**item) for item in payload]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="earth-weather", description="EARTH weather ingestion")
    sub = parser.add_subparsers(dest="command", required=True)
    ingest = sub.add_parser("ingest", help="Fetch and persist forecasts for configured locations")
    ingest.add_argument("--locations", required=True, help="JSON file containing locations")
    ingest.add_argument("--database", default="data/earth_weather.sqlite3")
    ingest.add_argument("--days", type=int, default=3)
    ingest.add_argument("--timeout", type=float, default=15.0)
    cycle = sub.add_parser("next-cycle", help="Show the next UTC-aligned collection boundary")
    cycle.add_argument("--interval-minutes", type=int, default=60)
    cycle.add_argument("--phase-minutes", type=int, default=0)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "next-cycle":
            print(next_utc_cycle(
                interval_minutes=args.interval_minutes,
                phase_minutes=args.phase_minutes,
            ).isoformat())
            return 0

        locations = _load_locations(args.locations)
        provider = OpenMeteoClient(timeout_seconds=args.timeout)
        with WeatherStore(args.database) as store:
            report = ForecastIngestor(provider, store).ingest(locations, args.days)
            output = {
                "source": report.source,
                "started_at": report.started_at.isoformat(),
                "completed_at": report.completed_at.isoformat(),
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
                "database": args.database,
            }
            print(json.dumps(output, indent=2))
            return 1 if report.failed_locations else 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"earth-weather: error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
