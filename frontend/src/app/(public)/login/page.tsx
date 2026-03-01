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
        setError(data?.detail || "Giriş başarısız. Email veya şifre hatalı.");
        return;
      }
      const token = data?.access_token;
      if (!token) {
        setError("Sunucudan geçersiz yanıt alındı.");
        return;
      }
      window.localStorage.setItem("scx_token", token);
      document.cookie = `scx_token=${token}; path=/; max-age=86400; SameSite=Lax`;
      router.push("/dashboard");
    } catch {
      setError("Sunucuya bağlanılamadı. Lütfen tekrar deneyin.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#f5f3ef] px-4">
      <div className="w-full max-w-md">
        <div className="mb-6 text-center">
          <span className="text-2xl font-bold tracking-tight text-[#0c2a2a]">Stellcodex</span>
        </div>

        <section className="rounded-3xl border border-[#d7d3c8] bg-white/90 p-8 shadow-sm">
          <div className="text-xs font-semibold uppercase tracking-[0.2em] text-[#4f6f6b]">Giriş Yap</div>
          <h1 className="mt-2 text-xl font-semibold text-[#0c2a2a]">Hesabına giriş yap</h1>

          <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-4">
            <div>
              <label className="mb-1 block text-sm font-medium text-[#2c4b49]">Email</label>
              <input
                type="email"
                required
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="ornek@sirket.com"
                className="w-full rounded-xl border border-[#d7d3c8] bg-white px-4 py-2.5 text-sm text-[#1f2937] outline-none focus:border-[#4f6f6b] focus:ring-2 focus:ring-[#4f6f6b]/20"
              />
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-[#2c4b49]">Şifre</label>
              <input
                type="password"
                required
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full rounded-xl border border-[#d7d3c8] bg-white px-4 py-2.5 text-sm text-[#1f2937] outline-none focus:border-[#4f6f6b] focus:ring-2 focus:ring-[#4f6f6b]/20"
              />
            </div>

            {error && (
              <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="mt-1 w-full rounded-xl bg-[#0c2a2a] py-2.5 text-sm font-semibold text-white transition hover:bg-[#1a3d3d] disabled:opacity-60"
            >
              {loading ? "Giriş yapılıyor..." : "Giriş Yap"}
            </button>
          </form>

          <div className="mt-5 flex items-center justify-between text-xs text-[#6b7280]">
            <Link href="/register" className="hover:text-[#0c2a2a] hover:underline">
              Hesap oluştur
            </Link>
            <Link href="/dashboard" className="hover:text-[#0c2a2a] hover:underline">
              Misafir olarak devam et
            </Link>
          </div>
        </section>
      </div>
    </main>
  );
}
