import type { ReactNode } from "react";
import { AppShell } from "@/components/shell/AppShell";

export default function LibraryRoutesLayout({ children }: { children: ReactNode }) {
  return <AppShell section="library">{children}</AppShell>;
}
