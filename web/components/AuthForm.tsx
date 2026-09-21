"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { createClient } from "@/lib/supabase/client";

export function AuthForm({
  mode,
  nextPath = "/",
}: {
  mode: "login" | "signup";
  nextPath?: string;
}) {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const title = mode === "login" ? "Log in" : "Create an account";
  const submitLabel = mode === "login" ? "Log in" : "Sign up";
  const altHref = mode === "login" ? "/signup" : "/login";
  const altLabel =
    mode === "login" ? "Need an account? Sign up" : "Already have an account? Log in";

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setInfo(null);
    setPending(true);
    try {
      const supabase = createClient();
      if (mode === "login") {
        const { error: signError } = await supabase.auth.signInWithPassword({
          email,
          password,
        });
        if (signError) {
          setError(signError.message);
          return;
        }
        router.push(nextPath);
        router.refresh();
        return;
      }

      const { data, error: signError } = await supabase.auth.signUp({
        email,
        password,
      });
      if (signError) {
        setError(signError.message);
        return;
      }
      if (!data.session) {
        setInfo(
          "Account created. If email confirmation is enabled, check your inbox before logging in. For local use, turn off Confirm email in Supabase Auth settings.",
        );
        return;
      }
      router.push(nextPath);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setPending(false);
    }
  }

  return (
    <main className="mx-auto max-w-md px-6 py-12">
      <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
      <p className="mt-2 text-sm text-zinc-600">
        Email and password via Supabase Auth. No social login in M4.
      </p>
      <form onSubmit={(event) => void onSubmit(event)} className="mt-6 space-y-4">
        <label className="block text-sm">
          <span className="font-medium text-zinc-800">Email</span>
          <input
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            className="mt-1 w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm"
          />
        </label>
        <label className="block text-sm">
          <span className="font-medium text-zinc-800">Password</span>
          <input
            type="password"
            autoComplete={mode === "login" ? "current-password" : "new-password"}
            required
            minLength={6}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="mt-1 w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm"
          />
        </label>
        {error ? <p className="text-sm text-red-700">{error}</p> : null}
        {info ? <p className="text-sm text-zinc-700">{info}</p> : null}
        <button
          type="submit"
          disabled={pending}
          className="w-full rounded-md bg-zinc-900 px-3 py-2 text-sm font-medium text-white hover:bg-zinc-800 disabled:opacity-50"
        >
          {pending ? "Working…" : submitLabel}
        </button>
      </form>
      <p className="mt-4 text-sm">
        <Link href={altHref} className="text-zinc-700 underline hover:text-zinc-900">
          {altLabel}
        </Link>
      </p>
    </main>
  );
}
