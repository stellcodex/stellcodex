import * as React from "react";

export interface PageHeaderProps {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
}

export function PageHeader({ actions, subtitle, title }: PageHeaderProps) {
  return (
    <div className="flex flex-col gap-4 border-b border-[#eeeeee] pb-4 md:flex-row md:items-end md:justify-between">
      <div className="space-y-1">
        <h1 className="text-[18px] font-semibold text-[var(--foreground-strong)]">{title}</h1>
        {subtitle ? <p className="text-sm leading-5 text-[var(--foreground-muted)]">{subtitle}</p> : null}
      </div>
      {actions}
    </div>
  );
}
