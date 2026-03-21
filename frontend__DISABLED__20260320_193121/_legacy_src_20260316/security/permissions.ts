import { ACCESS_CONTROL } from "./access_control.generated";
import { PermissionKey, isPermissionKey } from "./permissions.generated";

export type PermissionSet = Array<PermissionKey | "*">;
export type SessionUser = { role?: string | null; permissions?: PermissionSet | null };

type AccessRole = keyof typeof ACCESS_CONTROL.role_grants;

const USER_TOKEN_KEY = "scx_token";

function isAccessRole(value: string): value is AccessRole {
  return value in ACCESS_CONTROL.role_grants;
}

function readJwtPayload(token: string): Record<string, unknown> | null {
  try {
    const [, payload] = token.split(".");
    if (!payload) return null;
    const normalized = payload.replace(/-/g, "+").replace(/_/g, "/");
    const padded = normalized.padEnd(normalized.length + ((4 - (normalized.length % 4)) % 4), "=");
    const json = window.atob(padded);
    const decoded = JSON.parse(json);
    return decoded && typeof decoded === "object" ? (decoded as Record<string, unknown>) : null;
  } catch {
    return null;
  }
}

function normalizePermissionSet(value: unknown): PermissionSet | null {
  if (!Array.isArray(value)) return null;

  const perms = value.filter((item): item is PermissionKey | "*" => item === "*" || (typeof item === "string" && isPermissionKey(item)));
  if (perms.includes("*")) return ["*"];
  return perms;
}

export function getPermissionsForRole(role: string | null | undefined): PermissionSet {
  if (!role || !isAccessRole(role)) return [];
  const grants = ACCESS_CONTROL.role_grants[role] as readonly string[];
  if (grants.some((grant) => grant === "*")) return ["*"];
  return grants.filter((grant): grant is PermissionKey => isPermissionKey(grant));
}

export function hasPermission(perms: PermissionSet | null | undefined, permKey: string): boolean {
  if (!perms || !permKey) return false;
  if (perms.includes("*")) return true;
  if (!isPermissionKey(permKey)) return false;
  return perms.includes(permKey);
}

export function getSessionPermissions(): PermissionSet {
  if (typeof window === "undefined") return [];

  const token = window.localStorage.getItem(USER_TOKEN_KEY);
  if (!token) return [];

  const payload = readJwtPayload(token);
  if (!payload || payload.typ !== "user") return [];

  const explicitPermissions = normalizePermissionSet(payload.permissions);
  if (explicitPermissions) return explicitPermissions;

  return getPermissionsForRole(typeof payload.role === "string" ? payload.role : null);
}
