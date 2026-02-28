"use client";

import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getMe } from "@/services/api";
import { EmptyState } from "@/components/ui/EmptyState";

type GuardState = "loading" | "allowed" | "denied";

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
      setState("denied");
      setNotice("Yönetici erişimi için kullanıcı oturumu gerekli.");
      return;
    }
    getMe()
      .then((me) => {
        if (me?.role === "admin") setState("allowed");
        else {
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
  if (state === "denied") {
    return <EmptyState title="Yetkin yok" description={notice || "Yetkin yok."} />;
  }
  return <EmptyState title="Kontrol ediliyor" description="Yetki kontrolü yapılıyor." />;
}

export function UserGuard({ children }: { children: ReactNode }) {
  // Session UX: dashboard token girişi istemez, tek oturum hissi verir.
  return <>{children}</>;
}

