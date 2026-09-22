# Deploy ThreatLens (Gabby)

M7 adds optional explain-only on the API. This agent does not log into your
Vercel / Render / Supabase accounts. Follow A → D in order. There is still no
AI detector and no mock detector. Explain only summarizes incidents `/detect`
already returned.

Chicken-and-egg: the API needs the Vercel origin in `CORS_ORIGINS`, and Vercel
needs the public API URL in `NEXT_PUBLIC_API_URL`. Deploy the API first (localhost
CORS is enough to boot), import the web app, then **put the Vercel URL on the API
and restart**, then **set the API URL on Vercel and redeploy**.

## A. Supabase

1. Create a project at [https://supabase.com/dashboard](https://supabase.com/dashboard).
2. **Authentication → Providers → Email**: enabled.
3. **Demo convenience:** turn **Confirm email** **off** so signup returns a session
   immediately. If you leave it on, the UI tells you to check your inbox — that is
   expected, not a bug.
4. **SQL editor:** paste and run
   [`supabase/migrations/20260921120000_init_auth_persistence.sql`](../supabase/migrations/20260921120000_init_auth_persistence.sql).
5. **Project Settings → API:** copy **Project URL** and **anon / publishable** key.
   Never copy `service_role`. The web app uses the anon key + RLS only (Option A).
   The FastAPI process does not get a Supabase key.

## B. API (FastAPI)

Public **HTTPS** origin required. Visitors' browsers cannot reach `127.0.0.1`.

Use `api/Dockerfile` (Render / Railway / Fly Docker) **or** a native Python
service with root directory `api/`:

| Setting | Value |
| --- | --- |
| Build | `pip install -r requirements.txt` (or Docker build from `api/`) |
| Start | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health | `GET /health` → `{"status":"ok"}` |

Environment:

```
CORS_ORIGINS=https://YOUR-APP.vercel.app,http://localhost:3000,http://127.0.0.1:3000
```

- Default if unset: **localhost only** (intentional). The Vercel origin will fail
  CORS until you set this and restart.
- Do **not** use `*` unless you are debugging. Prefer the exact `https://…vercel.app`
  URL (and Preview URLs if you use them).
- Optional: `RATE_LIMIT_REQUESTS` / `RATE_LIMIT_WINDOW_SECONDS` (defaults **60 POST
  /parse|/detect|/explain per IP per 60s**, in-memory, per instance). `RATE_LIMIT_ENABLED=false`
  disables it.
- Bodies over **1 MiB** are `413`. That bound is a code constant, not an env var.

### Optional: Explain from evidence (M7)

`OPENAI_API_KEY` belongs on the **API** (Render) only. Do not add it to Vercel.
Do not create `NEXT_PUBLIC_OPENAI_API_KEY`. The Next.js bundle must not contain the key.

1. Render dashboard → your API web service → **Environment**.
2. Add **Environment Variable**: key `OPENAI_API_KEY`, value your OpenAI secret.
   Mark it secret if Render offers that. Do not commit it.
3. Optional: `OPENAI_MODEL` (default `gpt-4o-mini`). Optional: `OPENAI_BASE_URL`
   if you use an OpenAI-compatible chat completions endpoint.
4. Save. Render restarts the service. You do not need to redeploy Vercel for this
   key — the browser already calls the API.

If the variable is missing, `POST /explain` returns **503**. Analyze and the
investigation page hide **Explain from evidence** and do not invent text.
`/detect` is unchanged either way.

Confirm the process is up, and that explain fails closed until the key is set
(503, no `explanation` field):

```bash
curl -sf https://YOUR-API-HOST/health
curl -sf https://YOUR-API-HOST/rules
curl -sS -o /dev/null -w '%{http_code}\n' -X POST https://YOUR-API-HOST/explain \
  -H 'Content-Type: application/json' \
  -d '{"incidents":[{"rule_id":"brute_force","severity":"high","title":"Brute force","description":"50 failures","evidence":{"source_ip":"203.0.113.77","failure_count":50}}]}'
```

The API does not log request bodies or env dumps. It still does not get a
Supabase key. The only secret it should hold for this milestone is
`OPENAI_API_KEY`.

## C. Vercel (web)

1. Import [https://github.com/gabbygtobar-coder/threatlens](https://github.com/gabbygtobar-coder/threatlens).
2. **Root Directory = `web`**. Do not add a root `vercel.json` — that would fight
   the monorepo. Framework: Next.js. Node 22. Default `npm run build` is fine.
   Details: [vercel.md](vercel.md).
3. Environment variables (`NEXT_PUBLIC_*` are inlined at **build** time — change
   then **redeploy**):

| Name | Value |
| --- | --- |
| `NEXT_PUBLIC_API_URL` | Public FastAPI HTTPS origin from B (no trailing slash). **Not** `http://127.0.0.1:8000`. |
| `NEXT_PUBLIC_SUPABASE_URL` | From A |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Anon / publishable only |

4. After you have the production URL, go back to B and make sure `CORS_ORIGINS`
   includes it, then restart the API.

Without Supabase env, landing / Analyze / Rules still render; login and save
show a setup page. Without a reachable API, Analyze / Rules fail honestly — no
demo-mode fallback.

## D. Smoke checklist

Use the **Vercel URL** (not localhost) after CORS is updated.

1. **Landing** (`/`) — stack copy, Implemented vs Not, API status (live `/health` or an honest error).
2. **Rules** (`/rules`) — live `GET /rules` lists the six thresholds. Not a mock catalog.
3. **Analyze** (`/analyze`) — load **normal** (0 incidents, no Explain button), then **brute_force** (incidents + evidence). Click **Explain from evidence**. With the Render key set, you get prose about that incident. Without it, the button hides after HTTP 503 and no fake explanation appears. Optional: **edge** for parse errors.
4. **Sign up** — create an account. If Confirm email is off, you should land in-session.
5. **Save** — save the brute_force run.
6. **Investigations** (`/analyses`) — the saved row appears; open it, filters work, raw log is there. **Explain from evidence** is on the detail page for those saved incidents.

If Analyze fails with CORS / fetch: `CORS_ORIGINS` missing the Vercel origin, or
`NEXT_PUBLIC_API_URL` still pointing at localhost (rebuild required after env change).
