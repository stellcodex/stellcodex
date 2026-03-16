"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";

const navItems = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/projects", label: "Projects" },
  { href: "/shares", label: "Shares" },
  { href: "/admin", label: "Admin" },
  { href: "/settings", label: "Settings" },
];

export interface AppSidebarProps {
  collapsed?: boolean;
}

export function AppSidebar({ collapsed = false }: AppSidebarProps) {
  const pathname = usePathname();

  return (
    <aside className={cn("border-r border-[var(--border-muted)] bg-[var(--background-shell)] px-4 py-6", collapsed ? "w-20" : "w-72")}>
      <div className="mb-8 px-2">
        <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[var(--foreground-soft)]">STELLCODEX</div>
        {!collapsed ? <div className="mt-2 text-lg font-semibold text-[var(--foreground-strong)]">Manufacturing decision workspace</div> : null}
      </div>
      <nav className="space-y-1">
        {navItems.map((item) => {
          const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              className={cn(
                "flex items-center rounded-[var(--radius-md)] px-3 py-2.5 text-sm transition-colors",
                active
                  ? "bg-[var(--accent-default)] text-[var(--accent-foreground)]"
                  : "text-[var(--foreground-muted)] hover:bg-[var(--background-subtle)] hover:text-[var(--foreground-default)]",
              )}
              href={item.href}
            >
              {collapsed ? item.label.slice(0, 1) : item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
