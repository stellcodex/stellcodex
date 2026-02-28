import type { NextConfig } from "next";

const isVercel = process.env.VERCEL === "1";

const nextConfig: NextConfig = {
  images: {
    unoptimized: !isVercel,
  },
};

export default nextConfig;
