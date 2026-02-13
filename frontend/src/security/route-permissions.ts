import routeMap from "./route-permissions.json";

export const BLOCKING_PERMISSION = "BLOCKING_PERM_KEY_REQUIRED" as const;

export const ROUTE_PERMISSION_MAP = routeMap as Record<string, string>;

export function listMissingRoutePermissions(): string[] {
  return Object.entries(ROUTE_PERMISSION_MAP)
    .filter(([, perm]) => perm === BLOCKING_PERMISSION)
    .map(([route]) => route)
    .sort();
}

export function assertRoutePermissionsComplete(): void {
  const missing = listMissingRoutePermissions();
  if (missing.length) {
    throw new Error(
      "RBAC rota eşlemesi eksik. Eksik izin anahtarları: " +
        missing.join(", ") +
        ". frontend/src/security/route-permissions.json dosyasını güncelleyin."
    );
  }
}
