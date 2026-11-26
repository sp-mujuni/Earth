# EARTH Web Platform

The web platform consists of a FastAPI service and a Next.js 15 App Router frontend.

## Backend

Install the API dependencies and start the service from the repository root:

```bash
python -m pip install -r requirements-api.txt
uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

Interactive API documentation: `/docs`.

| Endpoint | Purpose |
|---|---|
| `GET /api/v1/health` | Service and database health |
| `GET /api/v1/overview` | Aggregate stored-data counts and freshness |
| `GET /api/v1/locations` | Locations represented in stored forecast data |
| `GET /api/v1/forecast?location=Kampala&hours=72` | Hourly forecast records |
| `POST /api/v1/ingest` | Trigger provider ingestion; requires server token |

The ingestion endpoint is disabled unless `EARTH_INGEST_TOKEN` is configured.
Clients send it in `X-Earth-Ingest-Token`; do not expose this secret through a
browser-side environment variable. Use a trusted server-side operator or job runner.

Environment settings are documented in `api/.env.example`. Configure a persistent
volume for `EARTH_WEATHER_DB` in production. Configure `EARTH_CORS_ORIGINS` to the
exact deployed frontend origin.

## Frontend

See [web/README.md](../web/README.md). The frontend reads only the API and does not
create synthetic readings when data is missing.

## Deployment topology

- Deploy the API as a Python service/container.
- Deploy the Next.js frontend as a Node service/container.
- Place SQLite on persistent storage for a single API instance. For multiple API
  replicas or concurrent ingestion workers, migrate the store to PostgreSQL.
- Keep ingestion credentials server-side; never put them in `NEXT_PUBLIC_*` variables.
- Schedule ingestion independently using a managed job runner at UTC-aligned intervals.

## Current limitations

This is the first web platform iteration. Authentication, role-based access, audit logs,
PostgreSQL support, server-side ingestion controls, map tiles, alert feeds, and advanced
hazard models are not yet implemented. The hazard page labels unavailable capabilities
rather than claiming live warning coverage.
