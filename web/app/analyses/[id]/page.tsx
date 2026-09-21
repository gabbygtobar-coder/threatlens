import type { Metadata } from "next";
import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import { DeleteAnalysisButton } from "@/components/DeleteAnalysisButton";
import { InvestigationIncidents } from "@/components/InvestigationIncidents";
import { SetupNeeded } from "@/components/SetupNeeded";
import { getCurrentUser } from "@/lib/auth";
import { isSupabaseConfigured } from "@/lib/env";
import {
  eventCountLabel,
  formatUtc,
  incidentCountLabel,
  parseErrorCountLabel,
} from "@/lib/format";
import { fromIncidentRow } from "@/lib/incidents";
import { createClient } from "@/lib/supabase/server";

export const metadata: Metadata = {
  title: "Investigation",
};

export const dynamic = "force-dynamic";

export default async function AnalysisDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  if (!isSupabaseConfigured()) {
    return <SetupNeeded purpose="Investigation detail reads your saved analyses from Supabase." />;
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

  const rows = (incidents ?? []).map(fromIncidentRow);

  return (
    <main className="mx-auto max-w-5xl space-y-6 px-4 py-10 sm:px-6">
      <p className="text-sm">
        <Link href="/analyses" className="text-zinc-400 hover:text-zinc-50">
          ← Investigations
        </Link>
      </p>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-50">
            {analysis.title?.trim() || "Untitled analysis"}
          </h1>
          <p className="mt-2 text-sm text-zinc-400">
            Saved {formatUtc(analysis.created_at)} · {eventCountLabel(analysis.events_count)} ·{" "}
            {parseErrorCountLabel(analysis.parse_errors_count)} · {incidentCountLabel(rows.length)}
          </p>
        </div>
        <DeleteAnalysisButton analysisId={analysis.id} />
      </div>

      <InvestigationIncidents
        incidents={rows}
        emptyMessage="No incidents were stored for this run. The original log is still saved. That can happen for the normal fixture or any log that does not meet a rule threshold."
      />

      <details>
        <summary className="cursor-pointer text-sm text-zinc-300 hover:text-zinc-50">
          Raw log text
        </summary>
        <pre className="mt-2 max-h-96 overflow-auto rounded-md border border-zinc-800 bg-zinc-950 p-3 font-mono text-xs text-zinc-300">
          {analysis.raw_log_text || "(empty)"}
        </pre>
      </details>
    </main>
  );
}
