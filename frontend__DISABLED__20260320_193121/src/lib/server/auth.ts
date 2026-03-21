import { cookies, headers } from "next/headers";
import { redirect } from "next/navigation";

import type { RawSessionState } from "@/lib/contracts/auth";

export const DEFAULT_WORKSPACE_ROUTE = "/dashboard";
export const SIGN_IN_ROUTE = "/sign-in";

function normalizeOrigin(origin: string) {
  return origin.replace(/\/+$/, "");
}

export function sanitizeNextPath(value: string | null | undefined) {
  const candidate = String(value || "").trim();
  if (!candidate) return null;

  try {
    const normalized = candidate.startsWith("http://") || candidate.startsWith("https://")
      ? new URL(candidate).pathname
      : candidate;
    if (!normalized.startsWith("/") || normalized.startsWith("//")) return null;
    if (normalized.startsWith(SIGN_IN_ROUTE)) return null;
    return normalized;
  } catch {
    return null;
  }
}

async function resolveRequestOrigin() {
  const headerStore = await headers();
  const host = headerStore.get("x-forwarded-host") ?? headerStore.get("host");
  const proto = headerStore.get("x-forwarded-proto") ?? (process.env.NODE_ENV === "development" ? "http" : "https");
  if (!host) return normalizeOrigin(process.env.INTERNAL_FRONTEND_ORIGIN || "http://127.0.0.1:3010");
  return `${proto}://${host}`;
}

export async function getServerSession(): Promise<RawSessionState> {
  const cookieStore = await cookies();
  const origin = normalizeOrigin(await resolveRequestOrigin());
  const response = await fetch(`${origin}/api/v1/auth/me`, {
    cache: "no-store",
    headers: {
      cookie: cookieStore.toString(),
    },
  });
  if (!response.ok) {
    return { authenticated: false, role: null, user: null };
  }
  return (await response.json()) as RawSessionState;
}

async function resolveProtectedNextPath() {
  const headerStore = await headers();
  const candidates = [
    headerStore.get("x-forwarded-uri"),
    headerStore.get("x-original-uri"),
    headerStore.get("x-rewrite-url"),
    headerStore.get("next-url"),
    headerStore.get("x-invoke-path"),
    headerStore.get("x-matched-path"),
  ];

  for (const candidate of candidates) {
    const resolved = sanitizeNextPath(candidate);
    if (resolved) return resolved;
  }

  return null;
}

export async function buildSignInRedirectPath(nextPath?: string | null) {
  const resolvedNextPath = sanitizeNextPath(nextPath) ?? (await resolveProtectedNextPath());
  if (!resolvedNextPath) return SIGN_IN_ROUTE;
  return `${SIGN_IN_ROUTE}?next=${encodeURIComponent(resolvedNextPath)}`;
}

export async function requireWorkspaceSession(nextPath?: string | null) {
  const session = await getServerSession();
  if (!session.authenticated || !session.user) {
    redirect(await buildSignInRedirectPath(nextPath));
  }
  return session;
}
