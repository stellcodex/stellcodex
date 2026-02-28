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

function isSystemPath(pathname: string): boolean {
  if (pathname.startsWith("/api/")) return true;
  if (pathname.startsWith("/_next/")) return true;
  if (pathname.startsWith("/assets/")) return true;
  return (
    pathname === "/favicon.ico" ||
    pathname === "/favicon-32x32.png" ||
    pathname === "/favicon-16x16.png" ||
    pathname === "/apple-touch-icon.png" ||
    pathname === "/site.webmanifest" ||
    pathname === "/robots.txt" ||
    pathname === "/sitemap.xml"
  );
}

function notFoundResponse() {
  return new NextResponse("Not Found", { status: 404 });
}

function expiredShareResponse() {
  const html = `<!doctype html><html lang="en"><head><meta charset="utf-8"/><title>410 Link Expired</title><meta name="viewport" content="width=device-width,initial-scale=1"/></head><body style="margin:0;background:#0b1220;color:#e2e8f0;font-family:Segoe UI,Arial,sans-serif;display:grid;min-height:100vh;place-items:center"><div style="width:min(92vw,520px);border:1px solid #334155;border-radius:16px;background:#0f172a;padding:20px"><h1 style="margin:0 0 8px 0;font-size:20px;color:#fda4af">410 Link Expired</h1><p style="margin:0 0 12px 0;font-size:14px">Bu paylaşım bağlantısının süresi dolmuş.</p><a href=\"/\" style=\"display:inline-block;font-size:12px;padding:8px 12px;border-radius:10px;border:1px solid #334155;color:#fff;text-decoration:none;background:#111827\">Ana Sayfaya Dön</a></div></body></html>`;
  return new NextResponse(html, {
    status: 410,
    headers: {
      "content-type": "text/html; charset=utf-8",
      "cache-control": "no-store",
    },
  });
}

async function enforceShareStatus(req: NextRequest): Promise<NextResponse | null> {
  const { pathname } = req.nextUrl;
  if (!pathname.startsWith("/s/")) return null;
  const token = pathname.split("/")[2]?.trim();
  if (!token) return notFoundResponse();

  const apiBase = resolveApiBase(req);
  const res = await fetch(`${apiBase}/share/resolve?share_token=${encodeURIComponent(token)}`, {
    cache: "no-store",
  });

  if (res.status === 410) return expiredShareResponse();
  if (res.status === 401 || res.status === 404) return notFoundResponse();
  return null;
}

export async function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;
  if (isSystemPath(pathname)) return NextResponse.next();
  const shareGuard = await enforceShareStatus(req);
  if (shareGuard) return shareGuard;
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
  if (raw.startsWith("/")) return `${req.nextUrl.origin}${raw}`;
  if (raw.endsWith("/api/v1")) return raw;
  return `${raw}/api/v1`;
}

export const config = {
  matcher: ["/:path*"],
};
