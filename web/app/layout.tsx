import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";

import { SiteHeader } from "@/components/SiteHeader";
import { getCurrentUser } from "@/lib/auth";
import { isSupabaseConfigured } from "@/lib/env";

import "./globals.css";

const geistSans = Geist({
  subsets: ["latin"],
  variable: "--font-geist-sans",
});

const geistMono = Geist_Mono({
  subsets: ["latin"],
  variable: "--font-geist-mono",
});

export const metadata: Metadata = {
  title: {
    default: "ThreatLens",
    template: "%s · ThreatLens",
  },
  description:
    "Detection-first log analysis. FastAPI rules over TLAL; saved investigations in Supabase under RLS. No AI detector and no mock SOC data.",
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
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} dark`}>
      <body className={`${geistSans.className} min-h-screen bg-zinc-950 text-zinc-100 antialiased`}>
        <SiteHeader email={email} configured={configured} />
        {children}
      </body>
    </html>
  );
}
