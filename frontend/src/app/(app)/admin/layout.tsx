"use client";

import type { ReactNode } from "react";
import { AdminShell } from "@/components/layout/AdminShell";
import { AdminGuard } from "@/security/token-guards";

export default function AdminLayout({ children }: { children: ReactNode }) {
  return (
    <AdminShell>
      <AdminGuard>{children}</AdminGuard>
    </AdminShell>
  );
}
