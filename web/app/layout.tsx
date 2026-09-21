import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ThreatLens",
  description:
    "Early skeleton for a cybersecurity log-analysis / threat-detection portfolio project. No detection yet.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
