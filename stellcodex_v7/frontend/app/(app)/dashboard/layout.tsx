"use client";

import type { ReactNode } from "react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { RouteGuard } from "@/security/route-guards";
import { UserGuard } from "@/security/token-guards";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <DashboardShell>
      <UserGuard>
        <RouteGuard>{children}</RouteGuard>
      </UserGuard>
    </DashboardShell>
  );
}
