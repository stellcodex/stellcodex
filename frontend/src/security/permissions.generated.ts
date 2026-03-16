// AUTO-GENERATED. DO NOT EDIT.
// source: /root/workspace/frontend/src/security/access-control.source.json

export const PERMISSION_KEYS = [
  "admin.files.read",
  "admin.users.read",
  "logs.audit.read",
  "system.queues.read",
  "system.status.read"
] as const;

export type PermissionKey = typeof PERMISSION_KEYS[number];

export function isPermissionKey(value: string): value is PermissionKey {
  return (PERMISSION_KEYS as readonly string[]).includes(value);
}
