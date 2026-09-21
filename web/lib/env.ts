/**
 * Public env for the Next.js app. These values are inlined at build time.
 * Missing values must not crash `next build` in CI — pages render an honest note.
 *
 * NEXT_PUBLIC_API_URL is required to call FastAPI. There is no in-browser
 * detector and no demo-mode fallback. Do not default to localhost in production
 * builds: a Vercel deployment with a silent 127.0.0.1 target looks "live" and is not.
 */

export function isSupabaseConfigured(): boolean {
  return Boolean(
    process.env.NEXT_PUBLIC_SUPABASE_URL?.trim() &&
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY?.trim(),
  );
}

export function getSupabaseUrl(): string {
  return process.env.NEXT_PUBLIC_SUPABASE_URL?.trim() ?? "";
}

export function getSupabaseAnonKey(): string {
  return process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY?.trim() ?? "";
}

export function getApiBaseUrl(): string {
  return (process.env.NEXT_PUBLIC_API_URL ?? "").trim().replace(/\/$/, "");
}

export function isApiConfigured(): boolean {
  return Boolean(getApiBaseUrl());
}

export const API_URL_MISSING_MESSAGE =
  "NEXT_PUBLIC_API_URL is not set. This UI does not run detection itself and does not ship mock incidents. Set the env var to a reachable FastAPI origin (local: http://127.0.0.1:8000).";
