import { formatUtc } from "@/lib/format";
import type { IncidentView } from "@/lib/incidents";

import { EvidenceView } from "@/components/EvidenceView";
import { SeverityBadge } from "@/components/ui/badge";

export function IncidentCard({ incident }: { incident: IncidentView }) {
  return (
    <article className="rounded-xl border border-zinc-800 bg-zinc-900/80 p-4">
      <div className="flex flex-wrap items-center gap-2">
        <SeverityBadge severity={incident.severity} />
        <span className="font-mono text-xs text-zinc-400">{incident.rule_id}</span>
        <span className="font-mono text-xs text-zinc-500">{incident.status}</span>
      </div>
      <h3 className="mt-2 text-base font-semibold text-zinc-50">{incident.title}</h3>
      <p className="mt-1 text-xs text-zinc-500">{formatUtc(incident.created_at)}</p>
      {incident.engine_incident_id ? (
        <p className="mt-1 font-mono text-[11px] text-zinc-500">
          engine id {incident.engine_incident_id}
        </p>
      ) : null}
      <p className="mt-3 whitespace-pre-wrap text-sm text-zinc-300">{incident.description}</p>
      <details className="mt-3">
        <summary className="cursor-pointer text-sm text-zinc-300 hover:text-zinc-50">
          Evidence
        </summary>
        <div className="mt-2">
          <EvidenceView evidence={incident.evidence} />
        </div>
      </details>
    </article>
  );
}
