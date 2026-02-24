"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { clsx } from "clsx";
import { useUser } from "@/context/UserContext";

const ITEMS = [
  { href: "/", label: "Home" },
  { href: "/share", label: "StellShare" },
  { href: "/view", label: "StellView" },
  { href: "/mold", label: "MoldCodes" },
];

export function LeftNav() {
  const pathname = usePathname() || "/";
  const { user } = useUser();

  return (
    <aside className="sticky top-0 hidden h-screen w-64 shrink-0 border-r border-slate-200 bg-white lg:flex">
      <div className="flex w-full flex-col p-4">
        <Link href="/" className="rounded-2xl border border-slate-200 bg-slate-50 px-3 py-3">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
            STELLCODEX
          </div>
          <div className="mt-1 text-sm text-slate-700">Engineering Workflow Suite</div>
        </Link>

        <nav className="mt-4 grid gap-1">
          {ITEMS.map((item) => {
            const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={clsx(
                  "rounded-xl px-3 py-2 text-sm transition",
                  active
                    ? "bg-slate-900 text-white"
                    : "text-slate-700 hover:bg-slate-100 hover:text-slate-900"
                )}
              >
                {item.label}
              </Link>
            );
          })}

          {user.role === "admin" ? (
            <Link
              href="/admin"
              className={clsx(
                "rounded-xl px-3 py-2 text-sm transition",
                pathname === "/admin" || pathname.startsWith("/admin/")
                  ? "bg-slate-900 text-white"
                  : "text-slate-700 hover:bg-slate-100 hover:text-slate-900"
              )}
            >
              Admin
            </Link>
          ) : null}
        </nav>
      </div>
    </aside>
  );
}

