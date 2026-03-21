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
    <section className={cn("rounded-[12px] border border-[#eeeeee] bg-white p-4", className)}>
      {title || description || headerAction ? (
        <header className="mb-4 flex items-start justify-between gap-3">
          <div className="space-y-1">
            {title ? <h3 className="text-[18px] font-semibold text-[var(--foreground-strong)]">{title}</h3> : null}
            {description ? <p className="text-sm leading-5 text-[var(--foreground-muted)]">{description}</p> : null}
          </div>
          {headerAction}
        </header>
      ) : null}
      <div>{children}</div>
    </section>
  );
}
