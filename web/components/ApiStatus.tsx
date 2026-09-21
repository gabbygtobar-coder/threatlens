"use client";

import { useEffect, useState } from "react";

import { fetchHealth } from "@/lib/api";
import { getApiBaseUrl, isApiConfigured } from "@/lib/env";

import { Alert } from "@/components/ui/alert";

type Status = "missing" | "checking" | "ok" | "down";

export function ApiStatus({ compact = false }: { compact?: boolean }) {
  const configured = isApiConfigured();
  const base = getApiBaseUrl();
  const [status, setStatus] = useState<Status>(configured ? "checking" : "missing");
  const [detail, setDetail] = useState<string | null>(null);

  useEffect(() => {
    if (!configured) {
      return;
    }
    let cancelled = false;
    void fetchHealth()
      .then(() => {
        if (!cancelled) {
          setStatus("ok");
          setDetail(null);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setStatus("down");
          setDetail(err instanceof Error ? err.message : "Health check failed.");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [configured]);

  if (status === "missing") {
    return (
      <Alert variant="warning">
        Detection API URL is not configured (<code className="font-mono">NEXT_PUBLIC_API_URL</code>
        ). Analyze and Rules will not call a mock engine.
      </Alert>
    );
  }

  if (status === "checking") {
    return compact ? (
      <p className="text-xs text-zinc-500">Checking API at {base}…</p>
    ) : (
      <Alert variant="info">Checking detection API at {base}…</Alert>
    );
  }

  if (status === "ok") {
    return compact ? (
      <p className="text-xs text-zinc-500">
        Engine reachable at <span className="font-mono text-zinc-300">{base}</span>
      </p>
    ) : (
      <Alert variant="info">
        Engine reachable at <span className="font-mono">{base}</span>{" "}
        <code className="font-mono">GET /health</code> returned ok. This is a live check, not a
        dashboard widget.
      </Alert>
    );
  }

  return (
    <Alert variant="error">
      {detail ?? `Could not reach ${base}.`} The FastAPI process is not claimed as a production
      deployment from this UI.
    </Alert>
  );
}
