import type { Metadata } from "next";

import { ApiStatus } from "@/components/ApiStatus";
import { RulesCatalog } from "@/components/RulesCatalog";

export const metadata: Metadata = {
  title: "Rules",
};

export default function RulesPage() {
  return (
    <main className="mx-auto max-w-5xl space-y-6 px-4 py-10 sm:px-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight text-zinc-50">Detection rules</h1>
        <p className="mt-2 max-w-2xl text-sm text-zinc-400">
          Live catalog from FastAPI <code className="font-mono">GET /rules</code>. Thresholds are
          displayed only — this page does not change them.{" "}
          <code className="font-mono">impossible_travel</code> is simulated geo, not MaxMind.
        </p>
      </div>
      <ApiStatus />
      <RulesCatalog />
    </main>
  );
}
