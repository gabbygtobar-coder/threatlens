import Link from "next/link";

import type { AnalysisListItem } from "@/lib/incidents";
import { eventCountLabel, formatUtc, incidentCountLabel } from "@/lib/format";
import { nonZeroSeverityEntries } from "@/lib/incidents";

import { SeverityBadge } from "@/components/ui/badge";

export type { AnalysisListItem };

export function AnalysesList({ items }: { items: AnalysisListItem[] }) {
  if (items.length === 0) {
    return (
      <p className="text-sm text-zinc-400">
        No saved analyses yet. Run detection on the Analyze page and save a result. This list is
        empty because your account has no rows — not because of placeholder data.
      </p>
    );
  }

  return (
    <ul className="divide-y divide-zinc-800 rounded-xl border border-zinc-800 bg-zinc-900/80">
      {items.map((item) => {
        const severities = nonZeroSeverityEntries(item.severity_counts);
        return (
          <li key={item.id}>
            <Link
              href={`/analyses/${item.id}`}
              className="flex flex-col gap-2 px-4 py-3 hover:bg-zinc-800/40 sm:flex-row sm:items-center sm:justify-between"
            >
              <span>
                <span className="block font-medium text-zinc-50">
                  {item.title?.trim() || "Untitled analysis"}
                </span>
                <span className="mt-1 block text-xs text-zinc-500">
                  {formatUtc(item.created_at)} · {eventCountLabel(item.events_count)} ·{" "}
                  {incidentCountLabel(item.incident_count)}
                </span>
              </span>
              <span className="flex flex-wrap items-center gap-1.5">
                {item.incident_count === 0 ? (
                  <span className="text-xs text-zinc-500">no incidents</span>
                ) : (
                  severities.map((entry) => (
                    <span key={entry.label} className="inline-flex items-center gap-1">
                      <SeverityBadge severity={entry.label} />
                      <span className="font-mono text-xs text-zinc-400">{entry.count}</span>
                    </span>
                  ))
                )}
              </span>
            </Link>
          </li>
        );
      })}
    </ul>
  );
}
