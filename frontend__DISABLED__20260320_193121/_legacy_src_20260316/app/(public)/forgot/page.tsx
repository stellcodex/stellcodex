"use client";
import { useState } from "react";
import Link from "next/link";
import { getApiBase } from "@/lib/apiClient";
import { AuthShell, authInputClassName, authPrimaryButtonClassName } from "@/components/auth/AuthShell";

export default function ForgotPage() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setMessage(null);
    setLoading(true);
    try {
      const res = await fetch(`${getApiBase()}/auth/request-password-reset`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      if (!res.ok) throw new Error("Request failed.");
      const payload = await res.json().catch(() => null);
      if (payload && typeof payload === "object" && "delivery_enabled" in payload && !payload.delivery_enabled) {
        setMessage("Password recovery mail is not configured on this deployment. Use a signed-in session or contact an administrator.");
      } else {
        setMessage("Reset link sent if account exists.");
      }
    } catch {
      setError("Service error. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell
      eyebrow="Recovery"
      title="Reset password"
      description="Enter the account email and STELLCODEX will send a recovery link if the account exists."
      footer={
        <Link href="/login" className="font-semibold text-[#0f766e] hover:underline">
          Back to sign in
        </Link>
      }
    >
      <form onSubmit={handleSubmit} className="flex flex-col gap-5">
        <div>
          <label className="mb-2 block text-xs font-semibold uppercase tracking-[0.24em] text-[#6b7280]">Email address</label>
          <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="engineer@stellcodex.com" className={authInputClassName} />
        </div>
        {error ? <div className="rounded-2xl border border-[#f1c9c9] bg-[#fff5f5] px-4 py-3 text-sm text-[#b42318]">{error}</div> : null}
        {message ? <div className="rounded-2xl border border-[#b7d9d5] bg-[#eef8f6] px-4 py-3 text-sm text-[#0f766e]">{message}</div> : null}
        <button type="submit" disabled={loading} className={authPrimaryButtonClassName}>
          {loading ? "Sending reset link..." : "Send reset link"}
        </button>
      </form>
    </AuthShell>
  );
}
