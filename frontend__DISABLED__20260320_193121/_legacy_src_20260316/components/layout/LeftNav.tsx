"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { clsx } from "clsx";
import { useUser } from "@/context/UserContext";

const ITEMS = [
  { href: "/", label: "Suite Home", icon: "⬜" },
  { href: "/files", label: "My Files", icon: "◎" },
  { href: "/shares", label: "Shares", icon: "⇗" },
  { href: "/settings", label: "Settings", icon: "⚙" },
];

export function LeftNav() {
  const pathname = usePathname() || "/";
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const { user, logout, isAuthenticated, loading } = useUser();
  const [open, setOpen] = useState(false);

  const NavItem = ({ href, label, icon }: { href: string; label: string; icon: string }) => {
    const active =
      pathname === href ||
      (href === "/" && pathname === "/") ||
      (href !== "/" && pathname.startsWith(`${href}/`));

    return (
      <Link
        href={href}
        onClick={() => setOpen(false)}
        className={clsx(
          "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
          active
            ? "bg-accent/10 text-accent border border-accent/20"
            : "text-muted hover:bg-surface-2 hover:text-text"
        )}
      >
        <span className="text-lg opacity-80">{icon}</span>
        {label}
      </Link>
    );
  };

  const navContent = (
    <div className="flex h-full w-full flex-col p-4 bg-surface border-r border-white/5">
      <Link href="/" onClick={() => setOpen(false)} className="mb-6 flex flex-col px-2">
        <div className="text-xs font-bold uppercase tracking-[0.2em] text-accent">STELLCODEX</div>
        <div className="text-[10px] text-muted-2">Engineering Workflow Suite</div>
      </Link>

      <nav className="flex-1 space-y-1">
        {ITEMS.map((item) => (
          <NavItem key={item.href} {...item} />
        ))}

        {user?.role === "admin" && (
           <NavItem href="/admin" label="Admin Panel" icon="🔒" />
        )}
      </nav>

      <div className="mt-auto border-t border-white/5 pt-4">
        {loading ? (
          <div className="animate-pulse px-2 text-xs text-muted-2">Loading...</div>
        ) : isAuthenticated ? (
          <div className="flex items-center justify-between gap-2 px-2">
            <div className="flex flex-col overflow-hidden">
                <span className="truncate text-sm font-medium text-text">{user?.name}</span>
            </div>
            <button
              onClick={() => logout()}
              className="rounded p-1 text-muted-2 hover:bg-red-500/10 hover:text-red-500 transition-colors"
              title="Sign Out"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>
            </button>
          </div>
        ) : (
          <Link
            href="/login"
            onClick={() => setOpen(false)}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-accent/20 transition hover:bg-accent/90"
          >
            Sign In
          </Link>
        )}
      </div>
    </div>
  );

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="fixed left-3 top-3 z-50 flex h-10 w-10 items-center justify-center rounded-full border border-white/10 bg-surface shadow-lg text-text lg:hidden"
        aria-label="Open menu"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
           <line x1="3" y1="12" x2="21" y2="12"></line>
           <line x1="3" y1="6" x2="21" y2="6"></line>
           <line x1="3" y1="18" x2="21" y2="18"></line>
        </svg>
      </button>

      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
          onClick={() => setOpen(false)}
        />
      )}

      <aside
        className={clsx(
          "fixed inset-y-0 left-0 z-50 h-full w-64 transform transition-transform duration-300 lg:relative lg:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {navContent}
      </aside>
    </>
  );
}
