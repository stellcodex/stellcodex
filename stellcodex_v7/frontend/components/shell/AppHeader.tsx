import type { ReactNode } from "react";
import { AppBreadcrumbs, type BreadcrumbItem } from "@/components/shell/AppBreadcrumbs";

type AppHeaderProps = {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  breadcrumbs?: BreadcrumbItem[];
};

export function AppHeader({ title, subtitle, actions, breadcrumbs = [] }: AppHeaderProps) {
  return (
    <header className="sc-header">
      <div className="sc-stack">
        <AppBreadcrumbs items={breadcrumbs} />
        <strong>{title}</strong>
        {subtitle ? <span className="sc-muted">{subtitle}</span> : null}
      </div>
      {actions}
    </header>
  );
}
