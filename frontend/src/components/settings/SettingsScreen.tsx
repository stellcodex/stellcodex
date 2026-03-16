"use client";

import * as React from "react";

import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import { Input } from "@/components/primitives/Input";
import { PageHeader } from "@/components/shell/PageHeader";
import { getMe, login, logout } from "@/lib/api/auth";

export function SettingsScreen() {
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [sessionLabel, setSessionLabel] = React.useState("Guest session");
  const [message, setMessage] = React.useState<string | null>(null);

  React.useEffect(() => {
    void getMe()
      .then((user) => setSessionLabel(user.email))
      .catch(() => setSessionLabel("Guest session"));
  }, []);

  async function handleLogin() {
    setMessage(null);
    try {
      const result = await login(email, password);
      setSessionLabel(result.email);
      setMessage("User session established.");
    } catch (caughtError) {
      setMessage(caughtError instanceof Error ? caughtError.message : "Login failed.");
    }
  }

  async function handleLogout() {
    await logout();
    setSessionLabel("Guest session");
    setMessage("Session cleared.");
  }

  return (
    <div className="space-y-6">
      <PageHeader subtitle="Minimal session controls only. No fake account management surfaces are created." title="Settings" />
      <Card description="Guest access remains the default session path. User sign-in is only surfaced when the backend user contract is available." title="Session">
        <div className="space-y-4">
          <div className="text-sm">
            Current session: <span className="font-medium">{sessionLabel}</span>
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            <Input onChange={(event) => setEmail(event.target.value)} placeholder="engineer@example.com" value={email} />
            <Input onChange={(event) => setPassword(event.target.value)} placeholder="Password" type="password" value={password} />
          </div>
          <div className="flex gap-3">
            <Button onClick={() => void handleLogin()} variant="primary">
              Sign in
            </Button>
            <Button onClick={() => void handleLogout()}>Logout</Button>
          </div>
          {message ? <div className="text-sm text-[var(--foreground-muted)]">{message}</div> : null}
        </div>
      </Card>
    </div>
  );
}
