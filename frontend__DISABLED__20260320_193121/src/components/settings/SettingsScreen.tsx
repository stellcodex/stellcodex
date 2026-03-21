"use client";

import * as React from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import { PageHeader } from "@/components/shell/PageHeader";
import { logout } from "@/lib/api/auth";
import type { RawSessionState } from "@/lib/contracts/auth";

export interface SettingsScreenProps {
  initialSession: RawSessionState;
}

export function SettingsScreen({ initialSession }: SettingsScreenProps) {
  const router = useRouter();
  const [session, setSession] = React.useState<RawSessionState>(initialSession);
  const [message, setMessage] = React.useState<string | null>(null);
  const [isPending, startTransition] = React.useTransition();

  async function handleLogout() {
    await logout();
    setSession({ authenticated: false, role: null, user: null });
    setMessage("Signed out.");
    startTransition(() => {
      router.push("/sign-in");
      router.refresh();
    });
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-5xl items-start px-6 py-10">
      <div className="w-full space-y-6">
        <PageHeader
          subtitle="Review the active workspace session, role, and authentication provider."
          title="Settings"
        />
        <Card
          description="Protected workspace access is cookie-backed and limited to authenticated members or admins."
          title="Active session"
        >
          <div className="space-y-4">
            <div className="grid gap-3 rounded-[var(--radius-lg)] border border-[var(--border-muted)] bg-white p-5 text-sm md:grid-cols-2">
              <div>
                <div className="text-[var(--foreground-soft)]">Status</div>
                <div className="font-medium text-[var(--foreground-strong)]">{session.authenticated ? "Authenticated" : "Unauthenticated"}</div>
              </div>
              <div>
                <div className="text-[var(--foreground-soft)]">Role</div>
                <div className="font-medium text-[var(--foreground-strong)]">{session.role ?? "None"}</div>
              </div>
              <div>
                <div className="text-[var(--foreground-soft)]">Email</div>
                <div className="font-medium text-[var(--foreground-strong)]">{session.user?.email ?? "No active session"}</div>
              </div>
              <div>
                <div className="text-[var(--foreground-soft)]">Auth provider</div>
                <div className="font-medium text-[var(--foreground-strong)]">{session.user?.auth_provider ?? "None"}</div>
              </div>
            </div>
            <div className="flex gap-3">
              <Button onClick={() => router.push("/dashboard")} variant="secondary">
                Open dashboard
              </Button>
              <Button disabled={isPending} onClick={() => void handleLogout()} variant="primary">
                {isPending ? "Signing out..." : "Logout"}
              </Button>
            </div>
            <div className="text-sm leading-6 text-[var(--foreground-muted)]">
              Local password login and Google sign-in are available at the dedicated sign-in route. Settings is no longer
              used as the public auth gate.
            </div>
            {message ? <div className="text-sm text-[var(--foreground-muted)]">{message}</div> : null}
          </div>
        </Card>
      </div>
    </div>
  );
}
