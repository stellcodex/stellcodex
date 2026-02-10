"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useMemo, useState } from "react";
import { Button } from "@/components/ui/Button";
import { clsx } from "clsx";

const nav = [
  { href: "/", label: "Home" },
  { href: "/community", label: "Library" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/docs", label: "Docs / Help" },
];

function isActivePath(pathname: string, href: string) {
  if (href === "/") return pathname === "/" || pathname === "/home";
  return pathname === href || pathname.startsWith(href + "/");
}

export function SiteHeader() {
  const pathname = usePathname() || "/";
  const [open, setOpen] = useState(false);

  const items = useMemo(() => {
    return nav.map((i) => ({
      ...i,
      active: isActivePath(pathname, i.href),
    }));
  }, [pathname]);

  return (
    <>
      <header className="sticky top-0 z-50 border-b border-[#d7d3c8] bg-[#f3f2ee]/80 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
          <Link href="/" className="flex items-center gap-3" onClick={() => setOpen(false)}>
            <div className="grid h-10 w-10 place-items-center rounded-xl border border-[#1d5a57] bg-[#0c3b3a] text-white">
              <div className="relative h-4 w-4">
                <div className="absolute inset-0 rounded-full border border-white/70" />
                <div className="absolute left-1/2 top-1/2 h-1.5 w-1.5 -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#5ed0a6]" />
              </div>
            </div>
            <div className="leading-tight">
              <div className="text-sm font-semibold tracking-tight">STELLCODEX</div>
              <div className="text-xs text-[#4f6f6b]">Viewer + Share</div>
            </div>
          </Link>

          <nav className="hidden items-center gap-1 text-sm md:flex">
            {items.map((i) => (
              <Link
                key={i.href}
                href={i.href}
                className={clsx(
                  "rounded-xl px-3 py-2 transition",
                  i.active
                    ? "bg-[#0c3b3a] text-white"
                    : "text-[#2c4b49] hover:bg-[#e7e3da] hover:text-[#0c2a2a]"
                )}
              >
                {i.label}
              </Link>
            ))}
          </nav>

          <div className="hidden items-center gap-2 md:flex">
            <Button href="/login" variant="ghost">
              Login
            </Button>
            <Button href="/upload">Dosya Yukle</Button>
          </div>

          <button
            className="grid h-10 w-10 place-items-center rounded-xl border border-[#d7d3c8] bg-[#f7f5ef] text-[#0c2a2a] md:hidden"
            onClick={() => setOpen((s) => !s)}
            aria-label="Menu"
            aria-expanded={open}
          >
            ☰
          </button>
        </div>

        {open ? (
          <div className="border-t border-[#d7d3c8] bg-[#f7f5ef] md:hidden">
            <div className="mx-auto max-w-6xl px-4 py-3">
              <div className="grid gap-2">
                {items.map((i) => (
                  <Link
                    key={i.href}
                    href={i.href}
                    onClick={() => setOpen(false)}
                    className={clsx(
                      "rounded-xl px-3 py-2 text-sm transition",
                      i.active ? "bg-[#0c3b3a] text-white" : "text-[#2c4b49] hover:bg-[#efece3]"
                    )}
                  >
                    {i.label}
                  </Link>
                ))}

                <div className="mt-2 grid grid-cols-2 gap-2">
                  <Button href="/login" variant="secondary">
                    Login
                  </Button>
                  <Button href="/upload">Yukle</Button>
                </div>
              </div>
            </div>
          </div>
        ) : null}
      </header>
    </>
  );
}
