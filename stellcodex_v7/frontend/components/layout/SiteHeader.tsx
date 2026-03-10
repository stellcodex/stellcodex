"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useMemo, useState } from "react";
import { Button } from "@/components/ui/Button";
import { clsx } from "clsx";

const nav = [
  { href: "/", label: "Home" },
  { href: "/", label: "Suite" },
  { href: "/docs", label: "Docs" },
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
      <header className="sticky top-0 z-50 border-b border-[#e5e7eb] bg-white/95 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
          <Link href="/" className="flex items-center gap-3" onClick={() => setOpen(false)}>
            <Image
              src="/stellcodex-logo.png"
              alt="STELLCODEX logo"
              width={40}
              height={40}
              className="h-10 w-10 rounded-xl border border-[#d1d5db] object-cover"
            />
            <div className="hidden text-3xl font-semibold leading-none tracking-[-0.02em] text-[#111827] sm:block">
              STELLCODEX
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
                    ? "bg-[#111827] text-white"
                    : "text-[#4b5563] hover:bg-[#f3f4f6] hover:text-[#111827]"
                )}
              >
                {i.label}
              </Link>
            ))}
          </nav>

          <div className="hidden items-center gap-2 md:flex">
            <Button href="/login" variant="ghost">
              Sign In
            </Button>
            <Button href="/">Open Suite</Button>
          </div>

          <button
            className="grid h-10 w-10 place-items-center rounded-xl border border-[#d1d5db] bg-white text-[#111827] md:hidden"
            onClick={() => setOpen((s) => !s)}
            aria-label="Menu"
            aria-expanded={open}
          >
            ☰
          </button>
        </div>

        {open ? (
          <div className="border-t border-[#e5e7eb] bg-white md:hidden">
            <div className="mx-auto max-w-6xl px-4 py-3">
              <div className="grid gap-2">
                {items.map((i) => (
                  <Link
                    key={i.href}
                    href={i.href}
                    onClick={() => setOpen(false)}
                    className={clsx(
                      "rounded-xl px-3 py-2 text-sm transition",
                      i.active ? "bg-[#111827] text-white" : "text-[#4b5563] hover:bg-[#f3f4f6]"
                    )}
                  >
                    {i.label}
                  </Link>
                ))}

                <div className="mt-2 grid grid-cols-2 gap-2">
                  <Button href="/login" variant="secondary">
                    Sign In
                  </Button>
                  <Button href="/">Open Suite</Button>
                </div>
              </div>
            </div>
          </div>
        ) : null}
      </header>
    </>
  );
}
