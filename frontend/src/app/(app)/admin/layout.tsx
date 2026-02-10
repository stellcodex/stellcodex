"use client";

import type { ReactNode } from "react";
import { AdminShell } from "@/components/layout/AdminShell";
import { RouteGuard } from "@/security/route-guards";

export default function AdminLayout({ children }: { children: ReactNode }) {
  return (
    <AdminShell>
      <RouteGuard>{children}</RouteGuard>
    </AdminShell>
  );
}
