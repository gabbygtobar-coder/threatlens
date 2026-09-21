# Vercel (web UI)

Full Gabby order (Supabase → API → Vercel → smoke): [deploy.md](deploy.md).

Gabby authorized Vercel for **visuals**. The detection API is still a separate FastAPI process. Do not claim a production API is live unless it is actually deployed and `NEXT_PUBLIC_API_URL` points at it.

**Do not add `vercel.json` at the repo root.** Root Directory `web` is the Vercel project setting that keeps `api/` out of the Next.js build.

## Project settings

| Setting | Value |
| --- | --- |
| Root Directory | `web` |
| Framework | Next.js |
| Build | `npm run build` (default) |
| Node | 22.x |

## Environment variables

Set these on the Vercel project (Production / Preview as needed). They are `NEXT_PUBLIC_*`, so they are inlined at **build** time — change then redeploy.

| Name | Required for | Notes |
| --- | --- | --- |
| `NEXT_PUBLIC_SUPABASE_URL` | Login, save, investigations | Project URL. Omit to ship a read-only visual (landing / analyze / rules still render). |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Login, save, investigations | Anon / publishable key only. Never `service_role`. |
| `NEXT_PUBLIC_API_URL` | Analyze, Rules | Public FastAPI origin, e.g. `https://something.onrender.com`. **Not** `http://127.0.0.1:8000` — visitors' browsers cannot reach your laptop. If unset or fetch fails, the UI shows an error. There is no mock engine. |

CI sets `NEXT_PUBLIC_API_URL=http://127.0.0.1:8000` only so `next build` has a value. That does not mean a production API exists.

## API CORS

The browser calls FastAPI directly (Option A). On the API host, set:

```
CORS_ORIGINS=https://YOUR-DEPLOYMENT.vercel.app,http://localhost:3000,http://127.0.0.1:3000
```

Include Preview URLs if you use them. See `api/.env.example`.

## If the API is not deployed yet

Ship the UI anyway. Analyze and Rules will fail with a readable message (`NEXT_PUBLIC_API_URL` missing, or fetch/CORS error). Landing copy does not pretend the engine is a hosted production service.
