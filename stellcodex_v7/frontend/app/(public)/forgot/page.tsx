"use client";
import { useState } from "react";
import Link from "next/link";
import { getApiBase } from "@/lib/apiClient";

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
      const res = await fetch(`${getApiBase()}/auth/forgot`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      if (!res.ok) throw new Error("Request failed.");
      setMessage("Reset link sent if account exists.");
    } catch {
      setError("Service error. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#1a1a1a] px-4 text-gray-100">
      <div className="w-full max-w-md">
        <div className="mb-10 text-center">
          <span className="text-3xl font-bold tracking-tight text-white">STELL<span className="text-blue-500">CONSOLE</span></span>
        </div>
        <section className="rounded-2xl border border-gray-800 bg-[#2d2d2d] p-8 shadow-xl">
          <div className="text-[10px] font-bold uppercase tracking-[0.3em] text-blue-500 mb-2">Recovery</div>
          <h1 className="text-2xl font-semibold text-white">Reset Password</h1>
          <p className="text-gray-400 text-sm mt-1">Enter email to receive a recovery link.</p>
          <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-5">
            <div>
              <label className="mb-2 block text-xs font-semibold uppercase tracking-wider text-gray-500">Email Address</label>
              <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="engineer@stellcodex.com" className="w-full rounded-lg border border-gray-700 bg-black/30 px-4 py-3 text-sm text-white outline-none focus:border-blue-500 transition-colors" />
            </div>
            {error && <div className="text-xs text-red-400">{error}</div>}
            {message && <div className="text-xs text-green-400">{message}</div>}
            <button type="submit" disabled={loading} className="w-full rounded-lg bg-blue-600 py-3 text-sm font-bold text-white shadow-lg hover:bg-blue-500 transition-all">
              {loading ? "SENDING..." : "SEND RESET LINK"}
            </button>
          </form>
          <div className="mt-8 text-center text-xs text-gray-500 border-t border-gray-800 pt-6">
            <Link href="/login" className="text-blue-500 hover:underline font-bold">Back to Login</Link>
          </div>
        </section>
      </div>
    </main>
  );
}
