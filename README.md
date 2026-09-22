# ThreatLens

ThreatLens is a portfolio project for cybersecurity log analysis and threat detection. The intended product is a detection-engine-first tool that parses auth/access logs and surfaces real findings — not a SOC dashboard mockup.

**Stack:** Next.js (`web/`) for the investigation UI. FastAPI (`api/`) for parse + detect. Supabase Auth + Postgres with RLS for user-scoped persistence.

**Current status:** **M7 explain-only.** M0–M6 stay as shipped (six-rule engine, investigation UI, Option A auth/RLS, harden + deploy docs). This milestone adds optional `POST /explain`: a short explanation of incidents the deterministic engine already returned. It does **not** detect, score, or invent incidents. If `OPENAI_API_KEY` is unset, the API returns **503** and the UI does not show a fake explanation.

This repo does **not** auto-deploy to Gabby’s Vercel/Render/Supabase. Wire those accounts with [docs/deploy.md](docs/deploy.md). CI does not use live credentials.

## Complete vs not done (interview)

| | |
| --- | --- |
| **COMPLETE** | **M0** skeleton + CI |
| **COMPLETE** | **M1** TLAL parser + fixtures |
| **COMPLETE** | **M2** `brute_force`, `credential_spray` |
| **COMPLETE** | **M3** `unusual_login`, `impossible_travel` (simulated geo), `request_frequency`, `restricted_access` |
| **COMPLETE** | **M4** Supabase email auth + Postgres RLS (Option A; no `service_role` in the web app) |
| **COMPLETE** | **M5** investigation UI over **real** `/detect` output (no mock incident feed) |
| **COMPLETE** | **M6** harden + deploy docs (1 MiB body cap; POST `/parse`+`/detect` rate limit; CORS defaults; Next security headers; `api/Dockerfile`; [docs/deploy.md](docs/deploy.md)) |
| **COMPLETE** | **M7** AI explain-only (`POST /explain` summarizes existing incidents or a pasted detect response; **not** a detector; **503** if `OPENAI_API_KEY` is unset — no fake text) |
| **NOT DONE** | AI as a detector (will not be added — explain-only is the ceiling) |
| **NOT DONE** | Live log ingest / SIEM, real MaxMind GeoIP, production Redis rate limiting, org/shared access |

## Architecture (Option A)

```
Browser
  → FastAPI POST /detect     (stateless engine — the only thing that creates incidents)
  → FastAPI POST /explain    (optional prose over those incidents; 503 if no key)
  → FastAPI GET /rules       (live thresholds)
  → Supabase Auth + Postgres (CRUD saved runs; RLS = own rows only)
```

Option B (API holds the JWT and writes to Postgres) was not used so the detection service stays a pure function. Details: [docs/auth-persistence.md](docs/auth-persistence.md). Deploy: [docs/deploy.md](docs/deploy.md). Vercel root directory: [docs/vercel.md](docs/vercel.md).

## Roadmap

- **M1** — log parser and fixtures
- **M2** — detection engine: brute_force + credential_spray
- **M3** — more rules: unusual_login, impossible_travel (simulated), request_frequency, restricted_access
- **M4** — auth + RLS persistence
- **M5** — investigation UI over real detections
- **M6** — harden + deploy docs
- **M7** — AI explain-only (never the detector) *(this)*

## Pages (M5 UI, plus M7 Explain from evidence)

| Path | What it is |
| --- | --- |
| `/` | Honest landing: stack, implemented vs not |
| `/analyze` | Paste/upload TLAL or load a repo fixture → `POST /detect` → incidents + parse errors. **Explain from evidence** if incidents exist. Save if signed in |
| `/analyses` | Investigations list (your saved runs; severity counts from stored incidents) |
| `/analyses/[id]` | Investigation detail with severity / rule / status filters, readable evidence, and **Explain from evidence** |
| `/rules` | Live `GET /rules` catalog |
| `/login`, `/signup` | Supabase email/password |

## Run locally

Requires Node.js 22+ and Python 3.12+.

### 1. Supabase (once, for save/login)

1. Create a Supabase project.
2. Enable Email auth. For local/demo use, **disable Confirm email** so signup is immediate (say so if you leave it on).
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

