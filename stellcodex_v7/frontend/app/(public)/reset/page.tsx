"use client";
import { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { getApiBase } from "@/lib/apiClient";

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
      const res = await fetch(`${getApiBase()}/auth/reset`, {
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
        <label className="mb-2 block text-xs font-semibold uppercase tracking-wider text-gray-500">New Password</label>
        <input type="password" required value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" className="w-full rounded-lg border border-gray-700 bg-black/30 px-4 py-3 text-sm text-white outline-none focus:border-blue-500 transition-colors" />
      </div>
      {error && <div className="text-xs text-red-400">{error}</div>}
      <button type="submit" disabled={loading} className="w-full rounded-lg bg-blue-600 py-3 text-sm font-bold text-white shadow-lg hover:bg-blue-500 transition-all">
        {loading ? "UPDATING..." : "UPDATE PASSWORD"}
      </button>
    </form>
  );
}

export default function ResetPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[#1a1a1a] px-4 text-gray-100">
      <div className="w-full max-w-md">
        <section className="rounded-2xl border border-gray-800 bg-[#2d2d2d] p-8 shadow-xl">
          <div className="text-[10px] font-bold uppercase tracking-[0.3em] text-blue-500 mb-2">Security</div>
          <h1 className="text-2xl font-semibold text-white">New Password</h1>
          <p className="text-gray-400 text-sm mt-1">Choose a strong engineering-grade password.</p>
          <Suspense fallback={<div className="text-gray-500 mt-8">Loading...</div>}>
            <ResetForm />
          </Suspense>
        </section>
      </div>
    </main>
  );
}
