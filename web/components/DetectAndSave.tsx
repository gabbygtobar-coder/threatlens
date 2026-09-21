"use client";

import { useRouter } from "next/navigation";
import { useState, type ChangeEvent, type FormEvent } from "react";

import { detectLogs, type DetectResult } from "@/lib/api";
import type { Json } from "@/lib/database.types";
import { getApiBaseUrl } from "@/lib/env";
import { createClient } from "@/lib/supabase/client";

const MAX_BYTES = 1_048_576;

export function DetectAndSave({ userId }: { userId: string }) {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [text, setText] = useState("");
  const [result, setResult] = useState<DetectResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [detecting, setDetecting] = useState(false);
  const [saving, setSaving] = useState(false);

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
    if (!title) {
      setTitle(file.name);
    }
  }

  async function onDetect(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setResult(null);
    if (!text.trim()) {
      setError("Paste log text or choose a file.");
      return;
    }
    if (new TextEncoder().encode(text).length > MAX_BYTES) {
      setError("Log text is larger than the 1 MiB API limit.");
      return;
    }
    setDetecting(true);
    try {
      const detected = await detectLogs(text);
      setResult(detected);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Detect failed.";
      setError(
        `${message} Is the API running at ${getApiBaseUrl()}? CORS must allow this origin.`,
      );
    } finally {
      setDetecting(false);
    }
  }

  async function onSave() {
    if (!result) {
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
    <section className="rounded-lg border border-zinc-200 bg-white p-5">
      <h2 className="text-lg font-semibold">Run detection</h2>
      <p className="mt-1 text-sm text-zinc-600">
        Calls FastAPI <code>POST /detect</code>, then you can save the result to
        your Supabase account. The Python engine does not write to the database.
      </p>
      <form onSubmit={(event) => void onDetect(event)} className="mt-4 space-y-3">
        <label className="block text-sm">
          <span className="font-medium text-zinc-800">Title (optional)</span>
          <input
            type="text"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="e.g. bruteforce fixture"
            className="mt-1 w-full rounded-md border border-zinc-300 px-3 py-2 text-sm"
          />
        </label>
        <label className="block text-sm">
          <span className="font-medium text-zinc-800">Log file</span>
          <input
            type="file"
            accept=".log,.txt,.json,text/plain"
            onChange={(event) => void onFile(event)}
            className="mt-1 block w-full text-sm"
          />
        </label>
        <label className="block text-sm">
          <span className="font-medium text-zinc-800">Log text</span>
          <textarea
            value={text}
            onChange={(event) => setText(event.target.value)}
            rows={10}
            placeholder="2024-01-15T03:12:01Z login_failure user=alice ip=203.0.113.10"
            className="mt-1 w-full rounded-md border border-zinc-300 px-3 py-2 font-mono text-xs"
          />
        </label>
        <button
          type="submit"
          disabled={detecting}
          className="rounded-md bg-zinc-900 px-3 py-2 text-sm font-medium text-white hover:bg-zinc-800 disabled:opacity-50"
        >
          {detecting ? "Detecting…" : "Run /detect"}
        </button>
      </form>

      {error ? <p className="mt-3 text-sm text-red-700">{error}</p> : null}

      {result ? (
        <div className="mt-6 border-t border-zinc-200 pt-4">
          <p className="text-sm text-zinc-700">
            {result.events_count} event{result.events_count === 1 ? "" : "s"} ·{" "}
            {result.incidents.length} incident
            {result.incidents.length === 1 ? "" : "s"} · {result.parse_errors.length}{" "}
            parse error{result.parse_errors.length === 1 ? "" : "s"}
          </p>
          {result.incidents.length === 0 ? (
            <p className="mt-2 text-sm text-zinc-600">
              No incidents. You can still save this run.
            </p>
          ) : (
            <ul className="mt-3 space-y-2 text-sm">
              {result.incidents.map((incident) => (
                <li
                  key={incident.id}
                  className="rounded-md border border-zinc-200 bg-zinc-50 px-3 py-2"
                >
                  <span className="font-medium">{incident.title}</span>
                  <span className="mt-0.5 block text-zinc-600">
                    {incident.rule_id} · {incident.severity} · {incident.status}
                  </span>
                </li>
              ))}
            </ul>
          )}
          {result.parse_errors.length > 0 ? (
            <ul className="mt-3 space-y-1 text-xs text-zinc-600">
              {result.parse_errors.map((item) => (
                <li key={`${item.line_number}-${item.reason}`}>
                  line {item.line_number}: {item.reason}
                </li>
              ))}
            </ul>
          ) : null}
          <button
            type="button"
            onClick={() => void onSave()}
            disabled={saving}
            className="mt-4 rounded-md border border-zinc-900 bg-white px-3 py-2 text-sm font-medium text-zinc-900 hover:bg-zinc-100 disabled:opacity-50"
          >
            {saving ? "Saving…" : "Save to my account"}
          </button>
        </div>
      ) : null}
    </section>
  );
}

function defaultTitle(): string {
  const now = new Date().toISOString().replace("T", " ").replace(/\.\d+Z$/, " UTC");
  return `Analysis ${now}`;
}
