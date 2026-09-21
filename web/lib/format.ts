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
