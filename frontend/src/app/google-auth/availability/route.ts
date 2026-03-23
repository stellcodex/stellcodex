import { NextRequest, NextResponse } from "next/server";

function resolveApiBase(request: NextRequest) {
  const configured = String(process.env.NEXT_PUBLIC_API_BASE_URL || "").trim().replace(/\/+$/, "");
  if (!configured) {
    return `${request.nextUrl.origin}/api/v1`;
  }
  if (configured.startsWith("http://") || configured.startsWith("https://")) {
    return configured.endsWith("/api/v1") ? configured : `${configured}/api/v1`;
  }
  if (configured.startsWith("/")) {
    return `${request.nextUrl.origin}${configured.endsWith("/api/v1") ? configured : `${configured}/api/v1`}`;
  }
  return `${request.nextUrl.origin}/api/v1`;
}

export async function GET(request: NextRequest) {
  try {
    const response = await fetch(`${resolveApiBase(request)}/auth/google/start?next=%2Fdashboard`, {
      method: "GET",
      redirect: "manual",
      cache: "no-store",
    });

    if (response.status >= 300 && response.status < 400) {
      return NextResponse.json({ available: true, message: null });
    }

    const payload = await response.json().catch(() => null);
    const detail = payload && typeof payload === "object" && "detail" in payload ? payload.detail : null;
    return NextResponse.json({
      available: false,
      message: typeof detail === "string" && detail.trim() ? detail : "Google sign-in is unavailable.",
    });
  } catch {
    return NextResponse.json({
      available: false,
      message: "Google sign-in availability could not be verified.",
    });
  }
}
