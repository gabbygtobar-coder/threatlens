# ThreatLens API

FastAPI service. M2 exposes `GET /health`, `GET /rules`, `POST /parse`, and `POST /detect`. There is no persistence or auth.

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Liveness. Returns `{"status":"ok"}`. |
| `GET` | `/rules` | Registered detectors and thresholds. |
| `POST` | `/parse` | Parse raw log text. Returns `{ "events": [...], "errors": [...] }`. |
| `POST` | `/detect` | Parse, then run the engine. Returns `{ "events_count", "incidents", "parse_errors" }`. |

`POST /parse` and `POST /detect` accept:

- `Content-Type: text/plain` — body is the log blob
- `Content-Type: application/json` — `{"text": "<log lines>"}`

Bodies larger than 1 MiB are rejected (`413`). Malformed lines are listed in parse errors; they do not fail the request.

## Schema and log format

Normalized event model: `app/models.py` (`LogEvent`, `Incident`). Log format: [../docs/log-schema.md](../docs/log-schema.md). Detection: [../docs/detection.md](../docs/detection.md).

**ThreatLens Auth Log (TLAL)** — one event per line:

```
<timestamp> <event_type> [key=value ...]

2024-01-15T03:12:01Z login_failure user=alice ip=203.0.113.10
```

JSON lines (object per line, schema field names) are also accepted in the same blob.

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
