import type { ReactNode } from "react";
import { LeftNav } from "@/components/layout/LeftNav";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex h-screen overflow-hidden bg-slate-100 text-slate-900">
      <LeftNav />
      <main className="min-w-0 flex-1 overflow-auto">{children}</main>
    </div>
  );
}

