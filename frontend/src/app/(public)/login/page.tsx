"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { getApiBase } from "@/lib/apiClient";
import { AuthShell, authInputClassName, authPrimaryButtonClassName } from "@/components/auth/AuthShell";

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const message = searchParams.get("message");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await fetch(`${getApiBase()}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json().catch(() => null);
      if (!res.ok) {
        setError(data?.detail || "Sign-in failed. Check the email address and password.");
        return;
      }
      const token = data?.access_token;
      if (!token) {
        setError("The server returned an invalid response.");
        return;
      }
      window.localStorage.setItem("scx_token", token);
      document.cookie = `scx_token=${token}; path=/; max-age=86400; SameSite=Lax`;
      router.push("/");
    } catch {
      setError("The server could not be reached. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell
      eyebrow="Workspace Access"
      title="Sign in"
      description="Open the STELLCODEX suite and continue in the responsible application for each file."
      footer={
        <>
          <span>New here?</span>{" "}
          <Link href="/register" className="font-semibold text-[#0f766e] hover:underline">
            Create account
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="flex flex-col gap-5">
        <div>
          <label className="mb-2 block text-xs font-semibold uppercase tracking-[0.24em] text-[#6b7280]">Email address</label>
          <input
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="engineer@stellcodex.com"
            className={authInputClassName}
          />
        </div>

        <div>
          <div className="mb-2 flex items-center justify-between gap-3">
            <label className="block text-xs font-semibold uppercase tracking-[0.24em] text-[#6b7280]">Password</label>
            <Link href="/forgot" className="text-xs font-semibold text-[#0f766e] hover:underline">
              Forgot password?
            </Link>
          </div>
          <input
            type="password"
            required
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            className={authInputClassName}
          />
        </div>

        {message ? (
          <div className="rounded-2xl border border-[#b7d9d5] bg-[#eef8f6] px-4 py-3 text-sm text-[#0f766e]">
            {message}
          </div>
        ) : null}

        {error ? (
          <div className="rounded-2xl border border-[#f1c9c9] bg-[#fff5f5] px-4 py-3 text-sm text-[#b42318]">
            {error}
          </div>
        ) : null}

        <button type="submit" disabled={loading} className={authPrimaryButtonClassName}>
          {loading ? "Signing in..." : "Open STELLCODEX"}
        </button>
      </form>
    </AuthShell>
  );
}
