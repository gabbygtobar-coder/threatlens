import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export function Badge({
  className,
  ...props
}: HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md border px-2 py-0.5 font-mono text-[11px] font-medium uppercase tracking-wide",
        className,
      )}
      {...props}
    />
  );
}

export function SeverityBadge({ severity }: { severity: string }) {
  const key = severity.toLowerCase();
  const styles =
    key === "critical"
      ? "border-red-800 bg-red-950/70 text-red-200"
      : key === "high"
        ? "border-orange-800 bg-orange-950/60 text-orange-200"
        : key === "medium"
          ? "border-amber-800 bg-amber-950/50 text-amber-200"
          : key === "low"
            ? "border-sky-800 bg-sky-950/60 text-sky-200"
            : "border-zinc-700 bg-zinc-900 text-zinc-300";

  return <Badge className={styles}>{severity}</Badge>;
}
