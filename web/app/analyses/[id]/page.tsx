import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import { DeleteAnalysisButton } from "@/components/DeleteAnalysisButton";
import { IncidentCard } from "@/components/IncidentCard";
import { SetupNeeded } from "@/components/SetupNeeded";
import { getCurrentUser } from "@/lib/auth";
import { isSupabaseConfigured } from "@/lib/env";
import { formatUtc, incidentCountLabel } from "@/lib/format";
import { createClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

export default async function AnalysisDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  if (!isSupabaseConfigured()) {
    return <SetupNeeded />;
  }

  const user = await getCurrentUser();
  if (!user) {
    const { id } = await params;
    redirect(`/login?next=/analyses/${id}`);
  }

  const { id } = await params;
  const supabase = await createClient();
  const { data: analysis, error } = await supabase
    .from("analyses")
    .select(
      "id, title, created_at, events_count, parse_errors_count, raw_log_text, user_id",
    )
    .eq("id", id)
    .maybeSingle();

  if (error || !analysis || analysis.user_id !== user.id) {
    notFound();
  }

  const { data: incidents } = await supabase
    .from("incidents")
    .select(
      "id, analysis_id, user_id, engine_incident_id, rule_id, severity, status, title, description, evidence, created_at",
    )
    .eq("analysis_id", id)
    .order("created_at", { ascending: true });

  const rows = incidents ?? [];

  return (
    <main className="mx-auto max-w-3xl space-y-6 px-6 py-10">
      <p className="text-sm">
        <Link href="/" className="text-zinc-700 underline hover:text-zinc-900">
          ← Saved analyses
        </Link>
      </p>
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            {analysis.title?.trim() || "Untitled analysis"}
          </h1>
          <p className="mt-2 text-sm text-zinc-600">
            Saved {formatUtc(analysis.created_at)} · {analysis.events_count} events ·{" "}
            {analysis.parse_errors_count} parse errors · {incidentCountLabel(rows.length)}
          </p>
        </div>
        <DeleteAnalysisButton analysisId={analysis.id} />
      </div>

      {rows.length === 0 ? (
        <p className="text-sm text-zinc-600">
          No incidents were stored for this run. The original log is still saved.
        </p>
      ) : (
        <section className="space-y-4">
          {rows.map((incident) => (
            <IncidentCard key={incident.id} incident={incident} />
          ))}
        </section>
      )}

      <details>
        <summary className="cursor-pointer text-sm text-zinc-700">Raw log text</summary>
        <pre className="mt-2 max-h-96 overflow-auto rounded-md bg-white p-3 text-xs text-zinc-800 ring-1 ring-zinc-200">
          {analysis.raw_log_text || "(empty)"}
        </pre>
      </details>
    </main>
  );
}
