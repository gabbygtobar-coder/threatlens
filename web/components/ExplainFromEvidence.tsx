"use client";

import { useState } from "react";

import {
  ExplainNotConfiguredError,
  explainIncidents,
  type ExplainIncidentInput,
} from "@/lib/api";
import type { Json } from "@/lib/database.types";
import type { IncidentView } from "@/lib/incidents";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

export function ExplainFromEvidence({
  incidents,
  context,
}: {
  incidents: IncidentView[];
  context?: string;
}) {
  const [loading, setLoading] = useState(false);
  const [unavailable, setUnavailable] = useState(false);
  const [explanation, setExplanation] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (incidents.length === 0) {
    return null;
  }

  async function onExplain() {
    setError(null);
    const payload = incidents.map(toExplainInput);
    if (payload.some((item) => item === null)) {
      setError(
        "Evidence is not a structured object, so Explain from evidence refused to call the API.",
      );
      return;
    }
    setLoading(true);
    try {
      const text = await explainIncidents(payload as ExplainIncidentInput[], context);
      setExplanation(text);
    } catch (err) {
      setExplanation(null);
      if (err instanceof ExplainNotConfiguredError) {
        setUnavailable(true);
        return;
      }
      setError(err instanceof Error ? err.message : "Explain from evidence failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="space-y-3 rounded-xl border border-zinc-800 bg-zinc-950/40 p-4">
      <div>
        <h2 className="text-sm font-semibold text-zinc-50">Explain from evidence</h2>
        <p className="mt-1 text-xs text-zinc-500">
          Summarizes incidents the deterministic engine already returned. This is not a detector
          and it does not score or invent threats.
        </p>
      </div>

      {unavailable ? (
        <Alert variant="info">
          Explain from evidence is not configured on this API (HTTP 503). Set OPENAI_API_KEY on
          the API service only — never in the Next.js app. No explanation was generated. Detection
          results are unchanged. Reload this page after the key is set.
        </Alert>
      ) : (
        <Button
          type="button"
          variant="secondary"
          onClick={() => void onExplain()}
          disabled={loading}
          aria-busy={loading}
        >
          {loading ? "Explaining from evidence…" : "Explain from evidence"}
        </Button>
      )}

      {error ? <Alert variant="error">{error}</Alert> : null}

      {explanation ? (
        <article
          aria-label="Explanation from evidence"
          className="rounded-lg border border-zinc-800 bg-zinc-900/70 p-3"
        >
          <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
            Explanation from evidence
          </p>
          <p className="mt-2 whitespace-pre-wrap text-sm text-zinc-200">{explanation}</p>
          <p className="mt-3 text-xs text-zinc-500">
            This text only restates the incidents above. It did not detect anything.
          </p>
        </article>
      ) : null}
    </section>
  );
}

function toExplainInput(incident: IncidentView): ExplainIncidentInput | null {
  const evidence = asEvidenceRecord(incident.evidence);
  if (!evidence) {
    return null;
  }
  return {
    id: incident.engine_incident_id ?? incident.key,
    rule_id: incident.rule_id,
    severity: incident.severity,
    status: incident.status,
    title: incident.title,
    description: incident.description,
    evidence,
    created_at: incident.created_at,
  };
}

function asEvidenceRecord(value: Json): Record<string, unknown> | null {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return null;
  }
  return value;
}
