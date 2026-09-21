"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { createClient } from "@/lib/supabase/client";

export function DeleteAnalysisButton({ analysisId }: { analysisId: string }) {
  const router = useRouter();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onDelete() {
    if (!window.confirm("Delete this saved analysis and its incidents?")) {
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
      router.push("/");
      router.refresh();
    } finally {
      setPending(false);
    }
  }

  return (
    <div>
      <button
        type="button"
        onClick={() => void onDelete()}
        disabled={pending}
        className="text-sm text-red-700 underline hover:text-red-800 disabled:opacity-50"
      >
        {pending ? "Deleting…" : "Delete analysis"}
      </button>
      {error ? <p className="mt-1 text-sm text-red-700">{error}</p> : null}
    </div>
  );
}
