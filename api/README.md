# ThreatLens API

FastAPI service. M6 still exposes `GET /health`, `GET /rules`, `POST /parse`, and `POST /detect` only. Persistence, login, and the investigation UI live in the Next.js app (Option A) — this process does not take a user JWT or a service role key. No AI.

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Liveness. Returns `{"status":"ok"}`. No config, no secrets. |
| `GET` | `/rules` | Registered detectors and thresholds. |
| `POST` | `/parse` | Parse raw log text. Returns `{ "events": [...], "errors": [...] }`. |
| `POST` | `/detect` | Parse, then run the engine. Returns `{ "events_count", "incidents", "parse_errors" }`. |

`POST /parse` and `POST /detect` accept:

- `Content-Type: text/plain` — body is the log blob
- `Content-Type: application/json` — `{"text": "<log lines>"}`

Bodies larger than **1 MiB** are rejected (`413`). That bound is intentional and kept. Malformed lines are listed in parse errors; they do not fail the request.

POST `/parse` and `/detect` are also **rate-limited** in-memory: **60 requests / 60 seconds / client IP** by default (`RATE_LIMIT_REQUESTS`, `RATE_LIMIT_WINDOW_SECONDS`). `GET /health` and `GET /rules` are not limited. Exceeding the cap is `429`. This is per process (not Redis); disable with `RATE_LIMIT_ENABLED=false`. Request bodies are not logged.

## CORS

The web app calls this API from the browser. Default `Access-Control-Allow-Origin` list (production-safe: local only):

- `http://localhost:3000`
- `http://127.0.0.1:3000`

A hosted Vercel origin will **fail CORS** until you set `CORS_ORIGINS` (comma-separated) and restart. Example: `https://your-app.vercel.app`. Do not use `*`. See `api/.env.example` and [../docs/deploy.md](../docs/deploy.md).

## Docker (Render / Railway / Fly)

```bash
docker build -t threatlens-api .
docker run --rm -p 8000:8000 \
  -e CORS_ORIGINS=https://YOUR-APP.vercel.app,http://localhost:3000,http://127.0.0.1:3000 \
  threatlens-api
```

The image listens on `0.0.0.0:$PORT` (default 8000). Health check: `GET /health`. Do not bake `.env` into the image.

Native start (same contract): `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.

## Schema and log format

Normalized event model: `app/models.py` (`LogEvent`, `Incident`). Log format: [../docs/log-schema.md](../docs/log-schema.md). Detection: [../docs/detection.md](../docs/detection.md). Auth/persistence: [../docs/auth-persistence.md](../docs/auth-persistence.md).

**ThreatLens Auth Log (TLAL)** — one event per line:

```
<timestamp> <event_type> [key=value ...]

2024-01-15T03:12:01Z login_failure user=alice ip=203.0.113.10
```

JSON lines (object per line, schema field names) are also accepted in the same blob. Optional `country=` / `geo=` (or JSON `country` / `geo`) is a simulated location key for `impossible_travel` — not MaxMind GeoIP.

## Run locally

From this directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/rules
curl -sS -X POST http://127.0.0.1:8000/parse \
  -H 'Content-Type: text/plain' \
  --data-binary '2024-01-15T03:12:01Z login_failure user=alice ip=203.0.113.10'
curl -sS -X POST http://127.0.0.1:8000/detect \
  -H 'Content-Type: text/plain' \
  --data-binary @../fixtures/bruteforce/auth.log
```

## Tests

```bash
pytest
```
