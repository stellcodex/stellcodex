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

function isAllowedPath(pathname: string): boolean {
  if (pathname === "/") return true;
  if (pathname.startsWith("/api/")) return true;
  if (pathname === "/share" || pathname.startsWith("/share/file/")) return true;
  if (pathname === "/view" || pathname.startsWith("/view/")) return true;
  if (pathname === "/mold") return true;
  if (pathname.startsWith("/s/")) return true;
  if (pathname === "/admin" || pathname.startsWith("/admin/job/")) return true;
  if (pathname.startsWith("/_next/")) return true;
  if (pathname.startsWith("/assets/")) return true;
  if (
    pathname === "/favicon.ico" ||
    pathname === "/favicon-32x32.png" ||
    pathname === "/favicon-16x16.png" ||
    pathname === "/apple-touch-icon.png" ||
    pathname === "/site.webmanifest" ||
    pathname === "/robots.txt" ||
    pathname === "/sitemap.xml"
  ) {
    return true;
  }
  return false;
}

function notFoundResponse() {
  return new NextResponse("Not Found", { status: 404 });
}

export async function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;
  if (!isAllowedPath(pathname)) return notFoundResponse();
  if (!pathname.startsWith("/admin")) return NextResponse.next();
  if (process.env.STELLCODEX_ENABLE_MOCK_ADMIN === "1") return NextResponse.next();

  const token = req.cookies.get("admin_session")?.value;
  if (!token) return notFoundResponse();

  const required = requiredPermFor(pathname);
  if (!required) return NextResponse.next();

  const apiBase = resolveApiBase(req);
  const meResp = await fetch(`${apiBase}/admin/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!meResp.ok) return notFoundResponse();

  const me = (await meResp.json()) as { permissions: string[] };
  if (!hasPerm(me.permissions, required)) return notFoundResponse();

  return NextResponse.next();
}

function resolveApiBase(req: NextRequest): string {
  const raw = (process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_API_BASE || "")
    .trim()
    .replace(/\/+$/, "");
  if (!raw) return `${req.nextUrl.origin}/api/v1`;
  if (raw.endsWith("/api/v1")) return raw;
  return `${raw}/api/v1`;
}

export const config = {
  matcher: ["/:path*"],
};
