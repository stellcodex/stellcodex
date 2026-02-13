"use client";

import type { ReactNode } from "react";
import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { getMe } from "@/services/api";
import { EmptyState } from "@/components/ui/EmptyState";
import { Button } from "@/components/ui/Button";

type GuardState = "loading" | "allowed" | "denied" | "token_missing";

function getUserToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem("scx_token");
}

export function AdminGuard({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [state, setState] = useState<GuardState>("loading");
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    const token = getUserToken();
    if (!token) {
      setState("token_missing");
      setNotice("Yönetici erişimi için token gerekli.");
      return;
    }
    getMe()
      .then((me) => {
        if (me?.role === "admin") {
          setState("allowed");
        } else {
          setState("denied");
          setNotice("Yetkin yok.");
          router.replace("/");
        }
      })
      .catch(() => {
        setState("denied");
        setNotice("Yetkin yok.");
        router.replace("/");
      });
  }, [router]);

  if (state === "allowed") return <>{children}</>;
  if (state === "token_missing" || state === "denied") {
    return <EmptyState title="Yetkin yok" description={notice || "Yetkin yok."} />;
  }
  return (
    <EmptyState
      title="Kontrol ediliyor"
      description="Yetkin kontrolü yapılıyor."
    />
  );
}

export function UserGuard({ children }: { children: ReactNode }) {
  const [state, setState] = useState<GuardState>("loading");
  const [tokenInput, setTokenInput] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const canShowTokenForm = useMemo(
    () => state === "token_missing" || state === "denied",
    [state]
  );

  const verifyToken = async (token: string) => {
    if (!token.trim()) {
      setError("Token gerekli.");
      return;
    }
    if (typeof window !== "undefined") {
      window.localStorage.setItem("scx_token", token.trim());
    }
    setSaving(true);
    setError(null);
    try {
      await getMe();
      setState("allowed");
    } catch {
      if (typeof window !== "undefined") {
        window.localStorage.removeItem("scx_token");
      }
      setState("denied");
      setError("Token geçersiz veya süresi dolmuş.");
    } finally {
      setSaving(false);
    }
  };

  useEffect(() => {
    const token = getUserToken();
    if (!token) {
      setState("token_missing");
      return;
    }
    getMe()
      .then(() => setState("allowed"))
      .catch(() => setState("denied"));
  }, []);

  if (state === "allowed") return <>{children}</>;
  if (canShowTokenForm) {
    return (
      <EmptyState
        title="Token gerekli"
        description="Panel erişimi için scx_token gerekli."
        action={
          <div className="grid gap-2">
            <label className="text-xs text-[#4f6f6b]" htmlFor="scx-token-input">
              Token
            </label>
            <input
              id="scx-token-input"
              type="text"
              value={tokenInput}
              onChange={(e) => setTokenInput(e.target.value)}
              className="w-full rounded-lg border border-[#d7d3c8] bg-white px-3 py-2 text-sm outline-none focus:border-[#0c3b3a] focus:ring-2 focus:ring-[#0c3b3a]/20"
              placeholder="scx_token"
              aria-label="Token gir"
            />
            {error ? <div className="text-xs text-red-600">{error}</div> : null}
            <Button
              onClick={() => void verifyToken(tokenInput)}
              disabled={saving}
            >
              {saving ? "Doğrulanıyor..." : "Kaydet"}
            </Button>
          </div>
        }
      />
    );
  }
  return (
    <EmptyState
      title="Kontrol ediliyor"
      description="Yetkin kontrolü yapılıyor."
    />
  );
}
