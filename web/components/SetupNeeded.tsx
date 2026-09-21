export function SetupNeeded() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-12">
      <h1 className="text-2xl font-semibold tracking-tight">Supabase is not configured</h1>
      <p className="mt-3 max-w-xl text-zinc-600">
        M4 persistence needs a Supabase project. Copy{" "}
        <code className="rounded bg-zinc-100 px-1 py-0.5 text-sm">web/.env.example</code>{" "}
        to{" "}
        <code className="rounded bg-zinc-100 px-1 py-0.5 text-sm">web/.env.local</code>{" "}
        and set:
      </p>
      <ul className="mt-4 list-disc space-y-1 pl-5 text-sm text-zinc-700">
        <li>
          <code>NEXT_PUBLIC_SUPABASE_URL</code>
        </li>
        <li>
          <code>NEXT_PUBLIC_SUPABASE_ANON_KEY</code>
        </li>
        <li>
          <code>NEXT_PUBLIC_API_URL</code> (FastAPI, default{" "}
          <code>http://127.0.0.1:8000</code>)
        </li>
      </ul>
      <p className="mt-4 text-sm text-zinc-600">
        Do not put the service role key in the web app. Run the SQL in{" "}
        <code className="rounded bg-zinc-100 px-1 py-0.5">supabase/migrations/</code>{" "}
        on the project. Details: <code>docs/auth-persistence.md</code>.
      </p>
    </main>
  );
}
