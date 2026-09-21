# ThreatLens

ThreatLens is a portfolio project for cybersecurity log analysis and threat detection. The intended product is a detection-engine-first tool that parses auth/access logs and surfaces real findings — not a SOC dashboard mockup.

**Stack:** Next.js and TypeScript in `web/`, FastAPI and Python in `api/`. Postgres (likely via Supabase) is planned later; it is not wired up yet.

**Current status:** M2 complete. The API parses ThreatLens Auth Log (TLAL) text/JSON lines and runs a deterministic detection engine with two rules: `brute_force` and `credential_spray`. Incidents are explainable (rule id, thresholds, evidence). There is no dashboard of alerts, no database, no auth, and no AI.

## Roadmap

- **M1** — log parser and fixtures
- **M2** — detection engine: brute_force + credential_spray *(this)*
- **M3** — persistence (Postgres / Supabase)
- **M4** — UI that shows real detections from the engine
- **Later** — more rules (unusual login, impossible travel, …); auth if needed
- **Optional, last** — AI as explain-only (never as the detector)

## Run locally

Requires Node.js 22+ and Python 3.12+.

### Web (`web/`)

```bash
cd web
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). Landing page only — detections are API-side.

### API (`api/`)

```bash
cd api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- `GET http://127.0.0.1:8000/health` → `{"status":"ok"}`
- `GET http://127.0.0.1:8000/rules` → registered rule ids and thresholds
- `POST http://127.0.0.1:8000/parse` — raw log text → `{ "events": [...], "errors": [...] }`
- `POST http://127.0.0.1:8000/detect` — same body as `/parse` → `{ "events_count": N, "incidents": [...], "parse_errors": [...] }`

```bash
# From the repo root, with the API running on :8000
curl -sS -X POST http://127.0.0.1:8000/detect \
  -H 'Content-Type: text/plain' \
  --data-binary @fixtures/bruteforce/auth.log

curl -sS -X POST http://127.0.0.1:8000/detect \
  -H 'Content-Type: text/plain' \
  --data-binary @fixtures/spray/auth.log
```

Parser: [docs/log-schema.md](docs/log-schema.md). Detection: [docs/detection.md](docs/detection.md). Samples: [fixtures/README.md](fixtures/README.md).

### Tests

```bash
cd api
pip install -r requirements.txt
pytest
```

## Thresholds (M2 defaults)

| Rule | Trigger | N / M | Window | Severity |
| --- | --- | --- | --- | --- |
| `brute_force` | `login_failure` from the same IP | **10** failures | **5** minutes | `high` |
| `credential_spray` | `login_failure` from the same IP across distinct usernames | **5** usernames | **10** minutes | `high` |

Incident `id` is a SHA-256 prefix of `rule_id|source_ip|window_start|window_end` (deterministic). `created_at` is the last contributing event time.

## Honest scope

This is not a production detection platform. It finds brute-force and credential-spray patterns in **synthetic TLAL** fixtures. It does not ingest live logs, geolocate, learn baselines, or render a SOC UI. Features that do not exist (dashboard mock alerts, AI, login) are intentionally absent.
