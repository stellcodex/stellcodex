"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";

const navItems = [
  { href: "/dashboard", label: "Dashboard", shortLabel: "DA" },
  { href: "/projects", label: "Projects", shortLabel: "PR" },
  { href: "/shares", label: "Shares", shortLabel: "SH" },
  { href: "/settings", label: "Settings", shortLabel: "SE" },
];

export const sidebarActiveItemClassName = "bg-[var(--background-subtle)] text-[var(--foreground-strong)]";
export const sidebarInactiveItemClassName =
  "text-[var(--foreground-default)] hover:bg-[var(--background-subtle)] hover:text-[var(--foreground-strong)]";

export function getSidebarWidthClass(collapsed: boolean) {
  return collapsed ? "w-[92px]" : "w-[272px]";
}

export interface AppSidebarProps {
  collapsed?: boolean;
  showAdmin?: boolean;
  onToggle?: () => void;
}

export function AppSidebar({ collapsed = false, onToggle, showAdmin = false }: AppSidebarProps) {
  const pathname = usePathname();
  const items = showAdmin ? [...navItems.slice(0, 3), { href: "/admin", label: "Admin", shortLabel: "AD" }, navItems[3]] : navItems;

  return (
    <aside
      className={cn(
        "flex h-screen flex-col border-r border-[var(--border-muted)] bg-white px-4 py-5 transition-[width] duration-[var(--motion-base)] ease-[var(--ease-standard)]",
        getSidebarWidthClass(collapsed),
      )}
    >
      <div className="mb-8 flex items-start justify-between gap-3 px-2">
        <div className={cn("min-w-0", collapsed && "w-full text-center")}>
          {collapsed ? (
            <div className="text-base font-semibold tracking-[0.18em] text-[var(--foreground-strong)]">SC</div>
          ) : (
            <>
              <div className="text-xl font-semibold tracking-[0.2em] text-[var(--foreground-strong)]">STELLCODEX</div>
              <div className="mt-2 text-sm leading-6 text-[var(--foreground-muted)]">Manufacturing decision workspace</div>
            </>
          )}
        </div>
        <button
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[var(--radius-md)] border border-[var(--border-muted)] bg-white text-sm text-[var(--foreground-default)] transition-colors hover:bg-[var(--background-subtle)]"
          onClick={onToggle}
          type="button"
        >
          {collapsed ? ">" : "<"}
        </button>
      </div>
      <nav className="space-y-1.5">
        {items.map((item) => {
          const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              aria-current={active ? "page" : undefined}
              key={item.href}
              className={cn(
                "flex items-center rounded-[var(--radius-md)] px-3 py-2.5 text-sm font-medium transition-colors",
                active ? sidebarActiveItemClassName : sidebarInactiveItemClassName,
                collapsed ? "justify-center" : "justify-start",
              )}
              href={item.href}
              title={collapsed ? item.label : undefined}
            >
              {collapsed ? item.shortLabel : item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
