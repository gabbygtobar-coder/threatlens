import type { Metadata } from "next";

import { ApiStatus } from "@/components/ApiStatus";
import { DetectAndSave } from "@/components/DetectAndSave";
import { getCurrentUser } from "@/lib/auth";
import { isSupabaseConfigured } from "@/lib/env";

export const metadata: Metadata = {
  title: "Analyze",
};

export const dynamic = "force-dynamic";

export default async function AnalyzePage() {
  const user = isSupabaseConfigured() ? await getCurrentUser() : null;

  return (
    <main className="mx-auto max-w-5xl space-y-6 px-4 py-10 sm:px-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight text-zinc-50">Analyze</h1>
        <p className="mt-2 max-w-2xl text-sm text-zinc-400">
          Paste or upload ThreatLens Auth Log (TLAL) text. This page calls the FastAPI detection
          engine and shows whatever it returns — including zero incidents. Explain from evidence
          only summarizes those incidents. Saving requires a signed-in Supabase user.
        </p>
      </div>
      <ApiStatus />
      <DetectAndSave userId={user?.id ?? null} />
    </main>
  );
}
