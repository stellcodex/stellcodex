"use client";

import type { ReactNode } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { AdminGuard } from "@/security/token-guards";

export default function AdminLayout({ children }: { children: ReactNode }) {
  return (
    <AppShell>
      <AdminGuard>{children}</AdminGuard>
    </AppShell>
  );
}
