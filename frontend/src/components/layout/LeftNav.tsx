"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { clsx } from "clsx";
import { useUser } from "@/context/UserContext";

const ITEMS = [
  { href: "/", label: "Ana Sayfa", icon: "⬜" },
  { href: "/dashboard", label: "Dashboard", icon: "▦" },
  { href: "/share", label: "StellShare", icon: "⇗" },
  { href: "/view", label: "StellView", icon: "◎" },
  { href: "/mold", label: "MoldCodes", icon: "⬡" },
];

export function LeftNav() {
  const pathname = usePathname() || "/";
  const { user, logout, isAuthenticated, loading } = useUser();
  const [open, setOpen] = useState(false);

  const navContent = (
    <div className="flex h-full w-full flex-col p-4">
      {/* Logo */}
      <Link href="/" onClick={() => setOpen(false)} className="rounded-2xl border border-slate-200 bg-slate-50 px-3 py-3">
        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">STELLCODEX</div>
        <div className="mt-1 text-sm text-slate-700">Engineering Workflow Suite</div>
      </Link>

      {/* Nav items */}
      <nav className="mt-4 grid gap-1">
        {ITEMS.map((item) => {
          const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(`${item.href}/`));
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setOpen(false)}
              className={clsx(
                "flex items-center gap-2 rounded-xl px-3 py-2 text-sm transition",
                active
                  ? "bg-slate-900 text-white"
                  : "text-slate-700 hover:bg-slate-100 hover:text-slate-900"
              )}
            >
              <span className="text-base">{item.icon}</span>
              {item.label}
            </Link>
          );
        })}

        {user.role === "admin" && (
          <Link
            href="/admin"
            onClick={() => setOpen(false)}
            className={clsx(
              "flex items-center gap-2 rounded-xl px-3 py-2 text-sm transition",
              pathname === "/admin" || pathname.startsWith("/admin/")
                ? "bg-slate-900 text-white"
                : "text-slate-700 hover:bg-slate-100 hover:text-slate-900"
            )}
          >
            <span className="text-base">⚙</span>
            Admin
          </Link>
        )}
      </nav>

      {/* Alt: kullanıcı */}
      <div className="mt-auto pt-4 border-t border-slate-200">
        {loading ? (
          <div className="text-xs text-slate-400 px-2">Yükleniyor...</div>
        ) : isAuthenticated ? (
          <div className="flex items-center justify-between gap-2 px-2">
            <div className="text-sm font-medium text-slate-700 truncate">{user.name}</div>
            <button
              onClick={logout}
              className="text-xs text-slate-500 hover:text-red-600 transition"
            >
              Çıkış
            </button>
          </div>
        ) : (
          <Link
            href="/login"
            onClick={() => setOpen(false)}
            className="block rounded-xl bg-slate-900 px-3 py-2 text-center text-sm font-semibold text-white"
          >
            Giriş Yap
          </Link>
        )}
      </div>
    </div>
  );

  return (
    <>
      {/* Mobil toggle butonu */}
      <button
        onClick={() => setOpen(true)}
        className="fixed left-3 top-3 z-40 flex h-9 w-9 items-center justify-center rounded-xl border border-slate-200 bg-white shadow-sm lg:hidden"
        aria-label="Menüyü aç"
      >
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <rect y="3" width="18" height="2" rx="1" fill="#374151" />
          <rect y="8" width="18" height="2" rx="1" fill="#374151" />
          <rect y="13" width="18" height="2" rx="1" fill="#374151" />
        </svg>
      </button>

      {/* Mobil overlay */}
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/40 lg:hidden"
          onClick={() => setOpen(false)}
        />
      )}

      {/* Mobil drawer */}
      <aside
        className={clsx(
          "fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-xl transition-transform duration-200 lg:hidden",
          open ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <button
          onClick={() => setOpen(false)}
          className="absolute right-3 top-3 flex h-8 w-8 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100"
        >
          ✕
        </button>
        {navContent}
      </aside>

      {/* Desktop sidebar */}
      <aside className="sticky top-0 hidden h-screen w-64 shrink-0 border-r border-slate-200 bg-white lg:flex">
        {navContent}
      </aside>
    </>
  );
}
