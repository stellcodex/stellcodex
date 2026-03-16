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
    <section className={cn("rounded-[var(--radius-xl)] border border-[var(--border-default)] bg-[var(--background-surface)] p-5 shadow-[var(--shadow-xs)]", className)}>
      {title || description || actions ? (
        <header className="mb-4 flex items-start justify-between gap-3">
          <div className="space-y-1">
            {title ? <h2 className="text-lg font-semibold text-[var(--foreground-strong)]">{title}</h2> : null}
            {description ? <p className="text-sm text-[var(--foreground-muted)]">{description}</p> : null}
          </div>
          {actions}
        </header>
      ) : null}
      {children}
    </section>
  );
}
