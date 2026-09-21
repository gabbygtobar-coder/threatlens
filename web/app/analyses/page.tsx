import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";

import { AnalysesList } from "@/components/AnalysesList";
import { SetupNeeded } from "@/components/SetupNeeded";
import { loadAnalyses } from "@/lib/analyses";
import { getCurrentUser } from "@/lib/auth";
import { isSupabaseConfigured } from "@/lib/env";

export const metadata: Metadata = {
  title: "Investigations",
};

export const dynamic = "force-dynamic";

export default async function InvestigationsPage() {
  if (!isSupabaseConfigured()) {
    return (
      <SetupNeeded purpose="Investigations lists analyses saved under your Supabase account." />
    );
  }

  const user = await getCurrentUser();
  if (!user) {
    redirect("/login?next=/analyses");
  }

  const { items, loadError } = await loadAnalyses(user.id);

  return (
    <main className="mx-auto max-w-5xl space-y-6 px-4 py-10 sm:px-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-zinc-50">Investigations</h1>
          <p className="mt-2 max-w-2xl text-sm text-zinc-400">
            Saved <code className="font-mono">/detect</code> runs for {user.email}. Counts and
            severity chips come from your incident rows, not from a dashboard seed file.
          </p>
        </div>
        <Link
          href="/analyze"
          className="inline-flex h-9 items-center rounded-md bg-sky-500 px-3 text-sm font-medium text-zinc-950 hover:bg-sky-400"
        >
          New analysis
        </Link>
      </div>
      {loadError ? (
        <p className="text-sm text-red-300">
          Could not load analyses ({loadError}). If this is a new Supabase project, run the SQL in
          supabase/migrations/.
        </p>
      ) : (
        <AnalysesList items={items} />
      )}
    </main>
  );
}
