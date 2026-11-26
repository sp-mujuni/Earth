# EARTH Web

Next.js 15 dashboard for the EARTH intelligence API.

## Local development

Terminal 1 — from the repository root:

```bash
python -m pip install -r requirements-api.txt
uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

Terminal 2:

```bash
cd web
cp .env.example .env.local
npm install
npm run dev
```

Open http://localhost:3000. The API's interactive documentation is at
http://localhost:8000/docs.

Set `NEXT_PUBLIC_EARTH_API_URL` to the API's `/api/v1` base URL when deploying.
Set `EARTH_CORS_ORIGINS` on the API to the exact frontend origin(s).

## Features

- Operational API status and UTC clock
- Stored forecast and observation counts
- Location network view with search
- Forecast timeline and hourly record table
- Hazard intelligence status and transparent roadmap
- Responsive dark observatory interface

The frontend does not fabricate weather readings. When no forecast has been ingested,
it shows the configured starter geography and an explicit empty-data state.
