import { NextResponse, type NextRequest } from "next/server";

import {
  DEFAULT_WORKSPACE_ROUTE,
  SIGN_IN_ROUTE,
  fetchSessionState,
  isAuthenticatedSession,
  isProtectedPath,
  isSignInPath,
  normalizeOrigin,
  resolveApiBase,
  sanitizeNextPath,
} from "@/lib/auth/session";

const SESSION_COOKIE_NAME = process.env.AUTH_SESSION_COOKIE_NAME ?? "stellcodex_session";

function buildRedirectResponse(request: NextRequest, nextPath?: string | null) {
  const signInUrl = new URL(SIGN_IN_ROUTE, request.url);
  const safeNextPath = sanitizeNextPath(nextPath);

  if (safeNextPath) {
    signInUrl.searchParams.set("next", safeNextPath);
  }

  const response = NextResponse.redirect(signInUrl);
  response.cookies.delete(SESSION_COOKIE_NAME);
  return response;
}

function buildSignedOutResponse() {
  const response = NextResponse.next();
  response.cookies.delete(SESSION_COOKIE_NAME);
  return response;
}

async function resolveRequestSession(request: NextRequest) {
  const origin = normalizeOrigin(request.nextUrl.origin);
  const apiBase = resolveApiBase(origin);
  return fetchSessionState(apiBase, request.headers.get("cookie"));
}

export async function proxy(request: NextRequest) {
  const { nextUrl } = request;
  const { pathname, search } = nextUrl;
  const hasSessionCookie = Boolean(request.cookies.get(SESSION_COOKIE_NAME)?.value);

  if (!hasSessionCookie) {
    if (isProtectedPath(pathname)) {
      return buildRedirectResponse(request, `${pathname}${search}`);
    }
    return NextResponse.next();
  }

  const session = await resolveRequestSession(request);
  const authenticated = isAuthenticatedSession(session);

  if (isSignInPath(pathname)) {
    if (!authenticated) {
      return buildSignedOutResponse();
    }

    const next = nextUrl.searchParams.get("next");
    const destination = sanitizeNextPath(next) ?? DEFAULT_WORKSPACE_ROUTE;
    return NextResponse.redirect(new URL(destination, request.url));
  }

  if (isProtectedPath(pathname) && !authenticated) {
    return buildRedirectResponse(request, `${pathname}${search}`);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/sign-in", "/sign-in/:path*", "/dashboard/:path*", "/projects/:path*", "/files/:path*", "/shares/:path*", "/admin/:path*", "/settings/:path*"],
};
