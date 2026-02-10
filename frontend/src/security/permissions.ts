import { PermissionKey, isPermissionKey } from "./permissions.generated";

export type PermissionSet = Array<PermissionKey | "*">;
export type SessionUser = { permissions?: PermissionSet | null };

export function hasPermission(perms: PermissionSet | null | undefined, permKey: string): boolean {
  if (!perms || !permKey) return false;
  if (perms.includes("*")) return true;
  if (!isPermissionKey(permKey)) return false;
  return perms.includes(permKey);
}

export function getSessionPermissions(): PermissionSet {
  // TODO: Wire to real auth/session payload (JWT, cookie, or /api/session).
  return [];
}
