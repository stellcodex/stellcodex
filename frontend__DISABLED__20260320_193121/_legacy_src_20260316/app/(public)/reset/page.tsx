"use client";
import { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { getApiBase } from "@/lib/apiClient";
import { AuthShell, authInputClassName, authPrimaryButtonClassName } from "@/components/auth/AuthShell";

function ResetForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) { setError("Invalid or missing token."); return; }
    setError(null);
    setLoading(true);
    try {
      const res = await fetch(`${getApiBase()}/auth/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, password }),
      });
      if (!res.ok) throw new Error("Reset failed.");
      router.push("/login?message=Password updated.");
    } catch {
      setError("Reset failed. Link may be expired.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-5">
      <div>
        <label className="mb-2 block text-xs font-semibold uppercase tracking-[0.24em] text-[#6b7280]">New password</label>
        <input type="password" required value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" className={authInputClassName} />
      </div>
      {error ? <div className="rounded-2xl border border-[#f1c9c9] bg-[#fff5f5] px-4 py-3 text-sm text-[#b42318]">{error}</div> : null}
      <button type="submit" disabled={loading} className={authPrimaryButtonClassName}>
        {loading ? "Updating password..." : "Update password"}
      </button>
    </form>
  );
}

export default function ResetPage() {
  return (
    <AuthShell
      eyebrow="Security"
      title="Set a new password"
      description="Use a strong password, then return to the suite and continue in the same workspace."
    >
      <Suspense fallback={<div className="rounded-2xl border border-[#d7dfde] bg-[#f8faf9] px-4 py-3 text-sm text-[#6b7280]">Loading reset form...</div>}>
        <ResetForm />
      </Suspense>
    </AuthShell>
  );
}
