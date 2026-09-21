export function formatUtc(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    return iso;
  }
  return date.toISOString().replace("T", " ").replace(/\.\d+Z$/, " UTC");
}

export function incidentCountLabel(count: number): string {
  return count === 1 ? "1 incident" : `${count} incidents`;
}

export function eventCountLabel(count: number): string {
  return count === 1 ? "1 event" : `${count} events`;
}

export function parseErrorCountLabel(count: number): string {
  return count === 1 ? "1 parse error" : `${count} parse errors`;
}

export function formatThresholdValue(value: unknown): string {
  if (value === null || value === undefined) {
    return "—";
  }
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  return JSON.stringify(value);
}
