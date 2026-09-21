import Link from "next/link";

export default function NotFound() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-12">
      <h1 className="text-2xl font-semibold">Not found</h1>
      <p className="mt-3 text-sm text-zinc-600">
        That analysis does not exist or you do not have access to it (RLS).
      </p>
      <p className="mt-4 text-sm">
        <Link href="/" className="underline">
          Back home
        </Link>
      </p>
    </main>
  );
}
