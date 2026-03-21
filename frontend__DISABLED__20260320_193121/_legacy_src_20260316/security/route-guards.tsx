"use client";

import type { ReactNode } from "react";
import { usePathname } from "next/navigation";
import { useUser } from "@/context/UserContext";
import { ErrorState, LoadingState } from "@/components/ui/StateBlocks";
import { BLOCKING_PERMISSION, ROUTE_PERMISSION_MAP } from "./route-permissions";
import { getPermissionsForRole, getSessionPermissions, hasPermission } from "./permissions";

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
  const { user, isAuthenticated, loading } = useUser();
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

  const eagerPerms = getSessionPermissions();
  const perms = eagerPerms.length > 0 ? eagerPerms : getPermissionsForRole(isAuthenticated ? user.role : null);

  if (loading && perms.length === 0) {
    return (
      fallback ?? (
        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <LoadingState lines={3} />
        </div>
      )
    );
  }

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
