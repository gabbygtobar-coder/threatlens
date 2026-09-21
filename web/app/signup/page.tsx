import { redirect } from "next/navigation";

import { AuthForm } from "@/components/AuthForm";
import { SetupNeeded } from "@/components/SetupNeeded";
import { getCurrentUser } from "@/lib/auth";
import { isSupabaseConfigured } from "@/lib/env";

export const metadata = {
  title: "Sign up",
};

export const dynamic = "force-dynamic";

export default async function SignupPage() {
  if (!isSupabaseConfigured()) {
    return <SetupNeeded purpose="Sign up uses Supabase Auth." />;
  }

  const user = await getCurrentUser();
  if (user) {
    redirect("/");
  }

  return <AuthForm mode="signup" nextPath="/analyze" />;
}
