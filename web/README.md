# ThreatLens web

Next.js App Router frontend for M5: landing page, email/password auth, paste or
upload a log, call FastAPI `/detect`, save under Supabase RLS, investigations
list/detail with filters, live `GET /rules` catalog.

There is no mock incident feed and no in-browser detector.

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

Vercel: set Root Directory to `web`. See the repository root README.
