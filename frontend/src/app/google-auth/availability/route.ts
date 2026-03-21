import { NextResponse } from "next/server";

function resolveBackendOrigin() {
  const value = String(process.env.BACKEND_API_ORIGIN || "").trim().replace(/\/+$/, "");
  return value || "http://127.0.0.1:18000";
}

export async function GET() {
  try {
    const response = await fetch(`${resolveBackendOrigin()}/api/v1/auth/google/start?next=%2Fdashboard`, {
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
