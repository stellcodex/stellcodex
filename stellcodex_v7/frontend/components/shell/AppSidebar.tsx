"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Button } from "@/components/primitives/Button";

type AppSidebarProps = {
  collapsed: boolean;
  onToggleCollapse: () => void;
  basePath?: string;
};

function buildItems(basePath?: string) {
  const root = basePath || "";
  return [
    { href: root || "/dashboard", label: "Dashboard" },
    { href: `${root}/projects`, label: "Projects" },
    { href: `${root}/shares`, label: "Shares" },
    { href: `${root}/admin`, label: "Admin" },
    { href: `${root}/settings`, label: "Settings" },
  ];
}

export function AppSidebar({ collapsed, onToggleCollapse, basePath }: AppSidebarProps) {
  const pathname = usePathname();
  const items = buildItems(basePath);
  return (
    <aside className="sc-sidebar">
      <div className="sc-sidebar-brand">
        <strong>{collapsed ? "SC" : "STELLCODEX"}</strong>
        {!collapsed ? <span className="sc-muted">Manufacturing workspace</span> : null}
      </div>
      <Button variant="ghost" onClick={onToggleCollapse}>
        {collapsed ? "Expand" : "Collapse"}
      </Button>
      <nav className="sc-nav">
        {items.map((item) => (
          <Link
            key={item.href}
            className="sc-nav-link"
            href={item.href}
            data-active={pathname === item.href || pathname?.startsWith(`${item.href}/`) ? "true" : "false"}
          >
            {collapsed ? item.label.slice(0, 1) : item.label}
          </Link>
        ))}
      </nav>
      <div className="sc-stack" style={{ marginTop: "auto" }}>
        {!collapsed ? <span className="sc-muted">Guest workspace</span> : null}
      </div>
    </aside>
  );
}
