# ThreatLens

ThreatLens is a portfolio project for cybersecurity log analysis and threat detection. The intended product is a detection-engine-first tool that parses auth/access logs and surfaces real findings — not a SOC dashboard mockup.

**Stack:** Next.js and TypeScript in `web/`, FastAPI and Python in `api/`. Postgres (likely via Supabase) is planned later; it is not wired up yet.

**Current status:** M1 complete. There is a normalized log event schema, a parser for a documented custom auth-log format (text + JSON lines), fixture sets under `fixtures/`, and `POST /parse`. There is no detection engine, no database, no auth, and no AI.

## Roadmap

- **M1** — log parser and fixtures *(this)*
- **M2** — detection engine
- **M3** — persistence (Postgres / Supabase)
- **M4** — UI that shows real detections from the engine
- **Later** — auth, if the project needs it
- **Optional, last** — AI as explain-only (never as the detector)

## Run locally

Requires Node.js 22+ and Python 3.12+.

### Web (`web/`)

```bash
cd web
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). You should see the ThreatLens landing page and nothing else.

### API (`api/`)

```bash
cd api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- `GET http://127.0.0.1:8000/health` → `{"status":"ok"}`
- `POST http://127.0.0.1:8000/parse` — raw log text (`text/plain` or JSON `{"text":"..."}`) → `{ "events": [...], "errors": [...] }`

Parser format and schema: [docs/log-schema.md](docs/log-schema.md). Sample logs: [fixtures/README.md](fixtures/README.md).

### Tests

```bash
cd api
pip install -r requirements.txt
pytest
```

## Honest scope

This is not a production detection platform. Parsing sample logs is implemented; nothing here claims to find threats, ingest live logs, or explain incidents. Features that do not exist (dashboard, mock alerts, AI, login) are intentionally absent.
