import Link from "next/link";

export default function NotFound() {
  return (
    <main className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
      <h1 className="text-2xl font-semibold text-zinc-50">Not found</h1>
      <p className="mt-3 text-sm text-zinc-400">
        That analysis does not exist or you do not have access to it (RLS). This page does not
        invent a sample investigation.
      </p>
      <p className="mt-4 text-sm">
        <Link href="/analyses" className="text-sky-400 hover:text-sky-300">
          Back to investigations
        </Link>
      </p>
    </main>
  );
}
