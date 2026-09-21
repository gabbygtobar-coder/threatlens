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
    <header className="sticky top-0 z-20 border-b border-zinc-800/80 bg-zinc-950/90 backdrop-blur">
      <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6">
        <Link href="/" className="text-sm font-semibold tracking-tight text-zinc-50">
          ThreatLens
        </Link>
        <nav className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-zinc-300">
          <Link href="/analyze" className="hover:text-zinc-50">
            Analyze
          </Link>
          <Link href="/analyses" className="hover:text-zinc-50">
            Investigations
          </Link>
          <Link href="/rules" className="hover:text-zinc-50">
            Rules
          </Link>
          {email ? (
            <>
              <span className="hidden max-w-48 truncate text-zinc-500 sm:inline" title={email}>
                {email}
              </span>
              <LogoutButton />
            </>
          ) : (
            <>
              <Link href="/login" className="hover:text-zinc-50">
                Log in
              </Link>
              <Link
                href="/signup"
                className="rounded-md bg-sky-500 px-3 py-1.5 text-zinc-950 hover:bg-sky-400"
              >
                Sign up
              </Link>
            </>
          )}
          {!configured ? (
            <span className="text-xs text-amber-400">auth env unset</span>
          ) : null}
        </nav>
      </div>
    </header>
  );
}
