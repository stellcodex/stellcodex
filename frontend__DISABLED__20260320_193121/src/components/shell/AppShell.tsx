"use client";

import type { ReactNode } from "react";

import type { SessionUser } from "@/lib/contracts/ui";
import { useUiStore } from "@/lib/stores/uiStore";

import { AppHeader } from "./AppHeader";
import { AppSidebar } from "./AppSidebar";

export const appShellRootClassName = "min-h-screen bg-white text-[var(--foreground-default)]";

export interface AppShellProps {
  children: ReactNode;
  session: SessionUser;
}

export function AppShell({ children, session }: AppShellProps) {
  const collapsed = useUiStore((state) => state.sidebarCollapsed);
  const toggleSidebarCollapsed = useUiStore((state) => state.toggleSidebarCollapsed);

  return (
    <div className={appShellRootClassName} data-sidebar-state={collapsed ? "collapsed" : "expanded"}>
      <div className="grid min-h-screen grid-cols-[auto_minmax(0,1fr)]">
        <AppSidebar collapsed={collapsed} onToggle={toggleSidebarCollapsed} showAdmin={session.role === "admin"} />
        <div className="min-w-0 bg-white">
          <AppHeader userLabel={session.label} userRole={session.role} />
          <main className="px-6 py-6 lg:px-8">{children}</main>
        </div>
      </div>
    </div>
  );
}
