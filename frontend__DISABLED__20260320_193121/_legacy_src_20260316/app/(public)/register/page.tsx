"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getApiBase } from "@/lib/apiClient";
import { AuthShell, authInputClassName, authPrimaryButtonClassName } from "@/components/auth/AuthShell";

export default function RegisterPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await fetch(`${getApiBase()}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, password }),
      });
      const data = await res.json().catch(() => null);
      if (!res.ok) {
        setError(data?.detail || "Registration failed. Please try again.");
        return;
      }
      router.push("/login?message=Account created. Please log in.");
    } catch {
      setError("Cannot connect to server.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell
      eyebrow="Account Setup"
      title="Create account"
      description="Set up a clean STELLCODEX workspace and keep files routed into the right application from the first upload."
      footer={
        <>
          <span>Already registered?</span>{" "}
          <Link href="/login" className="font-semibold text-[#0f766e] hover:underline">
            Sign in
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="flex flex-col gap-5">
        <div>
          <label className="mb-2 block text-xs font-semibold uppercase tracking-[0.24em] text-[#6b7280]">Full name</label>
          <input type="text" required value={name} onChange={(e) => setName(e.target.value)} placeholder="Jane Doe" className={authInputClassName} />
        </div>

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
          <label className="mb-2 block text-xs font-semibold uppercase tracking-[0.24em] text-[#6b7280]">Password</label>
          <input
            type="password"
            required
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            className={authInputClassName}
          />
        </div>

        {error ? (
          <div className="rounded-2xl border border-[#f1c9c9] bg-[#fff5f5] px-4 py-3 text-sm text-[#b42318]">
            {error}
          </div>
        ) : null}

        <button type="submit" disabled={loading} className={authPrimaryButtonClassName}>
          {loading ? "Creating account..." : "Create account"}
        </button>
      </form>
    </AuthShell>
  );
}
