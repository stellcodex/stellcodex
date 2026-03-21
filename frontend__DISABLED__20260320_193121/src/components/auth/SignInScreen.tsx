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
  const [isPending, startTransition] = React.useTransition();

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
    const search = new URLSearchParams({ next: nextPath });
    window.location.assign(`/api/v1/auth/google/start?${search.toString()}`);
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-white px-6 py-10">
      <div className="grid w-full max-w-5xl gap-12 lg:grid-cols-[minmax(0,1fr)_420px]">
        <div className="flex flex-col justify-center space-y-6">
          <div className="space-y-3">
            <div className="text-sm font-semibold uppercase tracking-[0.26em] text-[var(--foreground-soft)]">STELLCODEX</div>
            <h1 className="max-w-2xl text-4xl font-semibold tracking-[-0.05em] text-[var(--foreground-strong)]">
              Manufacturing decision workspace
            </h1>
            <p className="max-w-xl text-base leading-7 text-[var(--foreground-muted)]">
              Sign in to access dashboard, projects, files, viewer, shares, and admin surfaces. Public share links remain
              token-scoped and separate from the workspace.
            </p>
          </div>
          <div className="max-w-xl rounded-[var(--radius-xl)] border border-[var(--border-muted)] bg-white px-5 py-4 text-sm leading-6 text-[var(--foreground-muted)]">
            Protected workspace access is limited to authenticated members and admins. Guest workspace mode is disabled.
          </div>
        </div>
        <Card className="self-center border-[var(--border-muted)] p-7 shadow-[var(--shadow-sm)]">
          <div className="space-y-6">
            <div className="space-y-2">
              <h2 className="text-2xl font-semibold tracking-[-0.03em] text-[var(--foreground-strong)]">Sign in</h2>
              <p className="text-sm leading-6 text-[var(--foreground-muted)]">
                {nextPath !== "/dashboard" ? `You will return to ${nextPath} after authentication.` : "Open the workspace with your member or admin session."}
              </p>
            </div>
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
              <div className="flex flex-col gap-3">
                <Button disabled={isPending} size="lg" type="submit" variant="primary">
                  {isPending ? "Signing in..." : "Sign in"}
                </Button>
                <Button disabled={isPending} onClick={handleGoogleSignIn} size="lg" type="button" variant="secondary">
                  Continue with Google
                </Button>
              </div>
            </form>
            {message ? <div className="text-sm text-[var(--status-danger-fg)]">{message}</div> : null}
          </div>
        </Card>
      </div>
    </div>
  );
}
