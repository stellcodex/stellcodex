import type { ReactNode } from "react";
import { AppShell } from "@/components/shell/AppShell";

export default function AppRoutesLayout({ children }: { children: ReactNode }) {
  return <AppShell section="apps">{children}</AppShell>;
}
