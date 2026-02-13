"use client";

import type { ReactNode } from "react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { UserGuard } from "@/security/token-guards";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <DashboardShell>
      <UserGuard>{children}</UserGuard>
    </DashboardShell>
  );
}
