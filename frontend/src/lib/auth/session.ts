import type { RawSessionState } from "@/lib/contracts/auth";

export const DEFAULT_WORKSPACE_ROUTE = "/dashboard";
export const SIGN_IN_ROUTE = "/sign-in";
export const UNAUTHENTICATED_SESSION: RawSessionState = { authenticated: false, role: null, user: null };

function trimTrailingSlashes(value: string) {
  return value.replace(/\/+$/, "");
}

export function normalizeOrigin(origin: string) {
  return trimTrailingSlashes(origin);
}

export function resolveApiBase(origin: string) {
  const raw = process.env.NEXT_PUBLIC_API_BASE_URL || `${origin}/api/v1`;
  const normalized = trimTrailingSlashes(String(raw || "").trim());

  if (!normalized) return `${origin}/api/v1`;
  if (normalized === "/api") return `${origin}/api/v1`;
  if (normalized === "/api/v1") return `${origin}/api/v1`;

  if (normalized.startsWith("http://") || normalized.startsWith("https://")) {
    if (normalized.endsWith("/api/v1")) return normalized;
    if (normalized.endsWith("/api")) return `${normalized}/v1`;
    return `${normalized}/api/v1`;
  }

  if (normalized.startsWith("/")) {
    if (normalized.endsWith("/api/v1")) return `${origin}${normalized}`;
    if (normalized.endsWith("/api")) return `${origin}${normalized}/v1`;
    return `${origin}${normalized}/api/v1`;
  }

  return `${origin}/api/v1`;
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

export function isProtectedPath(pathname: string) {
  const protectedPrefixes = ["/dashboard", "/projects", "/files", "/shares", "/admin", "/settings"];
  return protectedPrefixes.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`));
}

export function isSignInPath(pathname: string) {
  return pathname === SIGN_IN_ROUTE || pathname.startsWith(`${SIGN_IN_ROUTE}/`);
}

export function isAuthenticatedSession(session: RawSessionState | null | undefined) {
  return Boolean(session?.authenticated && session.user);
}

export async function fetchSessionState(apiBase: string, cookieHeader: string | null | undefined): Promise<RawSessionState> {
  if (!cookieHeader?.trim()) return UNAUTHENTICATED_SESSION;

  try {
    const response = await fetch(`${apiBase}/auth/me`, {
      cache: "no-store",
      headers: {
        cookie: cookieHeader,
      },
    });

    if (!response.ok) {
      return UNAUTHENTICATED_SESSION;
    }

    return (await response.json()) as RawSessionState;
  } catch {
    return UNAUTHENTICATED_SESSION;
  }
}
