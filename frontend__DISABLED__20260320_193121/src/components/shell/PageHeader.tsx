import * as React from "react";

export interface PageHeaderProps {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
}

export function PageHeader({ actions, subtitle, title }: PageHeaderProps) {
  return (
    <div className="flex flex-col gap-4 border-b border-[var(--border-muted)] pb-5 md:flex-row md:items-end md:justify-between">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-[-0.03em] text-[var(--foreground-strong)]">{title}</h1>
        {subtitle ? <p className="text-sm text-[var(--foreground-muted)]">{subtitle}</p> : null}
      </div>
      {actions}
    </div>
  );
}
