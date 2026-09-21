import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export function Alert({
  className,
  variant = "error",
  ...props
}: HTMLAttributes<HTMLDivElement> & { variant?: "error" | "info" | "warning" }) {
  const styles =
    variant === "error"
      ? "border-red-900/80 bg-red-950/40 text-red-200"
      : variant === "warning"
        ? "border-amber-900/80 bg-amber-950/30 text-amber-100"
        : "border-zinc-700 bg-zinc-900 text-zinc-200";

  return (
    <div
      role="status"
      className={cn("rounded-lg border px-3 py-2 text-sm", styles, className)}
      {...props}
    />
  );
}
