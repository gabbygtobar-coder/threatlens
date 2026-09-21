import Link from "next/link";

export function SetupNeeded({ purpose }: { purpose: string }) {
  return (
    <main className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
      <h1 className="text-2xl font-semibold tracking-tight text-zinc-50">
        Supabase is not configured
      </h1>
      <p className="mt-3 max-w-xl text-zinc-400">
        {purpose} Copy{" "}
        <code className="rounded bg-zinc-900 px-1 py-0.5 font-mono text-sm text-zinc-200">
          web/.env.example
        </code>{" "}
        to{" "}
        <code className="rounded bg-zinc-900 px-1 py-0.5 font-mono text-sm text-zinc-200">
          web/.env.local
        </code>{" "}
        (or set the same keys on Vercel) and apply the SQL migration. The landing page, Analyze, and
        Rules still work without auth — they just cannot save.
      </p>
      <ul className="mt-4 list-disc space-y-1 pl-5 text-sm text-zinc-300">
        <li>
          <code className="font-mono">NEXT_PUBLIC_SUPABASE_URL</code>
        </li>
        <li>
          <code className="font-mono">NEXT_PUBLIC_SUPABASE_ANON_KEY</code> (anon / publishable only)
        </li>
        <li>
          <code className="font-mono">NEXT_PUBLIC_API_URL</code> — FastAPI origin. Local default in{" "}
          <code className="font-mono">.env.example</code> is <code className="font-mono">http://127.0.0.1:8000</code>.
          A Vercel UI needs a public API URL.
        </li>
      </ul>
      <p className="mt-4 text-sm text-zinc-500">
        Never put the service role key in the web app. Details:{" "}
        <code className="font-mono">docs/auth-persistence.md</code>.
      </p>
      <p className="mt-6 text-sm">
        <Link href="/" className="text-sky-400 hover:text-sky-300">
          ← Back to landing
        </Link>
      </p>
    </main>
  );
}
