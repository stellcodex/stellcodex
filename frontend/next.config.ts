import type { NextConfig } from "next";

const isVercel = process.env.VERCEL === "1";
const API_ORIGIN_FALLBACK = "http://127.0.0.1:8000";

function resolveApiOrigin() {
  const raw =
    process.env.BACKEND_API_ORIGIN ||
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    process.env.NEXT_PUBLIC_API_BASE ||
    API_ORIGIN_FALLBACK;
  const normalized = String(raw || "").trim().replace(/\/+$/, "");
  if (!normalized || normalized === "/api" || normalized === "/api/v1" || normalized.startsWith("/")) {
    return API_ORIGIN_FALLBACK;
  }
  if (normalized.endsWith("/api/v1")) return normalized.slice(0, -"/api/v1".length);
  if (normalized.endsWith("/api")) return normalized.slice(0, -"/api".length);
  return normalized;
}

const nextConfig: NextConfig = {
  images: {
    unoptimized: !isVercel,
  },
  async rewrites() {
    const apiOrigin = resolveApiOrigin();
    return [
      {
        source: "/api/v1/:path*",
        destination: `${apiOrigin}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;
