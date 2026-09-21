import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ThreatLens",
  description:
    "Portfolio log-analysis project. Detection (brute-force, credential spray) is in the API, not this UI.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
