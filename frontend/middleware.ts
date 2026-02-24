// AUTO-GENERATED. DO NOT EDIT.
// source: /var/www/stellcodex/security/rbac.policy.json

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
  if (process.env.STELLCODEX_ENABLE_MOCK_ADMIN === "1") return NextResponse.next();

  const token = req.cookies.get("admin_session")?.value;
  if (!token) {
    const url = req.nextUrl.clone();
    url.pathname = "/admin/login";
    url.searchParams.set("next", pathname);
    return NextResponse.redirect(url);
  }

  const required = requiredPermFor(pathname);
  if (!required) return NextResponse.next();

  const apiBase = resolveApiBase(req);
  const meResp = await fetch(`${apiBase}/admin/auth/me`, {
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

function resolveApiBase(req: NextRequest): string {
  const raw = (process.env.NEXT_PUBLIC_API_URL || "").trim().replace(/\/+$/, "");
  if (!raw) return `${req.nextUrl.origin}/api/v1`;
  if (raw.endsWith("/api/v1")) return raw;
  return `${raw}/api/v1`;
}

export const config = {
  matcher: ["/admin/:path*"],
};
