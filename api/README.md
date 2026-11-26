# EARTH API

Run from the repository root:

```bash
python -m pip install -r requirements-api.txt
uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

OpenAPI docs: http://127.0.0.1:8000/docs

See [../docs/WEB_PLATFORM.md](../docs/WEB_PLATFORM.md) for endpoints, deployment,
security settings and current limitations.
