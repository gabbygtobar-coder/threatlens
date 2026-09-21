"use client";

import { useMemo, useState } from "react";

import { formatUtc } from "@/lib/format";
import { uniqueSorted, type IncidentView } from "@/lib/incidents";

import { EvidenceView } from "@/components/EvidenceView";
import { SeverityBadge } from "@/components/ui/badge";
import { Input, Label, Select } from "@/components/ui/field";

export function InvestigationIncidents({
  incidents,
  emptyMessage,
}: {
  incidents: IncidentView[];
  emptyMessage: string;
}) {
  const [severity, setSeverity] = useState("all");
  const [ruleId, setRuleId] = useState("all");
  const [status, setStatus] = useState("all");
  const [query, setQuery] = useState("");
  const [expanded, setExpanded] = useState<string | null>(null);

  const ruleOptions = useMemo(
    () => uniqueSorted(incidents.map((item) => item.rule_id)),
    [incidents],
  );
  const statusOptions = useMemo(
    () => uniqueSorted(incidents.map((item) => item.status)),
    [incidents],
  );
  const severityOptions = useMemo(
    () => uniqueSorted(incidents.map((item) => item.severity)),
    [incidents],
  );

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return incidents.filter((item) => {
      if (severity !== "all" && item.severity !== severity) {
        return false;
      }
      if (ruleId !== "all" && item.rule_id !== ruleId) {
        return false;
      }
      if (status !== "all" && item.status !== status) {
        return false;
      }
      if (!needle) {
        return true;
      }
      const haystack = [
        item.title,
        item.description,
        item.rule_id,
        item.severity,
        item.status,
        item.engine_incident_id ?? "",
        JSON.stringify(item.evidence),
      ]
        .join(" ")
        .toLowerCase();
      return haystack.includes(needle);
    });
  }, [incidents, query, ruleId, severity, status]);

  if (incidents.length === 0) {
    return <p className="text-sm text-zinc-400">{emptyMessage}</p>;
  }

  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <Label htmlFor="filter-severity">Severity</Label>
          <Select
            id="filter-severity"
            className="mt-1"
            value={severity}
            onChange={(event) => setSeverity(event.target.value)}
          >
            <option value="all">All</option>
            {severityOptions.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </Select>
        </div>
        <div>
          <Label htmlFor="filter-rule">Rule</Label>
          <Select
            id="filter-rule"
            className="mt-1"
            value={ruleId}
            onChange={(event) => setRuleId(event.target.value)}
          >
            <option value="all">All</option>
            {ruleOptions.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </Select>
        </div>
        <div>
          <Label htmlFor="filter-status">Status</Label>
          <Select
            id="filter-status"
            className="mt-1"
            value={status}
            onChange={(event) => setStatus(event.target.value)}
          >
            <option value="all">All</option>
            {statusOptions.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </Select>
        </div>
        <div>
          <Label htmlFor="filter-search">Search</Label>
          <Input
            id="filter-search"
            className="mt-1"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Title, evidence, rule id…"
          />
        </div>
      </div>
      <p className="text-xs text-zinc-500">
        Showing {filtered.length} of {incidents.length} saved incident
        {incidents.length === 1 ? "" : "s"}. Filters only hide rows; they do not invent findings.
        Engine status is currently always <code className="font-mono">open</code>.
      </p>

      {filtered.length === 0 ? (
        <p className="text-sm text-zinc-400">No incidents match these filters.</p>
      ) : (
        <>
          <div className="hidden overflow-x-auto rounded-xl border border-zinc-800 md:block">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-zinc-900 text-xs uppercase tracking-wide text-zinc-400">
                <tr>
                  <th className="px-3 py-2 font-medium">Severity</th>
                  <th className="px-3 py-2 font-medium">Rule</th>
                  <th className="px-3 py-2 font-medium">Title</th>
                  <th className="px-3 py-2 font-medium">Status</th>
                  <th className="px-3 py-2 font-medium">Window end</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((incident) => {
                  const open = expanded === incident.key;
                  return (
                    <IncidentRows
                      key={incident.key}
                      incident={incident}
                      open={open}
                      onToggle={() =>
                        setExpanded((current) =>
                          current === incident.key ? null : incident.key,
                        )
                      }
                    />
                  );
                })}
              </tbody>
            </table>
          </div>
          <ul className="space-y-3 md:hidden">
            {filtered.map((incident) => (
              <li key={`card-${incident.key}`}>
                <IncidentMobileCard incident={incident} />
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}

function IncidentRows({
  incident,
  open,
  onToggle,
}: {
  incident: IncidentView;
  open: boolean;
  onToggle: () => void;
}) {
  return (
    <>
      <tr className="border-t border-zinc-800">
        <td className="px-3 py-2">
          <SeverityBadge severity={incident.severity} />
        </td>
        <td className="px-3 py-2 font-mono text-xs text-zinc-300">{incident.rule_id}</td>
        <td className="px-3 py-2">
          <button
            type="button"
            onClick={onToggle}
            className="text-left text-zinc-100 hover:text-sky-300"
          >
            {incident.title}
          </button>
        </td>
        <td className="px-3 py-2 font-mono text-xs text-zinc-400">{incident.status}</td>
        <td className="px-3 py-2 whitespace-nowrap text-xs text-zinc-400">
          {formatUtc(incident.created_at)}
        </td>
      </tr>
      {open ? (
        <tr className="border-t border-zinc-800 bg-zinc-950/60">
          <td colSpan={5} className="px-3 py-3">
            <p className="whitespace-pre-wrap text-sm text-zinc-300">{incident.description}</p>
            {incident.engine_incident_id ? (
              <p className="mt-2 font-mono text-[11px] text-zinc-500">
                engine id {incident.engine_incident_id}
              </p>
            ) : null}
            <div className="mt-3">
              <p className="mb-2 text-xs font-medium uppercase tracking-wide text-zinc-500">
                Evidence
              </p>
              <EvidenceView evidence={incident.evidence} />
            </div>
          </td>
        </tr>
      ) : null}
    </>
  );
}

function IncidentMobileCard({ incident }: { incident: IncidentView }) {
  return (
    <article className="rounded-xl border border-zinc-800 bg-zinc-900/80 p-4">
      <div className="flex flex-wrap items-center gap-2">
        <SeverityBadge severity={incident.severity} />
        <span className="font-mono text-xs text-zinc-400">{incident.rule_id}</span>
      </div>
      <h3 className="mt-2 font-medium text-zinc-50">{incident.title}</h3>
      <p className="mt-1 text-xs text-zinc-500">
        {incident.status} · {formatUtc(incident.created_at)}
      </p>
      <p className="mt-2 whitespace-pre-wrap text-sm text-zinc-300">{incident.description}</p>
      <details className="mt-3">
        <summary className="cursor-pointer text-sm text-zinc-300">Evidence</summary>
        <div className="mt-2">
          <EvidenceView evidence={incident.evidence} />
        </div>
      </details>
    </article>
  );
}
