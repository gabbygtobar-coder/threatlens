import Link from "next/link";

import { ApiStatus } from "@/components/ApiStatus";

export function LandingPage({
  email,
  supabaseConfigured,
}: {
  email: string | null;
  supabaseConfigured: boolean;
}) {
  return (
    <main className="mx-auto max-w-5xl px-4 py-12 sm:px-6">
      <p className="font-mono text-xs uppercase tracking-[0.2em] text-sky-400">
        Detection-first log analysis
      </p>
      <h1 className="mt-3 max-w-2xl text-4xl font-semibold tracking-tight text-zinc-50 sm:text-5xl">
        ThreatLens
      </h1>
      <p className="mt-4 max-w-2xl text-lg text-zinc-400">
        Paste an auth/access log. A FastAPI engine runs six deterministic rules and returns
        incidents with evidence. Sign in to save a run. There is no AI detector, no live SIEM, and
        no fake global threat map.
      </p>
      <div className="mt-8 flex flex-wrap gap-3">
        <Link
          href="/analyze"
          className="inline-flex h-10 items-center rounded-md bg-sky-500 px-4 text-sm font-medium text-zinc-950 hover:bg-sky-400"
        >
          Analyze a log
        </Link>
        <Link
          href="/rules"
          className="inline-flex h-10 items-center rounded-md border border-zinc-700 bg-zinc-900 px-4 text-sm font-medium text-zinc-100 hover:bg-zinc-800"
        >
          View rule thresholds
        </Link>
        {email ? (
          <Link
            href="/analyses"
            className="inline-flex h-10 items-center rounded-md border border-zinc-700 px-4 text-sm font-medium text-zinc-100 hover:bg-zinc-800"
          >
            Your investigations
          </Link>
        ) : supabaseConfigured ? (
          <Link
            href="/login"
            className="inline-flex h-10 items-center px-4 text-sm font-medium text-sky-400 hover:text-sky-300"
          >
            Log in to save runs
          </Link>
        ) : null}
      </div>

      <div className="mt-8 max-w-2xl">
        <ApiStatus compact />
      </div>

      <section className="mt-14 grid gap-6 md:grid-cols-3">
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
          <h2 className="text-sm font-semibold text-zinc-50">Stack</h2>
          <ul className="mt-3 space-y-2 text-sm text-zinc-400">
            <li>FastAPI parser + detection engine</li>
            <li>Next.js App Router UI</li>
            <li>Supabase Auth + Postgres RLS</li>
            <li>Option A: engine stays stateless</li>
          </ul>
        </div>
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
          <h2 className="text-sm font-semibold text-zinc-50">Implemented (M0–M6)</h2>
          <ul className="mt-3 space-y-2 text-sm text-zinc-400">
            <li>TLAL parser and six rules</li>
            <li>Email/password auth + RLS save</li>
            <li>Investigation UI over real /detect output</li>
            <li>Live GET /rules catalog</li>
            <li>Deploy docs, 1 MiB body cap, POST rate limit</li>
          </ul>
        </div>
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
          <h2 className="text-sm font-semibold text-zinc-50">Not this product</h2>
          <ul className="mt-3 space-y-2 text-sm text-zinc-400">
            <li>M7 AI explain-only — not started</li>
            <li>No MaxMind / real GeoIP</li>
            <li>No live log streaming</li>
            <li>No mock incident feed or charts</li>
            <li>
              <code className="font-mono text-zinc-300">impossible_travel</code> uses simulated geo
            </li>
          </ul>
        </div>
      </section>

      <section className="mt-14 max-w-3xl">
        <h2 className="text-lg font-semibold text-zinc-50">How a run works</h2>
        <ol className="mt-4 list-decimal space-y-2 pl-5 text-sm text-zinc-400">
          <li>
            Browser sends log text to FastAPI <code className="font-mono text-zinc-300">POST /detect</code>.
          </li>
          <li>Engine parses TLAL, runs the six rules, returns incidents + parse errors.</li>
          <li>If you are signed in, Save writes that payload to your Supabase rows (RLS).</li>
          <li>Investigations lists only your saved analyses. Empty means you have not saved yet.</li>
        </ol>
      </section>
    </main>
  );
}
