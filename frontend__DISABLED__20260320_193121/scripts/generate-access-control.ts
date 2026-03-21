import fs from "node:fs";
import path from "node:path";

type AccessControlSource = {
  version?: string;
  roles: string[];
  permissions: Record<string, string>;
  role_permissions: Record<string, string[]>;
  routes: Record<string, string>;
  approval?: { required_for?: string[] };
  kpis?: {
    user?: Array<{ key: string; endpoint: string }>;
    admin?: Array<{ key: string; endpoint: string }>;
  };
  limits?: Record<string, unknown>;
  status?: { mode?: string; components?: string[] };
  community?: { mode?: string; model?: string };
  ui_prefix_permissions?: Array<{ prefix: string; perm: string }>;
  api_endpoint_permissions?: Array<{ method: string; path: string; perm: string; approval_required?: boolean }>;
};

const FRONTEND_ROOT = path.resolve(__dirname, "..");
const REPO_ROOT = path.resolve(__dirname, "..", "..");
const SOURCE_PATH = path.join(FRONTEND_ROOT, "src", "security", "access-control.source.json");
const ROUTE_PERMS_OUT = path.join(FRONTEND_ROOT, "src", "security", "route-permissions.json");
const PERMS_OUT = path.join(FRONTEND_ROOT, "src", "security", "permissions.generated.ts");
const RBAC_OUT = path.join(REPO_ROOT, "security", "rbac.policy.json");
const EXISTING_RBAC = path.join(REPO_ROOT, "security", "rbac.policy.json");

const TODO = "TODO_REQUIRED";

function readJson(filePath: string) {
  return JSON.parse(fs.readFileSync(filePath, "utf-8"));
}

function collectTodos(value: unknown, currentPath: string, out: string[]) {
  if (value === TODO) {
    out.push(currentPath);
    return;
  }
  if (Array.isArray(value)) {
    value.forEach((item, idx) => collectTodos(item, `${currentPath}[${idx}]`, out));
    return;
  }
  if (value && typeof value === "object") {
    for (const [key, val] of Object.entries(value)) {
      collectTodos(val, `${currentPath}.${key}`, out);
    }
  }
}

function ensure(condition: boolean, message: string) {
  if (!condition) {
    console.error(`ACCESS CONTROL GENERATION FAILED: ${message}`);
    process.exit(1);
  }
}

function main() {
  ensure(fs.existsSync(SOURCE_PATH), `source file not found: ${SOURCE_PATH}`);
  const source = readJson(SOURCE_PATH) as AccessControlSource;

  const missing: string[] = [];
  collectTodos(source, "$", missing);
  if (missing.length) {
    console.error("ACCESS CONTROL GENERATION FAILED: TODO_REQUIRED found at:");
    missing.sort().forEach((item) => console.error(` - ${item}`));
    process.exit(1);
  }

  ensure(Array.isArray(source.roles) && source.roles.length > 0, "roles list is required");
  ensure(source.permissions && typeof source.permissions === "object", "permissions map is required");
  ensure(source.role_permissions && typeof source.role_permissions === "object", "role_permissions map is required");
  ensure(source.routes && typeof source.routes === "object", "routes map is required");

  const permKeys = Object.keys(source.permissions).sort();
  ensure(permKeys.length > 0, "permissions list is empty");

  const dupes = permKeys.filter((key, idx) => permKeys.indexOf(key) !== idx);
  ensure(dupes.length === 0, `duplicate permission keys: ${dupes.join(", ")}`);

  for (const role of source.roles) {
    const perms = source.role_permissions[role];
    ensure(Array.isArray(perms), `role_permissions missing for role: ${role}`);
    ensure(perms.length > 0, `role_permissions empty for role: ${role}`);
    const unknown = perms.filter((p) => p !== "*" && !source.permissions[p]);
    ensure(unknown.length === 0, `role ${role} references unknown permissions: ${unknown.join(", ")}`);
  }

  const routeUnknown = Object.values(source.routes).filter((perm) => perm !== "*" && !source.permissions[perm]);
  ensure(routeUnknown.length === 0, `routes reference unknown permissions: ${routeUnknown.join(", ")}`);

  const permissionDefinitions = permKeys.map((key) => ({ key }));

  let uiPrefixPermissions = source.ui_prefix_permissions ?? [];
  let apiEndpointPermissions = source.api_endpoint_permissions ?? [];

  if ((!uiPrefixPermissions.length || !apiEndpointPermissions.length) && fs.existsSync(EXISTING_RBAC)) {
    const existing = readJson(EXISTING_RBAC);
    if (!uiPrefixPermissions.length) uiPrefixPermissions = existing.ui_prefix_permissions ?? [];
    if (!apiEndpointPermissions.length) apiEndpointPermissions = existing.api_endpoint_permissions ?? [];
  }

  const rbacPolicy = {
    version: source.version ?? "1.0",
    roles: source.roles.map((name) => ({ name, permissions: source.role_permissions[name] })),
    permission_definitions: permissionDefinitions,
    ui_prefix_permissions: uiPrefixPermissions,
    api_endpoint_permissions: apiEndpointPermissions,
  };

  fs.writeFileSync(ROUTE_PERMS_OUT, JSON.stringify(source.routes, null, 2) + "\n", "utf-8");

  const permsOut = `// AUTO-GENERATED. DO NOT EDIT.\n// source: ${SOURCE_PATH}\n\n` +
    `export const PERMISSION_KEYS = ${JSON.stringify(permKeys, null, 2)} as const;\n\n` +
    `export type PermissionKey = typeof PERMISSION_KEYS[number];\n\n` +
    `export function isPermissionKey(value: string): value is PermissionKey {\n` +
    `  return (PERMISSION_KEYS as readonly string[]).includes(value);\n` +
    `}\n`;
  fs.writeFileSync(PERMS_OUT, permsOut, "utf-8");

  if (fs.existsSync(path.dirname(RBAC_OUT))) {
    fs.writeFileSync(RBAC_OUT, JSON.stringify(rbacPolicy, null, 2) + "\n", "utf-8");
  } else {
    console.warn(`RBAC output directory missing: ${path.dirname(RBAC_OUT)}. Skipping policy write.`);
  }

  console.log("Access control generation complete.");
}

main();
