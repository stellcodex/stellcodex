import type { NextConfig } from "next";

function resolveApiOrigin() {
  const raw = process.env.BACKEND_API_ORIGIN;
  const normalized = String(raw || "").trim().replace(/\/+$/, "");
  if (!normalized || normalized === "/api" || normalized === "/api/v1" || normalized.startsWith("/")) {
    return null;
  }
  if (normalized.endsWith("/api/v1")) return normalized.slice(0, -"/api/v1".length);
  if (normalized.endsWith("/api")) return normalized.slice(0, -"/api".length);
  return normalized;
}

const nextConfig: NextConfig = {
  images: {
    unoptimized: true,
  },
  async rewrites() {
    const apiOrigin = resolveApiOrigin();
    if (!apiOrigin) {
      return [];
    }
    return [
      {
        source: "/api/v1/:path*",
        destination: `${apiOrigin}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;
