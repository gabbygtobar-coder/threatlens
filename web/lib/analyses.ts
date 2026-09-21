import {
  countSeverities,
  type AnalysisListItem,
} from "@/lib/incidents";
import { createClient } from "@/lib/supabase/server";

export type { AnalysisListItem };

export async function loadAnalyses(
  userId: string,
): Promise<{ items: AnalysisListItem[]; loadError: string | null }> {
  const supabase = await createClient();
  const { data, error } = await supabase
    .from("analyses")
    .select(
      "id, title, created_at, events_count, parse_errors_count, incidents(severity)",
    )
    .eq("user_id", userId)
    .order("created_at", { ascending: false });

  if (error) {
    return { items: [], loadError: error.message };
  }

  return {
    loadError: null,
    items: (data ?? []).map((row) => {
      const nested = row.incidents as unknown as { severity: string }[] | { severity: string } | null;
      const severities = Array.isArray(nested)
        ? nested.map((item) => item.severity)
        : nested
          ? [nested.severity]
          : [];
      return {
        id: row.id,
        title: row.title,
        created_at: row.created_at,
        events_count: row.events_count,
        parse_errors_count: row.parse_errors_count,
        incident_count: severities.length,
        severity_counts: countSeverities(severities),
      };
    }),
  };
}
