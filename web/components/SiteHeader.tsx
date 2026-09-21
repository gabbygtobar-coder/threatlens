import Link from "next/link";

import { LogoutButton } from "@/components/LogoutButton";

export function SiteHeader({
  email,
  configured,
}: {
  email: string | null;
  configured: boolean;
}) {
  return (
    <header className="border-b border-zinc-200 bg-white">
      <div className="mx-auto flex max-w-3xl items-center justify-between gap-4 px-6 py-4">
        <Link href="/" className="text-sm font-semibold tracking-tight text-zinc-900">
          ThreatLens
        </Link>
        <nav className="flex items-center gap-3 text-sm">
          {email ? (
            <>
              <span className="hidden text-zinc-600 sm:inline">{email}</span>
              <LogoutButton />
            </>
          ) : (
            <>
              <Link href="/login" className="text-zinc-700 hover:text-zinc-900">
                Log in
              </Link>
              <Link
                href="/signup"
                className="rounded-md bg-zinc-900 px-3 py-1.5 text-white hover:bg-zinc-800"
              >
                Sign up
              </Link>
            </>
          )}
          {!configured ? (
            <span className="text-xs text-zinc-500">env not set</span>
          ) : null}
        </nav>
      </div>
    </header>
  );
}
