import { NextResponse, type NextRequest } from "next/server";

const SESSION_COOKIE_NAME = process.env.AUTH_SESSION_COOKIE_NAME ?? "stellcodex_session";

function isProtectedPath(pathname: string) {
  const protectedPrefixes = ["/dashboard", "/projects", "/files", "/shares", "/admin", "/settings"];
  return protectedPrefixes.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`));
}

export function middleware(request: NextRequest) {
  const { nextUrl } = request;

  if (!isProtectedPath(nextUrl.pathname)) {
    return NextResponse.next();
  }

  if (request.cookies.get(SESSION_COOKIE_NAME)?.value) {
    return NextResponse.next();
  }

  const signInUrl = new URL("/sign-in", request.url);
  signInUrl.searchParams.set("next", `${nextUrl.pathname}${nextUrl.search}`);
  return NextResponse.redirect(signInUrl);
}

export const config = {
  matcher: ["/dashboard/:path*", "/projects/:path*", "/files/:path*", "/shares/:path*", "/admin/:path*", "/settings/:path*"],
};
