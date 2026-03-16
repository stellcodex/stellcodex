"use client";

import * as React from "react";

import { AppHeader } from "./AppHeader";
import { AppSidebar } from "./AppSidebar";

export interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const [userLabel, setUserLabel] = React.useState("Guest session");

  React.useEffect(() => {
    const token = typeof window === "undefined" ? null : window.localStorage.getItem("scx_token");
    if (token) {
      setUserLabel("Authenticated");
    } else {
      setUserLabel("Guest session");
    }
  }, []);

  function handleLogout() {
    if (typeof window !== "undefined") {
      window.localStorage.removeItem("scx_token");
    }
    setUserLabel("Guest session");
  }

  return (
    <div className="min-h-screen bg-transparent">
      <div className="grid min-h-screen grid-cols-[272px_minmax(0,1fr)]">
        <AppSidebar />
        <div className="min-w-0">
          <AppHeader onLogout={handleLogout} userLabel={userLabel} />
          <main className="px-6 py-6">{children}</main>
        </div>
      </div>
    </div>
  );
}