- `GET http://127.0.0.1:8000/health` → `{"status":"ok"}` (no secrets)
- `GET http://127.0.0.1:8000/rules` → registered rule ids and thresholds
- `POST http://127.0.0.1:8000/parse` — raw log text → `{ "events": [...], "errors": [...] }`
- `POST http://127.0.0.1:8000/detect` — same body as `/parse` → `{ "events_count": N, "incidents": [...], "parse_errors": [...] }`
- `POST http://127.0.0.1:8000/explain` — `{ "incidents": [...], "context"?: "..." }` → `{ "explanation": "..." }`

`OPENAI_API_KEY` is **API-only**. Put it in `api/.env` locally or on Render. Never set `NEXT_PUBLIC_OPENAI_API_KEY` (or any `NEXT_PUBLIC_*` copy of the key) on Vercel — the browser must not see it. Optional `OPENAI_MODEL` (default `gpt-4o-mini`) and `OPENAI_BASE_URL` (OpenAI-compatible chat completions). If the key is missing, `/explain` returns **503** and the Explain button hides. Detection still works. The prompt may only use the evidence fields you send; it must not invent threats.

Bodies over **1 MiB** are `413`. POST `/parse`, `/detect`, and `/explain` share an in-memory rate limit (**60/minute/IP** by default). CORS defaults to `http://localhost:3000` and `http://127.0.0.1:3000` only — set `CORS_ORIGINS` for a hosted UI. See `api/.env.example`. Gabby’s Render steps: [docs/deploy.md](docs/deploy.md).

```bash
# From the repo root, with the API running on :8000
curl -sS -X POST http://127.0.0.1:8000/detect \
  -H 'Content-Type: text/plain' \
  --data-binary @fixtures/bruteforce/auth.log
```

Docker (Render/Railway/Fly): `docker build -t threatlens-api ./api` then run with `PORT` and `CORS_ORIGINS`.

### 3. Web (`web/`)

```bash
cd web
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). Analyze a fixture, inspect evidence, sign in, save, open Investigations.

**Vercel:** import the repo, set **Root Directory = `web`**. Do not add a root `vercel.json` (monorepo). Full Gabby steps: [docs/deploy.md](docs/deploy.md).

Parser: [docs/log-schema.md](docs/log-schema.md). Detection: [docs/detection.md](docs/detection.md). Auth/RLS: [docs/auth-persistence.md](docs/auth-persistence.md). Samples: [fixtures/README.md](fixtures/README.md).

### Tests

```bash
cd api
pip install -r requirements.txt
pytest
```

Pytest covers the engine, a static SQL/RLS check, and M6 file checks (Dockerfile, deploy docs, no `service_role` in web source). It does **not** need Supabase credentials.

```bash
cd web
npm ci
npm run build
```

## Interview demo path

1. Landing — explain Option A (stateless FastAPI, RLS in Next.js). Point at Implemented vs Not. M7 is explain-only; there is still no AI detector.
2. Rules — live `GET /rules` (if the API is up). Thresholds come from the engine.
3. Analyze — load **normal** (expect 0 incidents, no Explain button), then **brute_force**. Expand evidence JSON. Click **Explain from evidence** (not “AI detected”). With `OPENAI_API_KEY` on the API, the prose restates that incident. Without the key, the button hides after HTTP 503 and no explanation appears. Load **edge** to show parse errors.
4. Sign in → Save → Investigations list (severity chips from saved rows) → detail filters → Explain from evidence on the saved incidents.

Do not show a threat map. `impossible_travel` is simulated `country=` / TEST-NET prefixes, not MaxMind.

Hosted smoke (after [docs/deploy.md](docs/deploy.md)): landing → rules → analyze fixture → signup → save → analyses.

## Thresholds (M3 defaults, unchanged in M4–M7)

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

This is not a production detection platform. It finds the patterns above in **synthetic TLAL** fixtures, then stores them per user. It does not ingest live logs, perform real geolocation, learn baselines, or invent SOC noise for the UI. Explain-only text is optional and is not a finding. Rate limiting is in-memory per API instance — enough for a demo dyno, not a multi-region WAF.
