import * as React from "react";

import { cn } from "@/lib/utils";

export interface CardProps {
  title?: string;
  description?: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export function Card({ actions, children, className, description, title }: CardProps) {
  return (
    <section className={cn("rounded-[12px] border border-[#eee] bg-[var(--background-surface)] p-4", className)}>
      {title || description || actions ? (
        <header className="mb-4 flex items-start justify-between gap-3">
          <div className="space-y-1">
            {title ? <h2 className="text-[18px] font-semibold text-[var(--foreground-strong)]">{title}</h2> : null}
            {description ? <p className="text-sm leading-5 text-[var(--foreground-muted)]">{description}</p> : null}
          </div>
          {actions}
        </header>
      ) : null}
      {children}
    </section>
  );
}
