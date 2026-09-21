import Link from "next/link";

import { formatUtc, incidentCountLabel } from "@/lib/format";

export type AnalysisListItem = {
  id: string;
  title: string | null;
  created_at: string;
  incident_count: number;
};

export function AnalysesList({ items }: { items: AnalysisListItem[] }) {
  if (items.length === 0) {
    return (
      <p className="text-sm text-zinc-600">
        No saved analyses yet. Run detection and save a result.
      </p>
    );
  }

  return (
    <ul className="divide-y divide-zinc-200 rounded-lg border border-zinc-200 bg-white">
      {items.map((item) => (
        <li key={item.id}>
          <Link
            href={`/analyses/${item.id}`}
            className="flex items-baseline justify-between gap-4 px-4 py-3 hover:bg-zinc-50"
          >
            <span className="font-medium text-zinc-900">
              {item.title?.trim() || "Untitled analysis"}
            </span>
            <span className="shrink-0 text-sm text-zinc-600">
              {formatUtc(item.created_at)} · {incidentCountLabel(item.incident_count)}
            </span>
          </Link>
        </li>
      ))}
    </ul>
  );
}
