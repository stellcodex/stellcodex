from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "security" / "rbac.policy.json"
OUT_DIR = ROOT / "frontend" / "src" / "security"
MIDDLEWARE_PATH = ROOT / "frontend" / "middleware.ts"
REQUIRED_ROLES = {"admin", "support", "moderator", "user"}


def _ensure_roles_ready(policy: dict) -> None:
    roles = {
        r.get("name"): r.get("permissions", [])
        for r in policy.get("roles", [])
        if isinstance(r, dict)
    }
    missing = [r for r in REQUIRED_ROLES if r not in roles]
    if missing:
        print(f"RBAC generation blocked: missing roles {', '.join(missing)}")
        sys.exit(1)
    empty = [r for r in REQUIRED_ROLES if not roles.get(r)]
    if empty:
        print(
            "RBAC generation blocked: empty role permissions for "
            + ", ".join(empty)
            + ". Fill docs/security/role-permission-template.md"
        )
        sys.exit(1)


def main() -> None:
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    _ensure_roles_ready(policy)
    ui = policy.get("ui_prefix_permissions", [])

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    routes = sorted({r["prefix"] for r in ui})
    route_perms = sorted(ui, key=lambda r: len(r["prefix"]), reverse=True)

    (OUT_DIR / "admin-ui.routes.generated.ts").write_text(
        "// AUTO-GENERATED. DO NOT EDIT.\n"
        f"// source: {POLICY_PATH}\n\n"
        "export const ADMIN_UI_ROUTES = "
        + json.dumps(routes, indent=2)
        + " as const;\n",
        encoding="utf-8",
    )

    (OUT_DIR / "route-perms.generated.ts").write_text(
        "// AUTO-GENERATED. DO NOT EDIT.\n"
        f"// source: {POLICY_PATH}\n\n"
        "export const ROUTE_PERMS: Array<{ prefix: string; perm: string }> = "
        + json.dumps(route_perms, indent=2)
        + " as const;\n",
        encoding="utf-8",
    )

    middleware = """
import { NextRequest, NextResponse } from "next/server";
import { ROUTE_PERMS } from "./src/security/route-perms.generated";

function requiredPermFor(pathname: string): string | null {
  let best: { prefix: string; perm: string } | null = null;
  for (const r of ROUTE_PERMS) {
    if (pathname.startsWith(r.prefix)) {
      if (!best || r.prefix.length > best.prefix.length) best = r;
    }
  }
  return best?.perm ?? null;
}

function hasPerm(perms: string[], required: string): boolean {
  if (perms.includes("*")) return true;
  return perms.includes(required);
}

export async function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;
  if (!pathname.startsWith("/admin")) return NextResponse.next();

  const token = req.cookies.get("admin_session")?.value;
  if (!token) {
    const url = req.nextUrl.clone();
    url.pathname = "/admin/login";
    url.searchParams.set("next", pathname);
    return NextResponse.redirect(url);
  }

  const required = requiredPermFor(pathname);
  if (!required) return NextResponse.next();

  const meResp = await fetch(`${req.nextUrl.origin}/api/v1/admin/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!meResp.ok) {
    const url = req.nextUrl.clone();
    url.pathname = "/admin/login";
    url.searchParams.set("next", pathname);
    return NextResponse.redirect(url);
  }

  const me = (await meResp.json()) as { permissions: string[] };
  if (!hasPerm(me.permissions, required)) {
    const url = req.nextUrl.clone();
    url.pathname = "/admin/forbidden";
    return NextResponse.rewrite(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/admin/:path*"],
};
""".lstrip()

    MIDDLEWARE_PATH.write_text(
        "// AUTO-GENERATED. DO NOT EDIT.\n"
        f"// source: {POLICY_PATH}\n\n" + middleware,
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
