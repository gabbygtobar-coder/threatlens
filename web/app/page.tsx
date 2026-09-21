import { AnalysesList, type AnalysisListItem } from "@/components/AnalysesList";
import { DetectAndSave } from "@/components/DetectAndSave";
import { SetupNeeded } from "@/components/SetupNeeded";
import { getCurrentUser } from "@/lib/auth";
import { isSupabaseConfigured } from "@/lib/env";
import { createClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

export default async function Home() {
  if (!isSupabaseConfigured()) {
    return <SetupNeeded />;
  }

  const user = await getCurrentUser();
  if (!user) {
    return (
      <main className="mx-auto max-w-3xl px-6 py-12">
        <h1 className="text-3xl font-semibold tracking-tight">ThreatLens</h1>
        <p className="mt-4 max-w-xl text-zinc-600">
          Sign in to paste a log, run the FastAPI detection engine, and save the
          result to your account. There is no mock incident dashboard.
        </p>
        <p className="mt-4 text-sm text-zinc-600">
          Six deterministic rules live in <code>api/</code>. Persistence is
          Supabase + RLS (M4).
        </p>
      </main>
    );
  }

  const { items, loadError } = await loadAnalyses(user.id);

  return (
    <main className="mx-auto max-w-3xl space-y-10 px-6 py-10">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">ThreatLens</h1>
        <p className="mt-2 text-sm text-zinc-600">
          Signed in as {user.email}. Detection is FastAPI; this page only stores
          what you save.
        </p>
      </div>
      <DetectAndSave userId={user.id} />
      <section>
        <h2 className="mb-3 text-lg font-semibold">Saved analyses</h2>
        {loadError ? (
          <p className="text-sm text-red-700">
            Could not load analyses ({loadError}). If this is a new Supabase
            project, run the SQL in supabase/migrations/.
          </p>
        ) : (
          <AnalysesList items={items} />
        )}
      </section>
    </main>
  );
}

async function loadAnalyses(
  userId: string,
): Promise<{ items: AnalysisListItem[]; loadError: string | null }> {
  const supabase = await createClient();
  const { data, error } = await supabase
    .from("analyses")
    .select("id, title, created_at, incidents(count)")
    .eq("user_id", userId)
    .order("created_at", { ascending: false });

  if (error) {
    return { items: [], loadError: error.message };
  }

  return {
    loadError: null,
    items: (data ?? []).map((row) => {
      const nested = row.incidents as { count: number }[] | { count: number } | null;
      const count = Array.isArray(nested) ? nested[0]?.count : nested?.count;
      return {
        id: row.id,
        title: row.title,
        created_at: row.created_at,
        incident_count: count ?? 0,
      };
    }),
  };
}
