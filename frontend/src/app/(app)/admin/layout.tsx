"use client";

import type { ReactNode } from "react";
import { AdminGuard } from "@/security/token-guards";
import { RouteGuard } from "@/security/route-guards";

export default function AdminLayout({ children }: { children: ReactNode }) {
  return (
    <AdminGuard>
      <RouteGuard>{children}</RouteGuard>
    </AdminGuard>
  );
}
