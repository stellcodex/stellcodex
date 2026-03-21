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
    await logout().catch(() => undefined);
    setSession({ authenticated: false, role: null, user: null });
    setMessage("Signed out.");
    startTransition(() => {
      window.location.assign("/sign-in");
    });
  }

  return (
    <div className="mx-auto max-w-[900px] space-y-6">
      <PageHeader subtitle="Session details" title="Settings" />
      <Card title="Session">
        <div className="space-y-4">
          <div className="space-y-3 text-sm">
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
          <div className="flex flex-wrap gap-2">
            <Button onClick={() => router.push("/dashboard")} variant="secondary">
              Open dashboard
            </Button>
            <Button disabled={isPending} onClick={() => void handleLogout()} variant="primary">
              {isPending ? "Signing out..." : "Logout"}
            </Button>
          </div>
          {message ? <div className="text-sm text-[var(--foreground-muted)]">{message}</div> : null}
        </div>
      </Card>
    </div>
  );
}
