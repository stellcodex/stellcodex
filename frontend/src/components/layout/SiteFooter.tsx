"use client";

import Link from "next/link";

export function SiteFooter() {
  return (
    <footer className="border-t border-[#d7d3c8] bg-[#f3f2ee]">
      <div className="mx-auto max-w-6xl px-4 py-10">
        <div className="grid gap-6 md:grid-cols-[1.2fr_1fr] md:items-center">
          <div>
            <div className="text-sm font-semibold">STELLCODEX</div>
            <div className="mt-2 text-xs text-[#4f6f6b]">
              Visualize. Review. Share. Engineering data without CAD.
            </div>
          </div>

          <div className="flex flex-wrap gap-x-5 gap-y-2 text-sm md:justify-end">
            <Link className="text-[#2c4b49] hover:text-[#0c2a2a]" href="/">
              Home
            </Link>
            <Link className="text-[#2c4b49] hover:text-[#0c2a2a]" href="/community">
              Library
            </Link>
            <Link className="text-[#2c4b49] hover:text-[#0c2a2a]" href="/docs">
              Docs / Help
            </Link>
            <Link className="text-[#2c4b49] hover:text-[#0c2a2a]" href="/dashboard">
              Dashboard
            </Link>
            <Link className="text-[#2c4b49] hover:text-[#0c2a2a]" href="/login">
              Login
            </Link>
            <Link className="text-[#2c4b49] hover:text-[#0c2a2a]" href="/status">
              Status
            </Link>
            <Link className="text-[#2c4b49] hover:text-[#0c2a2a]" href="/privacy">
              Privacy
            </Link>
            <Link className="text-[#2c4b49] hover:text-[#0c2a2a]" href="/terms">
              Terms
            </Link>
          </div>
        </div>

        <div className="mt-8 flex flex-wrap items-center justify-between gap-2 text-xs text-[#4f6f6b]">
          <span>© 2026 STELLCODEX</span>
          <span>Viewer + Share • Web + PWA</span>
        </div>
      </div>
    </footer>
  );
}
