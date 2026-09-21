import {
  API_URL_MISSING_MESSAGE,
  getApiBaseUrl,
  isApiConfigured,
} from "@/lib/env";

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

export type RuleInfo = {
  rule_id: string;
  title: string;
  description: string;
  severity: string;
  thresholds: Record<string, unknown>;
};

export type RulesResponse = {
  rules: RuleInfo[];
};

export type HealthResponse = {
  status: string;
};

function apiUnreachableMessage(base: string): string {
  return `Could not reach the detection API at ${base}. If this UI is hosted on Vercel, NEXT_PUBLIC_API_URL must be a public URL (not 127.0.0.1), and the API CORS_ORIGINS list must include this site. ThreatLens does not fall back to fake detections.`;
}

async function apiFetch(path: string, init?: RequestInit): Promise<Response> {
  if (!isApiConfigured()) {
    throw new Error(API_URL_MISSING_MESSAGE);
  }
  const base = getApiBaseUrl();
  try {
    return await fetch(`${base}${path}`, init);
  } catch {
    throw new Error(apiUnreachableMessage(base));
  }
}

async function readJson(response: Response): Promise<unknown> {
  return response.json().catch(() => null);
}

export async function detectLogs(text: string): Promise<DetectResult> {
  const response = await apiFetch("/detect", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });

  const payload = (await readJson(response)) as
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

  if (!payload || typeof payload !== "object" || !("incidents" in payload)) {
    throw new Error("Detection API returned an unexpected body.");
  }

  return payload;
}

export async function fetchRules(): Promise<RuleInfo[]> {
  const response = await apiFetch("/rules", { method: "GET" });
  const payload = (await readJson(response)) as RulesResponse | { detail?: unknown } | null;

  if (!response.ok) {
    const detail =
      payload && typeof payload === "object" && "detail" in payload
        ? JSON.stringify(payload.detail)
        : `${response.status} ${response.statusText}`;
    throw new Error(`Rules API error: ${detail}`);
  }

  if (!payload || typeof payload !== "object" || !("rules" in payload) || !Array.isArray(payload.rules)) {
    throw new Error("Rules API returned an unexpected body.");
  }

  return payload.rules;
}

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await apiFetch("/health", { method: "GET" });
  const payload = (await readJson(response)) as HealthResponse | null;

  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status} ${response.statusText}`);
  }

  if (!payload || payload.status !== "ok") {
    throw new Error("Health endpoint did not return {\"status\":\"ok\"}.");
  }

  return payload;
}
