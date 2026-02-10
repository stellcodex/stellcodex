"use client";

import type { ReactNode } from "react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { RouteGuard } from "@/security/route-guards";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <DashboardShell>
      <RouteGuard>{children}</RouteGuard>
    </DashboardShell>
  );
}
