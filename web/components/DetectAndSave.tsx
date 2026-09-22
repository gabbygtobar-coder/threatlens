"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type ChangeEvent, type FormEvent } from "react";

import { detectLogs, type DetectResult } from "@/lib/api";
import type { Json } from "@/lib/database.types";
import { getApiBaseUrl, isApiConfigured, isSupabaseConfigured } from "@/lib/env";
import {
  eventCountLabel,
  incidentCountLabel,
  parseErrorCountLabel,
} from "@/lib/format";
import { fromDetectIncident } from "@/lib/incidents";
import { SAMPLE_FIXTURES } from "@/lib/samples";
import { createClient } from "@/lib/supabase/client";

import { ExplainFromEvidence } from "@/components/ExplainFromEvidence";
import { IncidentCard } from "@/components/IncidentCard";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Label, Textarea } from "@/components/ui/field";

const MAX_BYTES = 1_048_576;

export function DetectAndSave({ userId }: { userId: string | null }) {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [text, setText] = useState("");
  const [result, setResult] = useState<DetectResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [detecting, setDetecting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [loadingSample, setLoadingSample] = useState<string | null>(null);

  const apiReady = isApiConfigured();

  async function onFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    if (file.size > MAX_BYTES) {
      setError("File is larger than the 1 MiB API limit.");
      return;
    }
    const contents = await file.text();
    setText(contents);
    setResult(null);
    if (!title) {
      setTitle(file.name);
    }
  }

  async function loadSample(path: string, id: string, label: string) {
    setError(null);
    setLoadingSample(id);
    try {
      const response = await fetch(path);
      if (!response.ok) {
        throw new Error(`Could not load ${path} (${response.status}).`);
      }
      const contents = await response.text();
      setText(contents);
      setTitle(label);
      setResult(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load fixture.");
    } finally {
      setLoadingSample(null);
    }
  }

  async function onDetect(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setResult(null);
    if (!text.trim()) {
      setError("Paste log text, choose a file, or load a repo fixture.");
      return;
    }
    if (new TextEncoder().encode(text).length > MAX_BYTES) {
      setError("Log text is larger than the 1 MiB API limit.");
      return;
    }
    if (!apiReady) {
      setError(
        `NEXT_PUBLIC_API_URL is not set. There is no in-browser detector. Locally, use http://127.0.0.1:8000 in web/.env.local.`,
      );
      return;
    }
    setDetecting(true);
    try {
      const detected = await detectLogs(text);
      setResult(detected);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Detect failed.";
      setError(
        `${message} Target: ${getApiBaseUrl() || "(unset)"}. CORS must allow this origin.`,
      );
    } finally {
      setDetecting(false);
    }
  }

  async function onSave() {
    if (!result || !userId) {
      return;
    }
    setError(null);
    setSaving(true);
    try {
      const supabase = createClient();
      const label = title.trim() || defaultTitle();
      const { data: analysis, error: insertError } = await supabase
        .from("analyses")
        .insert({
          user_id: userId,
          title: label,
          raw_log_text: text,
          events_count: result.events_count,
          parse_errors_count: result.parse_errors.length,
        })
        .select("id")
        .single();
      if (insertError || !analysis) {
        throw new Error(insertError?.message ?? "Could not save analysis.");
      }

      if (result.incidents.length > 0) {
        const { error: incidentError } = await supabase.from("incidents").insert(
          result.incidents.map((incident) => ({
            analysis_id: analysis.id,
            user_id: userId,
            engine_incident_id: incident.id,
            rule_id: incident.rule_id,
            severity: incident.severity,
            status: incident.status,
            title: incident.title,
            description: incident.description,
            evidence: incident.evidence as Json,
            created_at: incident.created_at,
          })),
        );
        if (incidentError) {
          await supabase.from("analyses").delete().eq("id", analysis.id);
          throw new Error(incidentError.message);
        }
      }

      router.push(`/analyses/${analysis.id}`);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Run detection</CardTitle>
        <CardDescription>
          Calls FastAPI <code className="font-mono">POST /detect</code> with the text below. The
          Python engine does not write to the database. Save is a separate, signed-in step.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="mb-4">
          <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
            Load a repo fixture
          </p>
          <p className="mt-1 text-xs text-zinc-500">
            These are the same files as <code className="font-mono">fixtures/</code>.{" "}
            <code className="font-mono">normal</code> should return zero incidents.
          </p>
          <div className="mt-2 flex flex-wrap gap-2">
            {SAMPLE_FIXTURES.map((sample) => (
              <Button
                key={sample.id}
                variant="secondary"
                size="sm"
                disabled={loadingSample !== null}
                onClick={() => void loadSample(sample.path, sample.id, sample.label)}
                title={sample.expect}
              >
                {loadingSample === sample.id ? "Loading…" : sample.label}
              </Button>
            ))}
          </div>
        </div>

        <form onSubmit={(event) => void onDetect(event)} className="space-y-3">
          <div>
            <Label htmlFor="analysis-title">Title (optional)</Label>
            <Input
              id="analysis-title"
              type="text"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="e.g. bruteforce fixture"
              className="mt-1"
            />
          </div>
          <div>
            <Label htmlFor="log-file">Log file</Label>
            <Input
              id="log-file"
              type="file"
              accept=".log,.txt,.json,text/plain"
              onChange={(event) => void onFile(event)}
              className="mt-1 cursor-pointer file:mr-3 file:rounded file:border-0 file:bg-zinc-800 file:px-2 file:py-1 file:text-xs file:text-zinc-100"
            />
          </div>
          <div>
            <Label htmlFor="log-text">Log text</Label>
            <Textarea
              id="log-text"
              value={text}
              onChange={(event) => setText(event.target.value)}
              rows={12}
              placeholder="2024-01-15T03:12:01Z login_failure user=alice ip=203.0.113.10"
              className="mt-1"
            />
          </div>
          <Button type="submit" disabled={detecting} aria-busy={detecting}>
            {detecting ? "Detecting…" : "Run /detect"}
          </Button>
        </form>

        {error ? (
          <Alert variant="error" className="mt-4">
            {error}
          </Alert>
        ) : null}

        {result ? (
          <div className="mt-6 border-t border-zinc-800 pt-4">
            <p className="text-sm text-zinc-300">
              {eventCountLabel(result.events_count)} · {incidentCountLabel(result.incidents.length)}{" "}
              · {parseErrorCountLabel(result.parse_errors.length)}
            </p>
            {result.incidents.length === 0 ? (
              <p className="mt-2 text-sm text-zinc-400">
                No incidents from this run. That is a real engine result, not an empty mock. You can
                still save the analysis.
              </p>
            ) : (
              <ul className="mt-3 space-y-3">
                {result.incidents.map((incident) => (
                  <li key={incident.id}>
                    <IncidentCard incident={fromDetectIncident(incident)} />
                  </li>
                ))}
              </ul>
            )}
            {result.parse_errors.length > 0 ? (
              <details className="mt-4">
                <summary className="cursor-pointer text-sm text-zinc-300">
                  Parse errors ({result.parse_errors.length})
                </summary>
                <ul className="mt-2 space-y-2 text-xs text-zinc-400">
                  {result.parse_errors.map((item) => (
                    <li
                      key={`${item.line_number}-${item.reason}`}
                      className="rounded-md border border-zinc-800 bg-zinc-950 p-2"
                    >
                      <p>
                        line {item.line_number}: {item.reason}
                      </p>
                      <pre className="mt-1 overflow-x-auto font-mono text-[11px] text-zinc-300">
                        {item.line}
                      </pre>
                    </li>
                  ))}
                </ul>
              </details>
            ) : null}

            {result.incidents.length > 0 ? (
              <div className="mt-4">
                <ExplainFromEvidence
                  incidents={result.incidents.map(fromDetectIncident)}
                  context="Live POST /detect response from the deterministic engine."
                />
              </div>
            ) : null}

            {userId ? (
              <Button
                type="button"
                variant="secondary"
                className="mt-4"
                onClick={() => void onSave()}
                disabled={saving}
                aria-busy={saving}
              >
                {saving ? "Saving…" : "Save analysis"}
              </Button>
            ) : (
              <Alert variant="info" className="mt-4">
                {isSupabaseConfigured() ? (
                  <>
                    Sign in to save this run to your account.{" "}
                    <Link href="/login?next=/analyze" className="text-sky-300 hover:text-sky-200">
                      Log in
                    </Link>
                    {" · "}
                    <Link href="/signup" className="text-sky-300 hover:text-sky-200">
                      Sign up
                    </Link>
                  </>
                ) : (
                  <>
                    Saving needs Supabase env (
                    <code className="font-mono">NEXT_PUBLIC_SUPABASE_URL</code> and anon key). Detection
                    above does not.
                  </>
                )}
              </Alert>
            )}
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}

function defaultTitle(): string {
  const now = new Date().toISOString().replace("T", " ").replace(/\.\d+Z$/, " UTC");
  return `Analysis ${now}`;
}
