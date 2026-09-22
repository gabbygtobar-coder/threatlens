# ThreatLens web

Next.js App Router frontend (M5 UI, M6 harden, M7 explain button): landing page,
email/password auth, paste or upload a log, call FastAPI `/detect`, save under
Supabase RLS, investigations list/detail with filters, live `GET /rules` catalog.
**Explain from evidence** calls `POST /explain` with the incidents already on
screen. It is not a detector. The OpenAI key is not a web env var.

Security headers are set in `next.config.ts`. There is no mock incident feed,
no in-browser detector, and no `service_role` key.

From this directory:

```bash
cp .env.example .env.local
# set NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY, NEXT_PUBLIC_API_URL
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

- Without Supabase env the app still builds. Landing, Analyze, and Rules work;
  login/save/investigations show a setup page.
- Without `NEXT_PUBLIC_API_URL` Analyze and Rules fail honestly (no demo mode).

**Vercel:** set **Root Directory** to `web`. Do not add `vercel.json` at the repo
root (this is a monorepo; a root config would fight `api/`). Gabby steps:
[docs/deploy.md](../docs/deploy.md). Vercel env table: [docs/vercel.md](../docs/vercel.md).
