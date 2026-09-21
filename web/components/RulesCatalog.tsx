"use client";

import { useEffect, useState } from "react";

import { fetchRules, type RuleInfo } from "@/lib/api";
import { API_URL_MISSING_MESSAGE, isApiConfigured } from "@/lib/env";
import { formatThresholdValue } from "@/lib/format";

import { Alert } from "@/components/ui/alert";
import { SeverityBadge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export function RulesCatalog() {
  const configured = isApiConfigured();
  const [rules, setRules] = useState<RuleInfo[] | null>(null);
  const [error, setError] = useState<string | null>(
    configured ? null : API_URL_MISSING_MESSAGE,
  );
  const [loading, setLoading] = useState(configured);

  useEffect(() => {
    if (!configured) {
      return;
    }
    let cancelled = false;
    void fetchRules()
      .then((data) => {
        if (!cancelled) {
          setRules(data);
          setError(null);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Could not load rules.");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [configured]);

  if (loading) {
    return <Alert variant="info">Loading live rule catalog from GET /rules…</Alert>;
  }

  if (error) {
    return <Alert variant="error">{error}</Alert>;
  }

  if (!rules || rules.length === 0) {
    return (
      <Alert variant="warning">
        The API returned an empty rule list. That would mean no detectors are registered — unusual
        for this repo, and not a mocked catalog.
      </Alert>
    );
  }

  return (
    <div className="space-y-4">
      {rules.map((rule) => (
        <Card key={rule.rule_id}>
          <CardHeader>
            <div className="flex flex-wrap items-center gap-2">
              <CardTitle className="font-mono text-sm">{rule.rule_id}</CardTitle>
              <SeverityBadge severity={rule.severity} />
            </div>
            <CardDescription>{rule.title}</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-zinc-300">{rule.description}</p>
            <h3 className="mt-4 text-xs font-medium uppercase tracking-wide text-zinc-500">
              Thresholds (from the engine, not edited here)
            </h3>
            <dl className="mt-2 grid gap-2 text-sm sm:grid-cols-[minmax(8rem,14rem)_1fr]">
              {Object.entries(rule.thresholds).map(([key, value]) => (
                <div key={key} className="contents">
                  <dt className="font-mono text-xs text-zinc-400">{key}</dt>
                  <dd className="break-all font-mono text-xs text-zinc-200">
                    {formatThresholdValue(value)}
                  </dd>
                </div>
              ))}
            </dl>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
