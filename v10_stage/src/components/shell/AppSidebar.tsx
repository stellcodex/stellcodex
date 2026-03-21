"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";

const primaryNavItems = [
  { href: "/dashboard", label: "Dashboard", shortLabel: "DA" },
  { href: "/projects", label: "Projects", shortLabel: "PR" },
  { href: "/viewer", label: "Viewer", shortLabel: "VI" },
  { href: "/shares", label: "Shares", shortLabel: "SH" },
  { href: "/admin", label: "Admin", shortLabel: "AD" },
  { href: "/settings", label: "Settings", shortLabel: "SE" },
];

export const sidebarActiveItemClassName = "font-semibold text-[var(--foreground-strong)]";
export const sidebarInactiveItemClassName =
  "text-[var(--foreground-default)] hover:bg-[var(--background-muted)] hover:text-[var(--foreground-strong)]";

export function getSidebarWidthClass(collapsed: boolean) {
  return collapsed ? "w-[88px]" : "w-[220px]";
}

export interface AppSidebarProps {
  collapsed?: boolean;
  onToggle?: () => void;
}

export function AppSidebar({ collapsed = false, onToggle }: AppSidebarProps) {
  const pathname = usePathname();
  const primaryItems = primaryNavItems;

  return (
    <aside
      className={cn(
        "flex h-screen flex-col border-r border-[#eee] bg-white px-4 py-4 transition-[width] duration-[var(--motion-base)] ease-[var(--ease-standard)]",
        getSidebarWidthClass(collapsed),
      )}
    >
      <div className="mb-6 flex items-start justify-between gap-3 px-1">
        <div className={cn("min-w-0", collapsed && "w-full text-center")}>
          {collapsed ? (
            <div className="text-sm font-semibold text-[var(--foreground-strong)]">SC</div>
          ) : (
            <>
              <div className="text-[18px] font-semibold text-[var(--foreground-strong)]">STELLCODEX</div>
            </>
          )}
        </div>
        <button
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-[12px] border border-[#eee] bg-white text-sm text-[var(--foreground-default)] transition-colors hover:bg-[var(--background-subtle)]"
          onClick={onToggle}
          type="button"
        >
          {collapsed ? ">" : "<"}
        </button>
      </div>

      <nav className="space-y-2">
        {primaryItems.map((item) => {
          const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              aria-current={active ? "page" : undefined}
              className={cn(
                "flex items-center rounded-[12px] px-3 py-2.5 text-sm transition-colors",
                collapsed ? "justify-center" : "justify-start",
                active ? "bg-[var(--background-muted)] text-[var(--foreground-strong)] font-semibold" : sidebarInactiveItemClassName,
              )}
              href={item.href}
              key={item.href}
              title={collapsed ? item.label : undefined}
            >
              <span>{collapsed ? item.shortLabel : item.label}</span>
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
