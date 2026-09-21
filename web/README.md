# ThreatLens web

Next.js App Router frontend for M4: email/password auth, paste/upload a log,
call FastAPI `/detect`, save the result to Supabase under RLS, list past
analyses, open a basic detail page.

There is no investigation dashboard and no mock data.

From this directory:

```bash
cp .env.example .env.local
# set NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY, NEXT_PUBLIC_API_URL
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). Without Supabase env the
app still builds and shows a setup page. See the repository root README and
[docs/auth-persistence.md](../docs/auth-persistence.md).
