import type { Metadata } from "next";

import { LandingPage } from "@/components/LandingPage";
import { getCurrentUser } from "@/lib/auth";
import { isSupabaseConfigured } from "@/lib/env";

export const metadata: Metadata = {
  title: "ThreatLens",
  description:
    "Detection-first log analysis. Six deterministic FastAPI rules, optional Supabase save. No AI, no mock incidents.",
};

export const dynamic = "force-dynamic";

export default async function Home() {
  const supabaseConfigured = isSupabaseConfigured();
  const user = supabaseConfigured ? await getCurrentUser() : null;

  return (
    <LandingPage email={user?.email ?? null} supabaseConfigured={supabaseConfigured} />
  );
}
