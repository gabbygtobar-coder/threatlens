# ThreatLens API

Minimal FastAPI service. M0 exposes `GET /health` only — no parsers, detections, or persistence.

## Run locally

From this directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Then:

```bash
curl http://127.0.0.1:8000/health
```

Expected: `{"status":"ok"}`.
