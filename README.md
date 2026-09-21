# ThreatLens

ThreatLens is a portfolio project for cybersecurity log analysis and threat detection. The intended product is a detection-engine-first tool that parses auth/access logs and surfaces real findings — not a SOC dashboard mockup.

**Stack:** Next.js (`web/`) for the investigation UI. FastAPI (`api/`) for parse + detect. Supabase Auth + Postgres with RLS for user-scoped persistence.

**Current status:** M5 complete. Architecture is **Option A**: the web app authenticates with Supabase and writes `analyses` / `incidents` under RLS. The Python engine stays stateless (`/health`, `/parse`, `/detect`, `/rules`). The UI shows only live `/detect` output and saved rows. There is no AI, no mock incident list, and no fabricated charts.

**Requires Gabby to wire a Supabase project** (URL + anon key in `web/.env.local` or Vercel, migration applied) for save/login. Analyze and Rules only need a reachable FastAPI URL. CI does not use live Supabase credentials.

## Architecture (Option A)

```
Browser
  → FastAPI POST /detect     (stateless engine)
  → FastAPI GET /rules       (live thresholds)
  → Supabase Auth + Postgres (CRUD saved runs; RLS = own rows only)
```

Option B (API holds the JWT and writes to Postgres) was not used so the detection service stays a pure function. Details: [docs/auth-persistence.md](docs/auth-persistence.md).

## Roadmap

- **M1** — log parser and fixtures
- **M2** — detection engine: brute_force + credential_spray
- **M3** — more rules: unusual_login, impossible_travel (simulated), request_frequency, restricted_access
- **M4** — auth + RLS persistence
- **M5** — investigation UI over real detections *(this)*
- **Optional, last** — AI as explain-only (never as the detector)

## Pages (M5)

| Path | What it is |
| --- | --- |
| `/` | Honest landing: stack, implemented vs not |
| `/analyze` | Paste/upload TLAL or load a repo fixture → `POST /detect` → incidents + parse errors. Save if signed in |
| `/analyses` | Investigations list (your saved runs; severity counts from stored incidents) |
| `/analyses/[id]` | Investigation detail with severity / rule / status filters and readable evidence |
| `/rules` | Live `GET /rules` catalog |
| `/login`, `/signup` | Supabase email/password |

## Run locally

Requires Node.js 22+ and Python 3.12+.

### 1. Supabase (once, for save/login)

1. Create a Supabase project.
2. Enable Email auth. For local use, **disable Confirm email** so signup is immediate (say so if you leave it on).
3. Run [`supabase/migrations/20260921120000_init_auth_persistence.sql`](supabase/migrations/20260921120000_init_auth_persistence.sql) in the SQL editor.
4. Copy **Project URL** and **anon public** key only — never `service_role`.

`web/.env.local` (see `web/.env.example`):

```
NEXT_PUBLIC_SUPABASE_URL=https://YOUR_PROJECT.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

Without Supabase, the web app still builds. Landing / Analyze / Rules work; login and investigations show a setup page.

Without `NEXT_PUBLIC_API_URL`, Analyze and Rules show a clear error. There is **no** in-browser detector and **no** demo-mode fallback.

### 2. API (`api/`)

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

CORS defaults to `http://localhost:3000` and `http://127.0.0.1:3000`. Override with `CORS_ORIGINS` (comma-separated) when the web app is deployed.

```bash
# From the repo root, with the API running on :8000
curl -sS -X POST http://127.0.0.1:8000/detect \
  -H 'Content-Type: text/plain' \
  --data-binary @fixtures/bruteforce/auth.log
```

### 3. Web (`web/`)

```bash
cd web
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). Analyze a fixture, inspect evidence, sign in, save, open Investigations.

Parser: [docs/log-schema.md](docs/log-schema.md). Detection: [docs/detection.md](docs/detection.md). Auth/RLS: [docs/auth-persistence.md](docs/auth-persistence.md). Samples: [fixtures/README.md](fixtures/README.md). Vercel: [docs/vercel.md](docs/vercel.md).

### Tests

```bash
cd api
pip install -r requirements.txt
pytest
```

Pytest covers the engine plus a static check that the migration SQL defines tables and RLS. It does **not** need Supabase credentials.

```bash
cd web
npm ci
npm run build
```

## Interview demo path

1. Landing — explain Option A (stateless FastAPI, RLS in Next.js). Point at Implemented vs Not.
2. Rules — live `GET /rules` (if the API is up). Thresholds come from the engine.
3. Analyze — load **normal** (expect 0 incidents), then **brute_force**. Expand evidence JSON. Load **edge** to show parse errors.
4. Sign in → Save → Investigations list (severity chips from saved rows) → detail filters.

Do not show a threat map. `impossible_travel` is simulated `country=` / TEST-NET prefixes, not MaxMind.

## Thresholds (M3 defaults, unchanged in M4/M5)

| Rule | Trigger | Defaults | Severity |
| --- | --- | --- | --- |
| `brute_force` | `login_failure` from the same IP | **10** failures / **5** min | `high` |
| `credential_spray` | `login_failure` from the same IP across distinct usernames | **5** usernames / **10** min | `high` |
| `unusual_login` | `login_success` outside 08:00–22:00 UTC, **or** ≥ N successes for the same user in T | **08–22** UTC; **5** successes / **10** min | `medium` |
| `impossible_travel` | `login_success` for the same user from ≥2 **simulated** countries in T | **2** countries / **60** min | `high` |
| `request_frequency` | `request` events from the same IP | **50** requests / **1** min | `medium` |
| `restricted_access` | any `access_denied` to `/admin`, `/secrets`, `/etc/passwd`, `/.env` | **1** denial | `high` |

Incident `id` from the engine is a SHA-256 prefix of `rule_id|correlation_key|window_start|window_end`. Saved rows use a UUID; the engine id is stored as `engine_incident_id`.

**Impossible travel is simulated:** locations come from fixture `country=` / `geo=` fields or a static TEST-NET IP-prefix map. There is no MaxMind GeoIP database.

## Honest scope

This is not a production detection platform. It finds the patterns above in **synthetic TLAL** fixtures, then stores them per user. It does not ingest live logs, perform real geolocation, learn baselines, or invent SOC noise for the UI.
