import type { ReactNode } from "react";

export function TenantGuard({ children }: { children: ReactNode }) {
  return <>{children}</>;
}
