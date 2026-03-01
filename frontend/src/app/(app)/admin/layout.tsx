"use client";

import type { ReactNode } from "react";
import { AdminGuard } from "@/security/token-guards";

export default function AdminLayout({ children }: { children: ReactNode }) {
  return <AdminGuard>{children}</AdminGuard>;
}
