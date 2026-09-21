import { formatUtc } from "@/lib/format";
import type { IncidentRow } from "@/lib/database.types";

export function IncidentCard({ incident }: { incident: IncidentRow }) {
  const evidenceText = JSON.stringify(incident.evidence, null, 2);

  return (
    <article className="rounded-lg border border-zinc-200 bg-white p-4">
      <h3 className="text-base font-semibold text-zinc-900">{incident.title}</h3>
      <p className="mt-1 text-sm text-zinc-600">
        {incident.rule_id} · {incident.severity} · {incident.status} ·{" "}
        {formatUtc(incident.created_at)}
      </p>
      {incident.engine_incident_id ? (
        <p className="mt-1 font-mono text-xs text-zinc-500">
          engine id {incident.engine_incident_id}
        </p>
      ) : null}
      <p className="mt-3 whitespace-pre-wrap text-sm text-zinc-800">
        {incident.description}
      </p>
      <details className="mt-3">
        <summary className="cursor-pointer text-sm text-zinc-700">Evidence (JSON)</summary>
        <pre className="mt-2 overflow-x-auto rounded-md bg-zinc-50 p-3 text-xs text-zinc-800">
          {evidenceText}
        </pre>
      </details>
    </article>
  );
}
