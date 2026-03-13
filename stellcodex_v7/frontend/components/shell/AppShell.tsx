"use client";

import { useEffect, useState, type ReactNode } from "react";
import { AppHeader } from "@/components/shell/AppHeader";
import { AppSidebar } from "@/components/shell/AppSidebar";
import { loadSidebarCollapsed, saveSidebarCollapsed } from "@/lib/store/uiStore";
import type { BreadcrumbItem } from "@/components/shell/AppBreadcrumbs";

type AppShellProps = {
  title: string;
  subtitle?: string;
  headerActions?: ReactNode;
  children: ReactNode;
  navBasePath?: string;
  breadcrumbs?: BreadcrumbItem[];
};

export function AppShell({ title, subtitle, headerActions, children, navBasePath, breadcrumbs }: AppShellProps) {
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    setCollapsed(loadSidebarCollapsed());
  }, []);

  function toggleCollapse() {
    const next = !collapsed;
    setCollapsed(next);
    saveSidebarCollapsed(next);
  }

  return (
    <div className="sc-shell" data-collapsed={collapsed ? "true" : "false"}>
      <AppSidebar collapsed={collapsed} onToggleCollapse={toggleCollapse} basePath={navBasePath} />
      <div className="sc-main">
        <AppHeader title={title} subtitle={subtitle} actions={headerActions} breadcrumbs={breadcrumbs} />
        <main className="sc-content">{children}</main>
      </div>
    </div>
  );
}
