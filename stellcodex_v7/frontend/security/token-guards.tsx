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
      setNotice("A user session is required for admin access.");
      return;
    }
    getMe()
      .then((me) => {
        if (me?.role === "admin") setState("allowed");
        else {
          setState("denied");
          setNotice("Access denied.");
          router.replace("/");
        }
      })
      .catch(() => {
        setState("denied");
        setNotice("Access denied.");
        router.replace("/");
      });
  }, [router]);

  if (state === "allowed") return <>{children}</>;
  if (state === "denied") {
    return <EmptyState title="Access denied" description={notice || "Access denied."} />;
  }
  return <EmptyState title="Checking access" description="Permissions are being verified." />;
}

export function UserGuard({ children }: { children: ReactNode }) {
  // Session UX: the dashboard does not prompt for a token and keeps a single-session feel.
  return <>{children}</>;
}
