# Auth and persistence (M4, used by M5)

## Architecture: Option A

ThreatLens splits detection and storage on purpose so the Python engine stays
easy to explain in an interview.

```
Browser (Next.js, web/)
  ├─ Supabase Auth (email/password) — session cookie
  ├─ POST FastAPI /detect            — parse + six rules, no DB
  └─ Supabase Postgres               — insert/select analyses + incidents
                                      with the user JWT (anon key + RLS)

FastAPI (api/)  — stateless. /health /parse /detect /rules only.
                  Does not see the user, does not store rows.
```

**Option B** (not used) would have been: FastAPI validates the Supabase JWT and
writes to Postgres itself. That couples the engine to auth and secrets. Option A
keeps `api/` a pure function over log text.

The Next.js app is the only process that holds the **anon / publishable** key.
The **service role** key must never be in the client, in `NEXT_PUBLIC_*` env, or
in this repo.

## Data model

| Table | Purpose |
| --- | --- |
| `profiles` | `id` = `auth.users.id`. Optional `display_name`. Created by a trigger on signup. |
| `analyses` | One saved `/detect` run: `user_id`, `title`, `raw_log_text`, `events_count`, `parse_errors_count`. |
| `incidents` | Findings for that run. Row `id` is a UUID. `engine_incident_id` is the deterministic SHA-256 prefix from FastAPI. `evidence` is JSONB. `created_at` is the engine window end, not save time. |

SQL: [`supabase/migrations/`](../supabase/migrations/).

## RLS

Every table has Row Level Security enabled. Policies are `to authenticated`
only; `anon` has no table grants that bypass this.

- `profiles`: `id = auth.uid()`
- `analyses`: `user_id = auth.uid()`
- `incidents`: `user_id = auth.uid()`, and **insert/update** also require the
  parent `analyses` row to belong to the same user

Users can CRUD only their own rows. There is no shared/org access in M4.

`(select auth.uid())` is used so Postgres can treat the uid as a stable
initPlan instead of calling it per row.

## Create a Supabase project (Gabby)

This agent VM does not have Gabby’s Supabase credentials. Wire the project once:

1. Create a project at [https://supabase.com/dashboard](https://supabase.com/dashboard).
2. **Authentication → Providers → Email** enabled.
3. **Local convenience:** Authentication → Providers → Email → turn **Confirm
   email** off so signup returns a session immediately. If you leave it on,
   the UI tells you to check your inbox; that is expected, not a bug.
4. **SQL editor:** paste and run
   `supabase/migrations/20260921120000_init_auth_persistence.sql`
   (or `supabase db push` if you use the CLI and have linked the project).
5. **Project Settings → API:** copy **Project URL** and **anon public** key
   (sometimes labeled publishable). Do **not** copy `service_role`.

`web/.env.local`:

```
NEXT_PUBLIC_SUPABASE_URL=https://YOUR_PROJECT.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

Restart `npm run dev` after changing env.

## Run web + API

Terminal 1:

```bash
cd api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Terminal 2:

```bash
cd web
cp .env.example .env.local   # then fill real values
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). Sign up, Analyze a fixture
from `fixtures/` (or the Analyze page sample buttons), save, open Investigations.

## CORS (API)

The browser calls FastAPI from the web origin, so the API sends CORS headers.

Default allow-list: `http://localhost:3000`, `http://127.0.0.1:3000`.

Production: set `CORS_ORIGINS` on the API process to the deployed web origin
(comma-separated). Example: `https://your-app.vercel.app`. Do not put the
service role key on the API either — it does not need one under Option A.

## What this layer is not

- No AI.
- No live log ingest.
- No mock incident widgets — M5 lists only saved `/detect` rows.
- CI does **not** talk to Supabase. Detection tests and a static SQL/RLS check
  run without secrets. End-to-end save/load requires Gabby’s project env.
  Deploy: [deploy.md](deploy.md). Vercel notes: [vercel.md](vercel.md).
