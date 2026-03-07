import type { ReactNode } from "react";
import { MasterFrame } from "@/components/layout/MasterFrame";

export default function PublicLayout({ children }: { children: ReactNode }) {
  return <MasterFrame>{children}</MasterFrame>;
}
