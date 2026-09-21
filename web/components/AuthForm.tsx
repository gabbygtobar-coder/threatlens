"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { createClient } from "@/lib/supabase/client";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Label } from "@/components/ui/field";

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
          "Account created, but this project requires email confirmation. Check your inbox, then log in. For local demos, turn off Confirm email in Supabase Auth settings.",
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
    <main className="mx-auto flex w-full max-w-md flex-col px-4 py-12 sm:px-6">
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
          <CardDescription>
            Email and password via Supabase Auth. No social providers, no SSO. Saving analyses
            requires a session; running <code className="font-mono">/detect</code> does not.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={(event) => void onSubmit(event)} className="space-y-4" noValidate>
            <div>
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                className="mt-1"
                aria-invalid={Boolean(error)}
                disabled={pending}
              />
            </div>
            <div>
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                autoComplete={mode === "login" ? "current-password" : "new-password"}
                required
                minLength={6}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="mt-1"
                aria-invalid={Boolean(error)}
                disabled={pending}
              />
              {mode === "signup" ? (
                <p className="mt-1 text-xs text-zinc-500">At least 6 characters (Supabase default).</p>
              ) : null}
            </div>
            {error ? <Alert variant="error">{error}</Alert> : null}
            {info ? <Alert variant="info">{info}</Alert> : null}
            <Button type="submit" className="w-full" disabled={pending} aria-busy={pending}>
              {pending ? (mode === "login" ? "Signing in…" : "Creating account…") : submitLabel}
            </Button>
          </form>
          <p className="mt-4 text-sm text-zinc-400">
            <Link href={altHref} className="text-sky-400 hover:text-sky-300">
              {altLabel}
            </Link>
          </p>
        </CardContent>
      </Card>
    </main>
  );
}
