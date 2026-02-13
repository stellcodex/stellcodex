"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import React from "react";

const NAV = [
  { href: "/home", label: "Ana Sayfa" },
  { href: "/files", label: "Dosyalar" },
  { href: "/dashboard", label: "Panel" },
  { href: "/viewer-3d", label: "3D Görüntüleyici" },
  { href: "/viewer-2d", label: "2D Görüntüleyici" },
];

function cx(...a: Array<string | false | null | undefined>) {
  return a.filter(Boolean).join(" ");
}

export function TopNav() {
  const pathname = usePathname();
  const [open, setOpen] = React.useState(false);

  React.useEffect(() => setOpen(false), [pathname]);

  return (
    <header className="sticky top-0 z-50 border-b border-slate-200 bg-white/80 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
        <div className="flex items-center gap-3">
          <Link href="/home" className="flex items-center gap-2 font-semibold tracking-tight">
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-xl bg-slate-900 text-white">
              S
            </span>
            <span className="hidden sm:inline">STELLCODEX</span>
            <span className="ml-2 rounded-full bg-slate-900 px-2 py-0.5 text-xs font-medium text-white">
              PRO
            </span>
          </Link>

          <div className="hidden md:flex items-center gap-1 rounded-xl border border-slate-200 bg-white px-2 py-1">
            {NAV.slice(0, 6).map((i) => {
              const active = pathname === i.href;
              return (
                <Link
                  key={i.href}
                  href={i.href}
                  className={cx(
                    "rounded-lg px-2 py-1 text-sm",
                    active ? "bg-slate-900 text-white" : "text-slate-700 hover:bg-slate-100"
                  )}
                >
                  {i.label}
                </Link>
              );
            })}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Link
            href="/files"
            className="hidden sm:inline-flex rounded-xl bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800"
          >
            Yükle
          </Link>

          <button
            className="inline-flex items-center justify-center rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 hover:bg-slate-100 md:hidden"
            onClick={() => setOpen((v) => !v)}
            aria-label="Menüyü aç"
          >
            ☰
          </button>

          <div className="text-xs text-slate-500 hidden md:block">v0.1</div>
        </div>
      </div>

      {open ? (
        <div className="border-t border-slate-200 bg-white md:hidden">
          <div className="mx-auto grid max-w-6xl grid-cols-2 gap-2 px-4 py-3">
            {NAV.map((i) => {
              const active = pathname === i.href;
              return (
                <Link
                  key={i.href}
                  href={i.href}
                  className={cx(
                    "rounded-xl border px-3 py-2 text-sm",
                    active
                      ? "border-slate-900 bg-slate-900 text-white"
                      : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
                  )}
                >
                  {i.label}
                </Link>
              );
            })}
          </div>
        </div>
      ) : null}
    </header>
  );
}
