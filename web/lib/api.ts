import { getApiBaseUrl } from "@/lib/env";

export type DetectIncident = {
  id: string;
  rule_id: string;
  severity: string;
  status: string;
  title: string;
  description: string;
  evidence: Record<string, unknown>;
  created_at: string;
};

export type ParseError = {
  line_number: number;
  line: string;
  reason: string;
};

export type DetectResult = {
  events_count: number;
  incidents: DetectIncident[];
  parse_errors: ParseError[];
};

export async function detectLogs(text: string): Promise<DetectResult> {
  const base = getApiBaseUrl().replace(/\/$/, "");
  const response = await fetch(`${base}/detect`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });

  const payload = (await response.json().catch(() => null)) as
    | DetectResult
    | { detail?: unknown }
    | null;

  if (!response.ok) {
    const detail =
      payload && typeof payload === "object" && "detail" in payload
        ? JSON.stringify(payload.detail)
        : `${response.status} ${response.statusText}`;
    throw new Error(`Detection API error: ${detail}`);
  }

  if (!payload || !("incidents" in payload)) {
    throw new Error("Detection API returned an unexpected body.");
  }

  return payload;
}
