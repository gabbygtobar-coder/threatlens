import { redirect } from "next/navigation";

import { AuthForm } from "@/components/AuthForm";
import { SetupNeeded } from "@/components/SetupNeeded";
import { getCurrentUser } from "@/lib/auth";
import { isSupabaseConfigured } from "@/lib/env";

export const metadata = {
  title: "Log in",
};

export const dynamic = "force-dynamic";

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string }>;
}) {
  if (!isSupabaseConfigured()) {
    return <SetupNeeded purpose="Log in uses Supabase Auth." />;
  }

  const user = await getCurrentUser();
  if (user) {
    redirect("/");
  }

  const params = await searchParams;
  const nextPath = safeNext(params.next);

  return <AuthForm mode="login" nextPath={nextPath} />;
}

function safeNext(value: string | undefined): string {
  if (value && value.startsWith("/") && !value.startsWith("//")) {
    return value;
  }
  return "/";
}
