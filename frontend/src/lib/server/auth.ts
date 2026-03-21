import { cookies, headers } from "next/headers";
import { redirect } from "next/navigation";

import type { RawSessionState } from "@/lib/contracts/auth";
import {
  SIGN_IN_ROUTE,
  fetchSessionState,
  normalizeOrigin,
  resolveApiBase,
  sanitizeNextPath,
} from "@/lib/auth/session";

export { DEFAULT_WORKSPACE_ROUTE, SIGN_IN_ROUTE, sanitizeNextPath } from "@/lib/auth/session";

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
  const apiBase = resolveApiBase(origin);
  return fetchSessionState(apiBase, cookieStore.toString());
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
