"use client";

import Link from "next/link";

export function SiteFooter() {
  return (
    <footer className="border-t border-[#e5e7eb] bg-white">
      <div className="mx-auto max-w-6xl px-4 py-8">
        <div className="grid gap-4 md:grid-cols-[1.2fr_1fr] md:items-center">
          <div>
            <div className="text-sm font-semibold text-[#111827]">STELLCODEX</div>
            <div className="mt-2 text-xs text-[#6b7280]">
              Görüntüle. İncele. Paylaş. CAD’siz mühendislik verisi.
            </div>
          </div>

          <div className="flex flex-wrap gap-x-5 gap-y-2 text-sm md:justify-end">
            <Link className="text-[#4b5563] hover:text-[#111827]" href="/">
              Ana Sayfa
            </Link>
            <Link className="text-[#4b5563] hover:text-[#111827]" href="/docs">
              Dokümanlar
            </Link>
            <Link className="text-[#4b5563] hover:text-[#111827]" href="/dashboard">
              Panel
            </Link>
            <Link className="text-[#4b5563] hover:text-[#111827]" href="/login">
              Giriş
            </Link>
            <Link className="text-[#4b5563] hover:text-[#111827]" href="/privacy">
              Gizlilik
            </Link>
            <Link className="text-[#4b5563] hover:text-[#111827]" href="/terms">
              Şartlar
            </Link>
          </div>
        </div>

        <div className="mt-8 flex flex-wrap items-center justify-between gap-2 text-xs text-[#6b7280]">
          <span>© 2026 STELLCODEX</span>
          <span>Görüntüle + Paylaş • Web + PWA</span>
        </div>
      </div>
    </footer>
  );
}
