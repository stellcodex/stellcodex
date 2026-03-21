"use client";

import * as React from "react";
import { usePathname, useSearchParams } from "next/navigation";

import { AUTH_EXPIRED_EVENT } from "@/lib/api/fetch";
import type { SessionUser } from "@/lib/contracts/ui";
import { cn } from "@/lib/utils";
import { useUiStore } from "@/lib/stores/uiStore";

import { AppHeader } from "./AppHeader";
import { AppSidebar } from "./AppSidebar";

export const appShellRootClassName = "min-h-screen bg-white text-[var(--foreground-default)]";

export interface AppShellProps {
  children: React.ReactNode;
  session: SessionUser;
}

export function AppShell({ children, session }: AppShellProps) {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const collapsed = useUiStore((state) => state.sidebarCollapsed);
  const toggleSidebarCollapsed = useUiStore((state) => state.toggleSidebarCollapsed);
  const authRedirectingRef = React.useRef(false);
  const viewerRoute = pathname.startsWith("/files/") && pathname.endsWith("/viewer");

  React.useEffect(() => {
    function handleAuthExpired() {
      if (authRedirectingRef.current) return;
      authRedirectingRef.current = true;
      const query = searchParams.toString();
      const nextPath = pathname ? `${pathname}${query ? `?${query}` : ""}` : "/dashboard";
      window.location.assign(`/sign-in?next=${encodeURIComponent(nextPath)}`);
    }

    window.addEventListener(AUTH_EXPIRED_EVENT, handleAuthExpired);
    return () => {
      window.removeEventListener(AUTH_EXPIRED_EVENT, handleAuthExpired);
    };
  }, [pathname, searchParams]);

  return (
    <div className={appShellRootClassName} data-sidebar-state={collapsed ? "collapsed" : "expanded"}>
      <div className="grid min-h-screen grid-cols-[auto_minmax(0,1fr)]">
        <AppSidebar collapsed={collapsed} onToggle={toggleSidebarCollapsed} />
        <div className="min-w-0 bg-white">
          <AppHeader userLabel={session.label} />
          <main className={cn("min-w-0", viewerRoute ? "h-[calc(100vh-73px)] overflow-hidden px-4 py-4" : "px-4 py-6 lg:px-6")}>
            <div className={cn("w-full", viewerRoute ? "h-full" : "mx-auto max-w-[900px]")}>{children}</div>
          </main>
        </div>
      </div>
    </div>
  );
}
