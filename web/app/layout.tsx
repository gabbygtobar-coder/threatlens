import type { Metadata } from "next";
import { Geist } from "next/font/google";

import { SiteHeader } from "@/components/SiteHeader";
import { getCurrentUser } from "@/lib/auth";
import { isSupabaseConfigured } from "@/lib/env";

import "./globals.css";

const geist = Geist({
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "ThreatLens",
  description:
    "Portfolio log-analysis project. Detection runs in FastAPI; saved analyses live in Supabase under RLS.",
};

export const dynamic = "force-dynamic";

export default async function RootLayout({ children }: LayoutProps<"/">) {
  const configured = isSupabaseConfigured();
  let email: string | null = null;
  if (configured) {
    const user = await getCurrentUser();
    email = user?.email ?? null;
  }

  return (
    <html lang="en">
      <body className={`${geist.className} min-h-screen bg-zinc-50 text-zinc-900 antialiased`}>
        <SiteHeader email={email} configured={configured} />
        {children}
      </body>
    </html>
  );
}
