"use client";

export default function ErrorPage({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
      <h1 className="text-2xl font-semibold text-zinc-50">Something went wrong</h1>
      <p className="mt-3 text-sm text-zinc-400">
        {error.message || "An unexpected error occurred in the web app."}
      </p>
      <button
        type="button"
        onClick={reset}
        className="mt-6 rounded-md bg-sky-500 px-3 py-2 text-sm font-medium text-zinc-950 hover:bg-sky-400"
      >
        Try again
      </button>
    </main>
  );
}
