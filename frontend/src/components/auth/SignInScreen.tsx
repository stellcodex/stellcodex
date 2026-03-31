"use client";

import * as React from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import { Input } from "@/components/primitives/Input";
import { login } from "@/lib/api/auth";

export interface SignInScreenProps {
  authCode?: string | null;
  nextPath: string;
}

function resolveAuthMessage(authCode?: string | null) {
  if (!authCode) return null;
  if (authCode === "google-denied") return "Google sign-in was cancelled.";
  if (authCode === "google-state") return "Google sign-in could not verify the session.";
  if (authCode === "google-failed") return "Google sign-in failed.";
  if (authCode === "google-missing") return "Google sign-in callback was incomplete.";
  return null;
}

export function SignInScreen({ authCode, nextPath }: SignInScreenProps) {
  const router = useRouter();
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [message, setMessage] = React.useState<string | null>(resolveAuthMessage(authCode));
  const [googleReady, setGoogleReady] = React.useState(false);
  const [googleLoading, setGoogleLoading] = React.useState(true);
  const [googleMessage, setGoogleMessage] = React.useState<string | null>(null);
  const [isPending, startTransition] = React.useTransition();

  React.useEffect(() => {
    let active = true;

    async function checkGoogleAvailability() {
      setGoogleLoading(true);
      try {
        const response = await fetch("/google-auth/availability", {
          cache: "no-store",
          credentials: "include",
        });
        const payload = (await response.json().catch(() => null)) as { available?: unknown; message?: unknown } | null;
        if (!active) return;
        const available = payload?.available === true;
        const detail = typeof payload?.message === "string" ? payload.message : null;
        setGoogleReady(available);
        setGoogleMessage(available ? null : detail || "Google sign-in is unavailable.");
      } catch {
        if (!active) return;
        setGoogleReady(false);
        setGoogleMessage("Google sign-in availability could not be verified.");
      } finally {
        if (active) {
          setGoogleLoading(false);
        }
      }
    }

    void checkGoogleAvailability();
    return () => {
      active = false;
    };
  }, []);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage(null);

    try {
      await login(email.trim(), password);
      setPassword("");
      startTransition(() => {
        router.push(nextPath);
        router.refresh();
      });
    } catch (caughtError) {
      setMessage(caughtError instanceof Error ? caughtError.message : "Sign-in failed.");
    }
  }

  function handleGoogleSignIn() {
    if (!googleReady) {
      setMessage(googleMessage || "Google sign-in is unavailable.");
      return;
    }
    const search = new URLSearchParams({ next: nextPath });
    window.location.assign(`https://api.stellcodex.com/api/v1/auth/google/start?${search.toString()}`);
  }

  return (
    <main className="min-h-screen bg-white px-4 py-10">
      <div className="mx-auto max-w-[900px] space-y-6">
        <div className="space-y-2">
          <div className="text-[18px] font-semibold text-[var(--foreground-strong)]">STELLCODEX</div>
          <p className="text-sm leading-5 text-[var(--foreground-muted)]">
            Sign in to continue to the workspace.
          </p>
        </div>

        <Card title="Sign in">
          <div className="space-y-4">
            <form className="space-y-4" onSubmit={(event) => void handleSubmit(event)}>
              <div className="space-y-2">
                <label className="text-sm font-medium text-[var(--foreground-strong)]" htmlFor="sign-in-email">
                  Email
                </label>
                <Input
                  autoComplete="email"
                  id="sign-in-email"
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="engineer@example.com"
                  value={email}
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-[var(--foreground-strong)]" htmlFor="sign-in-password">
                  Password
                </label>
                <Input
                  autoComplete="current-password"
                  id="sign-in-password"
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="Password"
                  type="password"
                  value={password}
                />
              </div>

              <div className="flex flex-wrap gap-2">
                <Button disabled={isPending} size="sm" type="submit" variant="primary">
                  {isPending ? "Signing in..." : "Sign in"}
                </Button>
                <Button disabled={isPending || googleLoading || !googleReady} onClick={handleGoogleSignIn} size="sm" type="button" variant="secondary">
                  {googleLoading ? "Checking Google..." : googleReady ? "Continue with Google" : "Google unavailable"}
                </Button>
              </div>
            </form>

            {nextPath !== "/dashboard" ? <div className="text-sm text-[var(--foreground-muted)]">Next: {nextPath}</div> : null}
            {!googleLoading && googleMessage ? <div className="text-sm text-[var(--foreground-muted)]">{googleMessage}</div> : null}
            {message ? <div className="text-sm text-[var(--foreground-default)]">{message}</div> : null}
          </div>
        </Card>
      </div>
    </main>
  );
}
