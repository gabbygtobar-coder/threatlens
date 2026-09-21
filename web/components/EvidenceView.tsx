import type { Json } from "@/lib/database.types";
import { formatThresholdValue } from "@/lib/format";

export function EvidenceView({ evidence }: { evidence: Json }) {
  if (evidence && typeof evidence === "object" && !Array.isArray(evidence)) {
    const entries = Object.entries(evidence);
    if (entries.length === 0) {
      return <p className="text-sm text-zinc-500">Evidence object is empty.</p>;
    }
    return (
      <dl className="grid gap-2 text-sm sm:grid-cols-[minmax(8rem,12rem)_1fr]">
        {entries.map(([key, value]) => (
          <div key={key} className="contents">
            <dt className="font-mono text-xs text-zinc-400">{key}</dt>
            <dd className="min-w-0">
              {typeof value === "object" ? (
                <pre className="overflow-x-auto rounded-md bg-zinc-950 p-2 font-mono text-xs text-zinc-200">
                  {JSON.stringify(value, null, 2)}
                </pre>
              ) : (
                <span className="break-all font-mono text-xs text-zinc-200">
                  {formatThresholdValue(value)}
                </span>
              )}
            </dd>
          </div>
        ))}
      </dl>
    );
  }

  return (
    <pre className="overflow-x-auto rounded-md bg-zinc-950 p-3 font-mono text-xs text-zinc-200">
      {JSON.stringify(evidence, null, 2)}
    </pre>
  );
}
