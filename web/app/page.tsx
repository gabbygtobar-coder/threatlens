export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-zinc-50 px-6 text-zinc-900">
      <h1 className="text-3xl font-semibold tracking-tight">ThreatLens</h1>
      <p className="mt-4 max-w-xl text-center text-zinc-600">
        M2 detection lives in the API (brute-force and credential spray). This
        page does not show alerts.
      </p>
    </main>
  );
}
