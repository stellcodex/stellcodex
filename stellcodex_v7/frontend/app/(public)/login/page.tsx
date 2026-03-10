"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getApiBase } from "@/lib/apiClient";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

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
      router.push("/console"); // Redirect to the NEW console
    } catch {
      setError("The server could not be reached. Please try again.");
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
          <div className="text-[10px] font-bold uppercase tracking-[0.3em] text-blue-500 mb-2">Security Portal</div>
          <h1 className="text-2xl font-semibold text-white">Sign In</h1>
          <p className="text-gray-400 text-sm mt-1">Access your engineering workspace.</p>

          <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-5">
            <div>
              <label className="mb-2 block text-xs font-semibold uppercase tracking-wider text-gray-500">Email Address</label>
              <input
                type="email"
                required
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="engineer@stellcodex.com"
                className="w-full rounded-lg border border-gray-700 bg-black/30 px-4 py-3 text-sm text-white outline-none focus:border-blue-500 transition-colors"
              />
            </div>

            <div>
              <div className="flex justify-between items-center mb-2">
                 <label className="block text-xs font-semibold uppercase tracking-wider text-gray-500">Password</label>
                 <Link href="/forgot" className="text-[10px] text-blue-500 hover:underline uppercase font-bold">Forgot?</Link>
              </div>
              <input
                type="password"
                required
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full rounded-lg border border-gray-700 bg-black/30 px-4 py-3 text-sm text-white outline-none focus:border-blue-500 transition-colors"
              />
            </div>

            {error && (
              <div className="rounded-lg border border-red-900/50 bg-red-900/20 px-4 py-3 text-xs text-red-400">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="mt-2 w-full rounded-lg bg-blue-600 py-3 text-sm font-bold text-white shadow-lg shadow-blue-900/20 hover:bg-blue-500 active:scale-[0.98] transition-all disabled:opacity-50"
            >
              {loading ? "AUTHENTICATING..." : "SIGN IN"}
            </button>
          </form>

          <div className="mt-8 flex items-center justify-center text-xs text-gray-500 border-t border-gray-800 pt-6">
            <span>New here?</span>
            <Link href="/register" className="ml-2 text-blue-500 hover:underline font-bold">Create Account</Link>
          </div>
        </section>
      </div>
    </main>
  );
}
