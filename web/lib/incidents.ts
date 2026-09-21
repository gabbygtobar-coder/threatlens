import type { DetectIncident } from "@/lib/api";
import type { IncidentRow, Json } from "@/lib/database.types";

export type AnalysisListItem = {
  id: string;
  title: string | null;
  created_at: string;
  events_count: number;
  parse_errors_count: number;
  incident_count: number;
  severity_counts: SeverityCounts;
};

export type IncidentView = {
  key: string;
  rule_id: string;
  severity: string;
  status: string;
  title: string;
  description: string;
  evidence: Json;
  created_at: string;
  engine_incident_id: string | null;
};

export type SeverityCounts = {
  critical: number;
  high: number;
  medium: number;
  low: number;
  other: number;
};

const KNOWN_SEVERITIES = ["critical", "high", "medium", "low"] as const;

export function emptySeverityCounts(): SeverityCounts {
  return { critical: 0, high: 0, medium: 0, low: 0, other: 0 };
}

export function countSeverities(severities: string[]): SeverityCounts {
  const counts = emptySeverityCounts();
  for (const raw of severities) {
    const key = raw.toLowerCase();
    if (key === "critical" || key === "high" || key === "medium" || key === "low") {
      counts[key] += 1;
    } else {
      counts.other += 1;
    }
  }
  return counts;
}

export function nonZeroSeverityEntries(counts: SeverityCounts): { label: string; count: number }[] {
  const rows: { label: string; count: number }[] = [];
  for (const label of KNOWN_SEVERITIES) {
    if (counts[label] > 0) {
      rows.push({ label, count: counts[label] });
    }
  }
  if (counts.other > 0) {
    rows.push({ label: "other", count: counts.other });
  }
  return rows;
}

export function fromDetectIncident(incident: DetectIncident): IncidentView {
  return {
    key: incident.id,
    rule_id: incident.rule_id,
    severity: incident.severity,
    status: incident.status,
    title: incident.title,
    description: incident.description,
    evidence: incident.evidence as Json,
    created_at: incident.created_at,
    engine_incident_id: incident.id,
  };
}

export function fromIncidentRow(row: IncidentRow): IncidentView {
  return {
    key: row.id,
    rule_id: row.rule_id,
    severity: row.severity,
    status: row.status,
    title: row.title,
    description: row.description,
    evidence: row.evidence,
    created_at: row.created_at,
    engine_incident_id: row.engine_incident_id,
  };
}

export function uniqueSorted(values: string[]): string[] {
  return [...new Set(values)].sort((a, b) => a.localeCompare(b));
}
