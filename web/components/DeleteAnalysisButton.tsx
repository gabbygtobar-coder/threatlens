"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { createClient } from "@/lib/supabase/client";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

export function DeleteAnalysisButton({ analysisId }: { analysisId: string }) {
  const router = useRouter();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onDelete() {
    if (!window.confirm("Delete this saved analysis and its incidents? This cannot be undone.")) {
      return;
    }
    setPending(true);
    setError(null);
    try {
      const supabase = createClient();
      const { error: deleteError } = await supabase
        .from("analyses")
        .delete()
        .eq("id", analysisId);
      if (deleteError) {
        setError(deleteError.message);
        return;
      }
      router.push("/analyses");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed.");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="text-right">
      <Button
        variant="destructive"
        size="sm"
        onClick={() => void onDelete()}
        disabled={pending}
        aria-busy={pending}
      >
        {pending ? "Deleting…" : "Delete analysis"}
      </Button>
      {error ? (
        <Alert variant="error" className="mt-2">
          {error}
        </Alert>
      ) : null}
    </div>
  );
}
