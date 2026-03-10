import type { ReactNode } from "react";
import { MasterFrame } from "@/components/layout/MasterFrame";

// Public pages should refresh on a calm interval in Vercel without forcing request-time rendering.
export const revalidate = 1800;

export default function PublicLayout({ children }: { children: ReactNode }) {
  return <MasterFrame>{children}</MasterFrame>;
}
