"use client";

import type { ReactNode } from "react";
import { usePathname } from "next/navigation";
import { ErrorState } from "@/components/ui/StateBlocks";
import { BLOCKING_PERMISSION, ROUTE_PERMISSION_MAP } from "./route-permissions";
import { getSessionPermissions, hasPermission } from "./permissions";

function resolveRequiredPermission(pathname: string): string | null {
  let best: { route: string; perm: string } | null = null;
  for (const [route, perm] of Object.entries(ROUTE_PERMISSION_MAP)) {
    if (pathname === route || pathname.startsWith(route + "/")) {
      if (!best || route.length > best.route.length) {
        best = { route, perm };
      }
    }
  }
  return best?.perm ?? null;
}

export function RouteGuard({
  children,
  fallback,
}: {
  children: ReactNode;
  fallback?: ReactNode;
}) {
  const pathname = usePathname() || "/";
  const required = resolveRequiredPermission(pathname);

  if (!required) return <>{children}</>;

  if (required === BLOCKING_PERMISSION) {
    return (
      fallback ?? (
        <ErrorState
          title="Access not configured"
          description="Permission mapping for this route has not been set."
        />
      )
    );
  }

  const perms = getSessionPermissions();
  if (!hasPermission(perms, required)) {
    return (
      fallback ?? (
        <ErrorState
          title="Access denied"
          description="You do not have permission to view this page."
        />
      )
    );
  }

  return <>{children}</>;
}
