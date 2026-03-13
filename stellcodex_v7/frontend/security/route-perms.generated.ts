// AUTO-GENERATED. DO NOT EDIT.
// source: /var/www/stellcodex/security/rbac.policy.json

export const ROUTE_PERMS: Array<{ prefix: string; perm: string }> = [
  {
    "prefix": "/admin/presentations",
    "perm": "admin.presentations.read"
  },
  {
    "prefix": "/admin/approvals",
    "perm": "approvals.read"
  },
  {
    "prefix": "/admin/security",
    "perm": "security.policies.read"
  },
  {
    "prefix": "/admin/settings",
    "perm": "rbac.roles.read"
  },
  {
    "prefix": "/admin/library",
    "perm": "admin.library.read"
  },
  {
    "prefix": "/admin/content",
    "perm": "admin.library.read"
  },
  {
    "prefix": "/admin/shares",
    "perm": "admin.shares.read"
  },
  {
    "prefix": "/admin/system",
    "perm": "system.status.read"
  },
  {
    "prefix": "/admin/users",
    "perm": "admin.users.read"
  },
  {
    "prefix": "/admin/files",
    "perm": "admin.files.read"
  },
  {
    "prefix": "/admin/notes",
    "perm": "admin.notes.read"
  },
  {
    "prefix": "/admin/roles",
    "perm": "rbac.roles.read"
  },
  {
    "prefix": "/admin/audit",
    "perm": "logs.audit.read"
  },
  {
    "prefix": "/admin/logs",
    "perm": "logs.audit.read"
  },
  {
    "prefix": "/admin/ai",
    "perm": "ai.suggestions.read"
  },
  {
    "prefix": "/admin",
    "perm": "system.status.read"
  }
] as const;
