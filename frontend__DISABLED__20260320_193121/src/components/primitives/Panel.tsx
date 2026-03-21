import * as React from "react";

import { cn } from "@/lib/utils";

export interface PanelProps {
  title?: string;
  description?: string;
  children: React.ReactNode;
  className?: string;
  headerAction?: React.ReactNode;
}

export function Panel({ children, className, description, headerAction, title }: PanelProps) {
  return (
    <section className={cn("rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--background-surface)]", className)}>
      {title || description || headerAction ? (
        <header className="flex items-start justify-between gap-3 border-b border-[var(--border-muted)] px-4 py-3">
          <div className="space-y-1">
            {title ? <h3 className="text-sm font-semibold text-[var(--foreground-strong)]">{title}</h3> : null}
            {description ? <p className="text-xs text-[var(--foreground-muted)]">{description}</p> : null}
          </div>
          {headerAction}
        </header>
      ) : null}
      <div className="p-4">{children}</div>
    </section>
  );
}
