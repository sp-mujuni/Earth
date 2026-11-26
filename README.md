# EARTH — Global Temporal Intelligence

**One computational engine. Two interfaces. One global temporal model.**

EARTH is evolving from a country-based time-zone converter into a Global Temporal Intelligence platform: a reliable system for calculating, comparing, and reasoning about civil time across the planet.

The initial architecture provides a shared Python engine for both the command-line interface and the planned web application. The engine uses IANA time-zone identifiers and Python's `zoneinfo`, rather than treating countries as if each had one fixed UTC offset.

## Current development status

The `feature/temporal-engine` branch introduces the first foundation of EARTH v0.2:

- IANA time-zone resolution.
- Date-aware conversion between locations.
- Explicit detection of ambiguous and nonexistent local times during DST transitions.
- Multi-location comparison for a single exact instant.
- A starter city resolver and direct IANA identifier support.
- A new `earth` command-line entry point.
- Automated tests for offsets, DST, and date-boundary behaviour.

The existing `timezone_converter.py` and `countries-time-zones.md` remain in the repository as the original standard-offset converter and reference dataset. They are retained for backwards compatibility and are not the authoritative source for the new engine.

## Architecture

```text
EARTH
├── CLI (Python) ───────────────────────┐
│                                       │
└── Web application (Next.js)           │
        │                               │
        ▼                               ▼
     FastAPI                         EARTH Core
        │                               │
        └───────────────────────────────┘
                                        │
                   ┌────────────────────┼──────────────────┐
                   ▼                    ▼                  ▼
               Time Engine       Location Engine     Temporal Intelligence
               IANA / DST        City / IANA zones   Comparison / scheduling
                                        │
                                        ▼
                              IANA Time Zone Database
```

The core package must not depend on the CLI or web interface. Both interfaces call the same computation functions; the web backend will expose those functions through a versioned API.

### Repository layout

```text
earth/
├── core/
│   ├── timezone.py       # IANA resolution, DST validation, zone metadata
│   └── conversion.py     # Conversion and multi-location comparison
├── locations/
│   └── resolver.py       # Starter city index and IANA lookup
└── cli/
    └── main.py           # CLI backed by the shared engine

tests/
├── test_timezone.py
└── test_conversion.py

docs/
└── TIME_MODEL.md
```

## Requirements

- Python 3.10+
- IANA time-zone database; on Windows the project installs the `tzdata` fallback.
- Development tests: `pytest`

## Installation

Clone the repository and install the project in editable mode:

```bash
git clone https://github.com/sp-mujuni/Earth.git
cd Earth
python -m venv .venv
```

Activate the environment:

**Windows PowerShell**
```powershell
.venv\Scripts\Activate.ps1
```

**macOS / Linux**
```bash
source .venv/bin/activate
```

Install the package and development dependencies:

```bash
python -m pip install -e ".[dev]"
```

## CLI usage

The new CLI is installed as `earth`.

### Current local time

```bash
earth clock
earth clock --location London
earth clock --location Africa/Kampala
```

The default location is `Africa/Kampala`, but the engine does not assume that the computer itself is in Uganda.

### Convert a local date and time

```bash
earth convert --from Kampala --to London --datetime "2026-11-24T14:30"
```

The input is a local wall-clock time in the source location. If that time is ambiguous during a DST rollback, EARTH asks for an explicit occurrence:

```bash
earth convert --from New York --to Kampala --datetime "2026-11-01T01:30" --fold 0
```

- `--fold 0`: earlier occurrence.
- `--fold 1`: later occurrence.

A nonexistent wall time during a DST clock advance is rejected rather than silently shifted.

### Compare locations

```bash
earth compare Africa/Kampala Europe/London Asia/Tokyo
earth compare Africa/Kampala Europe/London --at "2026-11-24T12:00:00Z"
```

Comparisons require one exact instant. When `--at` is omitted, the current UTC instant is used.

### Search locations and time zones

```bash
earth location search Kampala
earth location search Pacific
```

The first location index is intentionally a curated starter set. Direct IANA identifiers are supported even when a city is not in that index.

## Python API

The shared engine can be used without invoking the CLI:

```python
from datetime import datetime
from earth.core.conversion import convert_local_datetime

result = convert_local_datetime(
    datetime(2026, 11, 24, 14, 30),
    "Africa/Kampala",
    "Europe/London",
)

print(result.target_local)
print(result.utc)
```

For a comparison of one instant across several zones:

```python
from datetime import datetime, timezone
from earth.core.conversion import compare_locations

rows = compare_locations(
    datetime.now(timezone.utc),
    ["Africa/Kampala", "Europe/London", "Asia/Tokyo"],
)
```

## Temporal correctness

EARTH distinguishes between a local wall-clock reading and an exact instant.

- **Aware datetime:** identifies an instant and an associated time zone or UTC offset.
- **Naive datetime:** represents a wall-clock value that still needs to be interpreted in a named zone.
- **Ambiguous local time:** occurs twice when clocks move backwards. The caller must choose `fold=0` or `fold=1`.
- **Nonexistent local time:** is skipped when clocks move forwards. EARTH raises an explicit error.

All cross-location conversions resolve the source instant and render that instant in the destination zone. Fractional-hour offsets, DST transitions, and date changes are handled by the IANA database.

See [docs/TIME_MODEL.md](docs/TIME_MODEL.md) for the detailed model and assumptions.

## Testing

Run the automated test suite:

```bash
python -m pytest
```

The initial tests cover Kampala, London, Chatham Islands' 45-minute offset, DST gaps and folds in New York, and date-line changes.

## Roadmap

| Phase | Focus | Status |
|---|---|---|
| 1 | Shared IANA-aware temporal engine and tests | In progress |
| 2 | Modernized CLI and expanded location resolution | Planned |
| 3 | FastAPI and Next.js web application | Planned |
| 4 | Working-hours and meeting-time intelligence | Planned |
| 5 | Sunrise, sunset, solar noon, and daylight maps | Planned |
| 6 | Julian dates, sidereal time, and astronomical calculations | Planned |

## Design principles

1. One computational engine shared by all interfaces.
2. IANA time-zone identifiers are authoritative for civil-time rules.
3. UTC is the common reference for comparing exact instants.
4. Ambiguous and nonexistent local times are surfaced explicitly.
5. Accuracy and reproducibility take priority over decorative features.
6. The system should expand into solar and astronomical time without rewriting the civil-time foundation.

## License

No license file is currently present. A license should be selected before distributing EARTH for reuse.


## Weather intelligence (foundation)

The `earth.weather` package includes geographic weather models, UTC-normalized observations
and forecasts, an Open-Meteo hourly forecast adapter, SQLite persistence with provenance,
per-location ingestion reporting, UTC-aligned scheduling helpers, and configurable 24-hour
rainfall screening. See [docs/WEATHER_INTELLIGENCE.md](docs/WEATHER_INTELLIGENCE.md) for
usage, synchronization principles, limitations, and next steps.

Run `earth-weather next-cycle` to inspect the next UTC collection boundary, or
`earth-weather ingest --locations config/weather_locations.json` to fetch and persist
hourly forecasts for configured locations.

Important: files under the root `weather/` directory are historical synthetic simulations,
not verified meteorological observations. The rainfall screen is not a flood forecast or
official warning.
