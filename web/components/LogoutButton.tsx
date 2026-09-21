"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { createClient } from "@/lib/supabase/client";

import { Button } from "@/components/ui/button";

export function LogoutButton() {
  const router = useRouter();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onLogout() {
    setPending(true);
    setError(null);
    try {
      const supabase = createClient();
      const { error: signOutError } = await supabase.auth.signOut();
      if (signOutError) {
        setError(signOutError.message);
        return;
      }
      router.push("/");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign out failed.");
    } finally {
      setPending(false);
    }
  }

  return (
    <span className="inline-flex items-center gap-2">
      <Button variant="secondary" size="sm" onClick={() => void onLogout()} disabled={pending}>
        {pending ? "Signing out…" : "Log out"}
      </Button>
      {error ? <span className="text-xs text-red-400">{error}</span> : null}
    </span>
  );
}
