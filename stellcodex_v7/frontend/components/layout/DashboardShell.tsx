"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { useMemo, useState } from "react";
import { clsx } from "clsx";
import { Button } from "@/components/ui/Button";

const nav = [
  { href: "/dashboard", label: "Overview" },
  { href: "/dashboard/files", label: "Files" },
  { href: "/dashboard/shares", label: "Shares" },
  { href: "/dashboard/settings", label: "Settings" },
];

function isActivePath(pathname: string, href: string) {
  return pathname === href || pathname.startsWith(href + "/");
}

export function DashboardShell({ children }: { children: ReactNode }) {
  const pathname = usePathname() || "/dashboard";
  const [open, setOpen] = useState(false);

  const items = useMemo(() => {
    return nav.map((item) => ({
      ...item,
      active: isActivePath(pathname, item.href),
    }));
  }, [pathname]);

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="flex">
        <aside className="hidden w-64 flex-col border-r border-slate-200 bg-white p-4 lg:flex">
          <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">
            Dashboard
          </div>
          <nav className="mt-4 grid gap-1">
            {items.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={clsx(
                  "rounded-xl px-3 py-2 text-sm transition",
                  item.active
                    ? "bg-slate-900 text-white"
                    : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                )}
              >
                {item.label}
              </Link>
            ))}
          </nav>
          <div className="mt-auto grid gap-2 pt-6">
            <Button href="/" variant="ghost">
              Home
            </Button>
          </div>
        </aside>

        <div className="flex-1">
          <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/80 backdrop-blur">
            <div className="flex h-14 items-center justify-between px-4 sm:px-6">
              <div className="flex items-center gap-3">
                <button
                  className="grid h-9 w-9 place-items-center rounded-lg border border-slate-200 bg-white lg:hidden"
                  onClick={() => setOpen((s) => !s)}
                  aria-label="Open dashboard menu"
                  aria-expanded={open}
                >
                  ☰
                </button>
                <div className="text-sm font-semibold text-slate-900">User Dashboard</div>
              </div>
              <div className="flex items-center gap-2">
                <Button href="/dashboard" variant="secondary">
                  Dashboard
                </Button>
                <div className="rounded-full border border-slate-200 px-3 py-1 text-xs text-slate-500">
                  Session
                </div>
              </div>
            </div>

            {open ? (
              <div className="border-t border-slate-200 bg-white lg:hidden">
                <div className="grid gap-1 px-4 py-3">
                  {items.map((item) => (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={() => setOpen(false)}
                      className={clsx(
                        "rounded-xl px-3 py-2 text-sm transition",
                        item.active
                          ? "bg-slate-900 text-white"
                          : "text-slate-600 hover:bg-slate-100"
                      )}
                    >
                      {item.label}
                    </Link>
                  ))}
                </div>
              </div>
            ) : null}
          </header>
          <main className="px-4 py-6 sm:px-6">{children}</main>
        </div>
      </div>
    </div>
  );
}
